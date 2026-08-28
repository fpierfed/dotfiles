import ctypes
import os
from ctypes.util import find_library

libc = ctypes.CDLL(find_library('c') or '/usr/lib/libc.dylib', use_errno=True)
cf = ctypes.CDLL(
    find_library('CoreFoundation')
    or '/System/Library/Frameworks/CoreFoundation.framework/CoreFoundation'
)
iokit = ctypes.CDLL(
    find_library('IOKit') or '/System/Library/Frameworks/IOKit.framework/IOKit'
)


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

    if libc.sysctlbyname(
        name.encode(), ctypes.byref(value), ctypes.byref(size), None, 0
    ):
        errno = ctypes.get_errno()
        raise OSError(errno, os.strerror(errno), name)

    return value.value


def status() -> dict:
    free = max(0, min(100, _sysctl_int('kern.memorystatus_level')))

    return {
        'memory_free_percent': free,
        'memory_pressure_percent': 100 - free,
        'memory_pressure_active': bool(_sysctl_int('vm.memory_pressure')),
    }
