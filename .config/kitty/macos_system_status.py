import ctypes
import json
import os
import threading
import time
import urllib.parse
import urllib.request
from ctypes.util import find_library


libc = ctypes.CDLL(find_library("c") or "/usr/lib/libc.dylib", use_errno=True)
cf = ctypes.CDLL(
    find_library("CoreFoundation")
    or "/System/Library/Frameworks/CoreFoundation.framework/CoreFoundation"
)
iokit = ctypes.CDLL(
    find_library("IOKit")
    or "/System/Library/Frameworks/IOKit.framework/IOKit"
)


# CPU

HOST_CPU_LOAD_INFO = 3
CPU_STATE_IDLE = 2
CPU_TICK_COUNT = 4

libc.mach_host_self.restype = ctypes.c_uint
libc.host_statistics64.argtypes = [
    ctypes.c_uint,
    ctypes.c_int,
    ctypes.c_void_p,
    ctypes.POINTER(ctypes.c_uint),
]
libc.host_statistics64.restype = ctypes.c_int

HOST = libc.mach_host_self()


def _cpu_ticks() -> list[int]:
    ticks = (ctypes.c_uint32 * CPU_TICK_COUNT)()
    count = ctypes.c_uint(CPU_TICK_COUNT)

    if libc.host_statistics64(HOST, HOST_CPU_LOAD_INFO, ticks, ctypes.byref(count)):
        raise RuntimeError("host_statistics64 failed")

    return list(ticks)


_LAST_CPU_TICKS: list[int] | None = None


def _cpu_utilization_from_ticks(before: list[int], after: list[int]) -> float:
    deltas = [(a - b) & 0xFFFFFFFF for a, b in zip(after, before)]
    total = sum(deltas)

    if total == 0:
        return 0.0

    return 100.0 * (total - deltas[CPU_STATE_IDLE]) / total


def cpu_utilization_percent(interval: float = 1.0) -> float:
    global _LAST_CPU_TICKS

    if interval <= 0:
        after = _cpu_ticks()
        before = _LAST_CPU_TICKS
        _LAST_CPU_TICKS = after

        if before is None:
            return 0.0

        return _cpu_utilization_from_ticks(before, after)

    before = _cpu_ticks()
    time.sleep(interval)
    after = _cpu_ticks()
    _LAST_CPU_TICKS = after

    return _cpu_utilization_from_ticks(before, after)


# Memory

libc.sysctlbyname.argtypes = [
    ctypes.c_char_p,
    ctypes.c_void_p,
    ctypes.POINTER(ctypes.c_size_t),
    ctypes.c_void_p,
    ctypes.c_size_t,
]
libc.sysctlbyname.restype = ctypes.c_int


def _sysctl_int(name: str) -> int:
    value = ctypes.c_int()
    size = ctypes.c_size_t(ctypes.sizeof(value))

    if libc.sysctlbyname(name.encode(), ctypes.byref(value), ctypes.byref(size), None, 0):
        errno = ctypes.get_errno()
        raise OSError(errno, os.strerror(errno), name)

    return value.value


def memory_status() -> dict:
    free = max(0, min(100, _sysctl_int("kern.memorystatus_level")))

    return {
        "memory_free_percent": free,
        "memory_pressure_percent": 100 - free,
        "memory_pressure_active": bool(_sysctl_int("vm.memory_pressure")),
    }


# Battery

CFTypeRef = ctypes.c_void_p
CFStringRef = ctypes.c_void_p
CFArrayRef = ctypes.c_void_p
CFDictionaryRef = ctypes.c_void_p
CFIndex = ctypes.c_long

kCFStringEncodingUTF8 = 0x08000100
kCFNumberIntType = 9

cf.CFRelease.argtypes = [CFTypeRef]
cf.CFStringCreateWithCString.argtypes = [
    CFTypeRef,
    ctypes.c_char_p,
    ctypes.c_uint32,
]
cf.CFStringCreateWithCString.restype = CFStringRef
cf.CFStringGetCString.argtypes = [
    CFStringRef,
    ctypes.c_char_p,
    CFIndex,
    ctypes.c_uint32,
]
cf.CFStringGetCString.restype = ctypes.c_ubyte
cf.CFDictionaryGetValue.argtypes = [CFDictionaryRef, CFTypeRef]
cf.CFDictionaryGetValue.restype = CFTypeRef
cf.CFArrayGetCount.argtypes = [CFArrayRef]
cf.CFArrayGetCount.restype = CFIndex
cf.CFArrayGetValueAtIndex.argtypes = [CFArrayRef, CFIndex]
cf.CFArrayGetValueAtIndex.restype = CFTypeRef
cf.CFNumberGetValue.argtypes = [CFTypeRef, ctypes.c_int, ctypes.c_void_p]
cf.CFNumberGetValue.restype = ctypes.c_ubyte
cf.CFBooleanGetValue.argtypes = [CFTypeRef]
cf.CFBooleanGetValue.restype = ctypes.c_ubyte

iokit.IOPSCopyPowerSourcesInfo.restype = CFTypeRef
iokit.IOPSCopyPowerSourcesList.argtypes = [CFTypeRef]
iokit.IOPSCopyPowerSourcesList.restype = CFArrayRef
iokit.IOPSGetPowerSourceDescription.argtypes = [CFTypeRef, CFTypeRef]
iokit.IOPSGetPowerSourceDescription.restype = CFDictionaryRef


def _cf_key(name: str) -> CFStringRef:
    key = cf.CFStringCreateWithCString(None, name.encode(), kCFStringEncodingUTF8)
    if not key:
        raise MemoryError(f"could not create CFString for {name!r}")

    return key


def _dict_get(dictionary: CFDictionaryRef, key: str) -> CFTypeRef:
    cf_key = _cf_key(key)
    try:
        return cf.CFDictionaryGetValue(dictionary, cf_key)
    finally:
        cf.CFRelease(cf_key)


def _cf_int(value: CFTypeRef) -> int | None:
    if not value:
        return None

    out = ctypes.c_int()
    if not cf.CFNumberGetValue(value, kCFNumberIntType, ctypes.byref(out)):
        return None

    return out.value


def _cf_bool(value: CFTypeRef) -> bool | None:
    if not value:
        return None

    return bool(cf.CFBooleanGetValue(value))


def _cf_str(value: CFTypeRef) -> str | None:
    if not value:
        return None

    buffer = ctypes.create_string_buffer(256)
    if not cf.CFStringGetCString(value, buffer, len(buffer), kCFStringEncodingUTF8):
        return None

    return buffer.value.decode()


def battery_status() -> dict | None:
    info = iokit.IOPSCopyPowerSourcesInfo()
    sources = iokit.IOPSCopyPowerSourcesList(info) if info else None

    try:
        if not sources:
            return None

        for i in range(cf.CFArrayGetCount(sources)):
            source = cf.CFArrayGetValueAtIndex(sources, i)
            desc = iokit.IOPSGetPowerSourceDescription(info, source)
            if not desc or _cf_str(_dict_get(desc, "Type")) != "InternalBattery":
                continue

            current = _cf_int(_dict_get(desc, "Current Capacity"))
            maximum = _cf_int(_dict_get(desc, "Max Capacity"))
            is_charging = _cf_bool(_dict_get(desc, "Is Charging"))

            return {
                "charge_percent": (
                    None if current is None or not maximum else current * 100.0 / maximum
                ),
                "charging_status": "charging" if is_charging else "not charging",
                "is_charging": is_charging,
                "is_charged": _cf_bool(_dict_get(desc, "Is Charged")),
                "power_source_state": _cf_str(_dict_get(desc, "Power Source State")),
            }

        return None
    finally:
        if sources:
            cf.CFRelease(sources)
        if info:
            cf.CFRelease(info)


# Stocks

STOCK_SYMBOL = "BKNG"
STOCK_CACHE_TTL = 900.0  # seconds a fetched quote is served before refetching
STOCK_RETRY_TTL = 60.0  # seconds to wait before retrying after a failed fetch
STOCK_TIMEOUT = 4.0

_STOCK_CHART_URL = (
    "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?range=3mo&interval=1d"
)
# Yahoo answers the default urllib user agent with HTTP 429.
_STOCK_USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"

_WEEK_SECONDS = 7 * 86400
_MONTH_SECONDS = 30 * 86400

_STOCK_CACHE: dict[str, dict] = {}
_STOCK_CACHE_LOCK = threading.Lock()
_STOCK_REFRESHING: set[str] = set()


def _fetch_daily_chart(symbol: str, timeout: float) -> dict:
    url = _STOCK_CHART_URL.format(symbol=urllib.parse.quote(symbol))
    request = urllib.request.Request(url, headers={"User-Agent": _STOCK_USER_AGENT})

    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.load(response)


def _daily_closes(result: dict) -> list[tuple[int, float]]:
    """Daily (timestamp, close) pairs, oldest first, with empty bars dropped."""
    timestamps = result.get("timestamp") or []
    quote = ((result.get("indicators") or {}).get("quote") or [{}])[0]
    closes = quote.get("close") or []

    return [
        (int(timestamp), float(close))
        for timestamp, close in zip(timestamps, closes)
        if timestamp is not None and close is not None
    ]


def _close_at_or_before(closes: list[tuple[int, float]], cutoff: int) -> float | None:
    """Latest close on or before cutoff, so weekends and holidays still resolve."""
    for timestamp, close in reversed(closes):
        if timestamp <= cutoff:
            return close

    return None


def _percent_change(price: float, reference: float | None) -> float | None:
    if not reference:
        return None

    return (price - reference) * 100.0 / reference


def stock_quote(symbol: str = STOCK_SYMBOL, timeout: float = STOCK_TIMEOUT) -> dict:
    """Quote with 1 week and 1 month lookbacks. Blocking; raises on failure."""
    chart = _fetch_daily_chart(symbol, timeout).get("chart") or {}
    results = chart.get("result") or []

    if not results:
        raise RuntimeError(f"no chart data for {symbol!r}: {chart.get('error')}")

    result = results[0]
    meta = result.get("meta") or {}
    closes = _daily_closes(result)

    price = meta.get("regularMarketPrice")
    if price is None and closes:
        price = closes[-1][1]
    if price is None:
        raise RuntimeError(f"no price for {symbol!r}")
    price = float(price)

    latest = closes[-1][0] if closes else int(meta.get("regularMarketTime") or 0)
    previous_close = closes[-2][1] if len(closes) > 1 else None
    week_ago_close = _close_at_or_before(closes, latest - _WEEK_SECONDS)
    month_ago_close = _close_at_or_before(closes, latest - _MONTH_SECONDS)

    return {
        "symbol": meta.get("symbol") or symbol,
        "name": meta.get("shortName") or meta.get("longName"),
        "currency": meta.get("currency"),
        "price": price,
        "previous_close": previous_close,
        "change_percent": _percent_change(price, previous_close),
        "week_ago_close": week_ago_close,
        "week_change_percent": _percent_change(price, week_ago_close),
        "month_ago_close": month_ago_close,
        "month_change_percent": _percent_change(price, month_ago_close),
        "as_of": int(meta.get("regularMarketTime") or latest),
    }


def _refresh_stock(symbol: str, timeout: float) -> dict | None:
    try:
        quote = stock_quote(symbol, timeout)
    except Exception:
        quote = None

    now = time.monotonic()
    with _STOCK_CACHE_LOCK:
        entry = _STOCK_CACHE.setdefault(symbol, {"quote": None, "fetched_at": 0.0})
        if quote is None:
            entry["failed_at"] = now
        else:
            entry.update(quote=quote, fetched_at=now, failed_at=None)
        _STOCK_REFRESHING.discard(symbol)
        last_known = entry["quote"]

    return last_known  # a failed refresh keeps serving the previous quote


def stock_status(
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
        quote = entry.get("quote")
        failed_at = entry.get("failed_at")

        fresh = quote is not None and now - entry.get("fetched_at", 0.0) < ttl
        backing_off = failed_at is not None and now - failed_at < STOCK_RETRY_TTL

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


def system_status(cpu_interval: float = 1.0, include_stock: bool = True) -> dict:
    return {
        "cpu_utilization_percent": cpu_utilization_percent(cpu_interval),
        **memory_status(),
        "battery": battery_status(),
        "stock": stock_status() if include_stock else None,
    }


if __name__ == "__main__":
    print(json.dumps(system_status(), indent=2))
