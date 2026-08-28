import ctypes
from ctypes.util import find_library

libc = ctypes.CDLL(find_library('c') or '/usr/lib/libc.dylib', use_errno=True)
cf = ctypes.CDLL(
    find_library('CoreFoundation')
    or '/System/Library/Frameworks/CoreFoundation.framework/CoreFoundation'
)
iokit = ctypes.CDLL(
    find_library('IOKit') or '/System/Library/Frameworks/IOKit.framework/IOKit'
)


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
    key = cf.CFStringCreateWithCString(
        None, name.encode(), kCFStringEncodingUTF8
    )
    if not key:
        raise MemoryError(f'could not create CFString for {name!r}')

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
    if not cf.CFStringGetCString(
        value, buffer, len(buffer), kCFStringEncodingUTF8
    ):
        return None

    return buffer.value.decode()


def status() -> dict | None:
    info = iokit.IOPSCopyPowerSourcesInfo()
    sources = iokit.IOPSCopyPowerSourcesList(info) if info else None

    try:
        if not sources:
            return None

        for i in range(cf.CFArrayGetCount(sources)):
            source = cf.CFArrayGetValueAtIndex(sources, i)
            desc = iokit.IOPSGetPowerSourceDescription(info, source)
            if (
                not desc
                or _cf_str(_dict_get(desc, 'Type')) != 'InternalBattery'
            ):
                continue

            current = _cf_int(_dict_get(desc, 'Current Capacity'))
            maximum = _cf_int(_dict_get(desc, 'Max Capacity'))
            is_charging = _cf_bool(_dict_get(desc, 'Is Charging'))

            return {
                'charge_percent': (
                    None
                    if current is None or not maximum
                    else current * 100.0 / maximum
                ),
                'charging_status': 'charging'
                if is_charging
                else 'not charging',
                'is_charging': is_charging,
                'is_charged': _cf_bool(_dict_get(desc, 'Is Charged')),
                'power_source_state': _cf_str(
                    _dict_get(desc, 'Power Source State')
                ),
            }

        return None
    finally:
        if sources:
            cf.CFRelease(sources)
        if info:
            cf.CFRelease(info)
