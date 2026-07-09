# Custom kitty tab bar: normal tabs on the left (powerline style),
# a right-aligned status showing battery %, date and 24h time.
#
# Enabled via `tab_bar_style custom` in kitty.conf. kitty imports this file
# and calls draw_tab() for each tab. We piggyback on the last tab to draw the
# right-hand status, and use a 1s timer to keep the clock live.

import datetime
import os
import subprocess

from kitty.boss import get_boss
from kitty.fast_data_types import add_timer, wcswidth
from kitty.tab_bar import (
    DrawData,
    ExtraData,
    Screen,
    TabBarData,
    as_rgb,
    draw_tab_with_powerline,
)
from kitty.utils import color_as_int

REFRESH_INTERVAL = 1.0  # seconds between clock redraws
BATTERY_REFRESH_TICKS = 30  # redraws between (slow) pmset calls

_timer_id = None
_battery_cache = ''
_battery_skipped = 1


def _read_battery() -> str:
    """Return e.g. '87%' or '⚡87%' when charging. '' if unavailable."""

    global _battery_cache, _battery_skipped

    # Not that we read the battery every N refreshes to avoid the sys call.
    if _battery_skipped < BATTERY_REFRESH_TICKS:
        _battery_skipped += 1
        return _battery_cache
    else:
        _battery_skipped = 1

    try:
        out = subprocess.check_output(
            ['pmset', '-g', 'batt'], text=True, timeout=1.0
        )
    except Exception:
        return _battery_cache

    pct = ''
    charging = False
    for line in out.splitlines():
        if '%' not in line:
            continue
        for token in line.replace(';', ' ').split():
            if token.endswith('%'):
                pct = token
        charging = 'discharging' not in line and (
            'charging' in line or 'charged' in line
        )
        break
    if not pct:
        return _battery_cache

    _battery_cache = ('⚡' + pct) if charging else pct
    return _battery_cache


def _status_text() -> str:
    now = datetime.datetime.now()
    parts = []
    try:
        parts.append('load %.2f' % os.getloadavg()[0])
    except OSError:
        pass
    bat = _read_battery()
    if bat:
        parts.append(bat)
    parts.append(now.strftime('%d %b %Y'))
    parts.append(now.strftime('%H:%M'))
    return ' | '.join(parts) + ' '


def _redraw_tab_bar(_id) -> None:
    tm = get_boss().active_tab_manager
    if tm is not None:
        tm.mark_tab_bar_dirty()


def _draw_right_status(draw_data: DrawData, screen: Screen) -> None:
    text = _status_text()
    width = wcswidth(text)
    start = screen.columns - width
    if start <= screen.cursor.x:  # not enough room; skip
        return
    screen.cursor.x = start
    screen.cursor.fg = as_rgb(color_as_int(draw_data.inactive_fg))
    screen.cursor.bg = as_rgb(color_as_int(draw_data.default_bg))
    screen.draw(text)


def draw_tab(
    draw_data: DrawData,
    screen: Screen,
    tab: TabBarData,
    before: int,
    max_title_length: int,
    index: int,
    is_last: bool,
    extra_data: ExtraData,
) -> int:
    global _timer_id
    if _timer_id is None:
        _timer_id = add_timer(_redraw_tab_bar, REFRESH_INTERVAL, True)
    draw_tab_with_powerline(
        draw_data,
        screen,
        tab,
        before,
        max_title_length,
        index,
        is_last,
        extra_data,
    )
    if is_last:
        _draw_right_status(draw_data, screen)
    return screen.cursor.x
