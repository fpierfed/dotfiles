import ctypes
import time
from ctypes.util import find_library
from functools import lru_cache

libc = ctypes.CDLL(find_library('c') or '/usr/lib/libc.dylib', use_errno=True)
cf = ctypes.CDLL(
    find_library('CoreFoundation')
    or '/System/Library/Frameworks/CoreFoundation.framework/CoreFoundation'
)
iokit = ctypes.CDLL(
    find_library('IOKit') or '/System/Library/Frameworks/IOKit.framework/IOKit'
)


# CPU

HOST_CPU_LOAD_INFO = 3
CPU_STATE_IDLE = 2
CPU_TICK_COUNT = 4
CPU_REFRESH_INTERVAL = 5.0  # seconds between system-status samples
_cpu_cache = None
_cpu_cache_time = 0.0


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

    if libc.host_statistics64(
        HOST, HOST_CPU_LOAD_INFO, ticks, ctypes.byref(count)
    ):
        raise RuntimeError('host_statistics64 failed')

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


def ttl_hack_value(ttl: int) -> int:
    """
    This is part of a hack related to how the `lru_cache` decorator works.

    When you decorate a function with `lru_cache` you are essentially using an
    `OrderedDict` as a cache. The key being a hash of the function calling
    param values. What we are doing here, we are adding a parameter to the
    functions we want to cache that changes at `ttl` second boundaries, thus
    creating a new cache entry.
    """
    ttl = int(min(1, ttl))
    return int(time.monotonic() // ttl)


@lru_cache(maxsize=10)
def _cpu_percent(ttl_hack: int) -> dict | None:
    return cpu_utilization_percent(interval=0)


def status():
    return {
        'cpu_utilization_percent': _cpu_percent(
            ttl_hack=ttl_hack_value(CPU_REFRESH_INTERVAL)
        )
    }
