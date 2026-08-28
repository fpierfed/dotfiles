import json
import threading
import time
import urllib.parse
import urllib.request

STOCK_SYMBOL = 'BKNG'
STOCK_CACHE_TTL = 900.0  # seconds a fetched quote is served before refetching
STOCK_RETRY_TTL = 60.0  # seconds to wait before retrying after a failed fetch
STOCK_TIMEOUT = 4.0

_STOCK_CHART_URL = 'https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?range=3mo&interval=1d'
# Yahoo answers the default urllib user agent with HTTP 429.
_STOCK_USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'

_WEEK_SECONDS = 7 * 86400
_MONTH_SECONDS = 30 * 86400

_STOCK_CACHE: dict[str, dict] = {}
_STOCK_CACHE_LOCK = threading.Lock()
_STOCK_REFRESHING: set[str] = set()


def _fetch_daily_chart(symbol: str, timeout: float) -> dict:
    url = _STOCK_CHART_URL.format(symbol=urllib.parse.quote(symbol))
    request = urllib.request.Request(
        url, headers={'User-Agent': _STOCK_USER_AGENT}
    )

    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.load(response)


def _daily_closes(result: dict) -> list[tuple[int, float]]:
    """Daily (timestamp, close) pairs, oldest first, with empty bars dropped."""
    timestamps = result.get('timestamp') or []
    quote = ((result.get('indicators') or {}).get('quote') or [{}])[0]
    closes = quote.get('close') or []

    return [
        (int(timestamp), float(close))
        for timestamp, close in zip(timestamps, closes)
        if timestamp is not None and close is not None
    ]


def _close_at_or_before(
    closes: list[tuple[int, float]], cutoff: int
) -> float | None:
    """Latest close on or before cutoff, so weekends and holidays still resolve."""
    for timestamp, close in reversed(closes):
        if timestamp <= cutoff:
            return close

    return None


def _percent_change(price: float, reference: float | None) -> float | None:
    if not reference:
        return None

    return (price - reference) * 100.0 / reference


def stock_quote(
    symbol: str = STOCK_SYMBOL,
    timeout: float = STOCK_TIMEOUT,
    hack_ttl: int = 0,
) -> dict:
    """Quote with 1 week and 1 month lookbacks. Blocking; raises on failure."""
    chart = _fetch_daily_chart(symbol, timeout).get('chart') or {}
    results = chart.get('result') or []

    if not results:
        raise RuntimeError(
            f'no chart data for {symbol!r}: {chart.get("error")}'
        )

    result = results[0]
    meta = result.get('meta') or {}
    closes = _daily_closes(result)

    price = meta.get('regularMarketPrice')
    if price is None and closes:
        price = closes[-1][1]
    if price is None:
        raise RuntimeError(f'no price for {symbol!r}')
    price = float(price)

    latest = (
        closes[-1][0] if closes else int(meta.get('regularMarketTime') or 0)
    )
    previous_close = closes[-2][1] if len(closes) > 1 else None
    week_ago_close = _close_at_or_before(closes, latest - _WEEK_SECONDS)
    month_ago_close = _close_at_or_before(closes, latest - _MONTH_SECONDS)

    return {
        'symbol': meta.get('symbol') or symbol,
        'name': meta.get('shortName') or meta.get('longName'),
        'currency': meta.get('currency'),
        'price': price,
        'previous_close': previous_close,
        'change_percent': _percent_change(price, previous_close),
        'week_ago_close': week_ago_close,
        'week_change_percent': _percent_change(price, week_ago_close),
        'month_ago_close': month_ago_close,
        'month_change_percent': _percent_change(price, month_ago_close),
        'as_of': int(meta.get('regularMarketTime') or latest),
    }


def _refresh_stock(symbol: str, timeout: float) -> dict | None:
    try:
        quote = stock_quote(symbol, timeout)
    except Exception:
        quote = None

    now = time.monotonic()
    with _STOCK_CACHE_LOCK:
        entry = _STOCK_CACHE.setdefault(
            symbol, {'quote': None, 'fetched_at': 0.0}
        )
        if quote is None:
            entry['failed_at'] = now
        else:
            entry.update(quote=quote, fetched_at=now, failed_at=None)
        _STOCK_REFRESHING.discard(symbol)
        last_known = entry['quote']

    return last_known  # a failed refresh keeps serving the previous quote


def cached_stock_quote(
    symbol: str = STOCK_SYMBOL,
    ttl: float = STOCK_CACHE_TTL,
    timeout: float = STOCK_TIMEOUT,
    blocking: bool = True,
) -> dict | None:
    """Cached quote, or None until one has been fetched. Never raises.

    With blocking=False a stale quote is refreshed on a background thread and the
    last known one is returned immediately, so callers on a UI thread (kitty's tab
    bar redraws every second) never wait on the network.
    """
    now = time.monotonic()

    with _STOCK_CACHE_LOCK:
        entry = _STOCK_CACHE.get(symbol) or {}
        quote = entry.get('quote')
        failed_at = entry.get('failed_at')

        fresh = quote is not None and now - entry.get('fetched_at', 0.0) < ttl
        backing_off = (
            failed_at is not None and now - failed_at < STOCK_RETRY_TTL
        )

        if fresh or backing_off:
            return quote

        if not blocking:
            if symbol not in _STOCK_REFRESHING:
                _STOCK_REFRESHING.add(symbol)
                threading.Thread(
                    target=_refresh_stock, args=(symbol, timeout), daemon=True
                ).start()

            return quote

    return _refresh_stock(symbol, timeout)


def status(symbol=STOCK_SYMBOL):
    return {symbol: _stock_text()}


def _stock_text() -> str | None:
    """BKNG price with its 1 week and 1 month moves, or None until it arrives.

    blocking=False keeps the network off this code path: the quote is fetched on a
    background thread and picked up by a later redraw.
    """
    try:
        quote = cached_stock_quote(blocking=False)
    except Exception:
        return None

    price = (quote or {}).get('price')
    if price is None:
        return None

    moves = []
    for label, key in (
        ('1w', 'week_change_percent'),
        ('1m', 'month_change_percent'),
    ):
        percent = quote.get(key)
        if percent is not None:
            moves.append(f'{label} {percent:+.1f}%')

    text = f'{quote.get("symbol") or "BKNG"} {price:,.2f}'
    if moves:
        text += ' (' + ' · '.join(moves) + ')'

    return text
