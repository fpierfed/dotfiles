# Custom kitty tab bar: normal tabs on the left (powerline style),
# a right-aligned status showing battery %, date and 24h time.
#
# Enabled via `tab_bar_style custom` in kitty.conf. kitty imports this file
# and calls draw_tab() for each tab. We piggyback on the last tab to draw the
# right-hand status, and use a timer to keep the clock live.

import os
import sys

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

CONFIG_DIR = os.path.dirname(os.path.abspath(__file__))
if CONFIG_DIR not in sys.path:
    sys.path.insert(0, CONFIG_DIR)
import status

REFRESH_INTERVAL = 1.0  # seconds between clock redraws
_timer_id = None


def _redraw_tab_bar(_id) -> None:
    tm = get_boss().active_tab_manager
    if tm is not None:
        tm.mark_tab_bar_dirty()


def _draw_right_status(draw_data: DrawData, screen: Screen) -> None:
    text = status.status_text()
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
