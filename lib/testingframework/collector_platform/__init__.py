'''
Module for getting a collector platform.

@var _PLATFORM_MAPPINGS: A dictionary that is used to decide which platform
                         should be used. The key should be a the OS string and
                         the key should be the platform class.
@type _PLATFORM_MAPPINGS: dict(str, class)
@var SUPPORTED_PLATFORMS: A list of supported platforms.
@type SUPPORTED_PLATFORMS: list(str)

@author: Weimin Ma
@contact: U{weimin@sumologic.com<mailto:weimin@sumologic.com>}
@since: 2016-05-23
'''
import re
from abc import ABCMeta, abstractproperty
import sys
from platform import machine

from . import os as _osm
from . import architecture as _archm
from . import platforms as _plat

# These 3 imports are here to make the OS and architecture constants available
# from this module.
from .os import OSX, WINDOWS, SOLARIS, LINUX, UnsupportedOS, OS_NAMES
from .architecture import X86_64, X86, UNIVERSAL, UnknownArchitecture, ARCHITECTURE_NAMES
from .collector_platform import UnsupportedArchitecture

_PLATFORM_MAPPINGS = {
    OSX: _plat.osx.OSXPlatform,
    WINDOWS: _plat.windows.WindowsPlatform,
    SOLARIS: _plat.solaris.SolarisPlatform,
    LINUX: _plat.linux.LinuxPlatform,
}

SUPPORTED_PLATFORMS = _PLATFORM_MAPPINGS.values()


def get_platform(platform_info=None):
    """
    Returns the platform for the given OS and architecture.

    @param platform_info: A tuple containing (os, architecture). The default
                          value is the current OS and architecture.
    @type platform_info: tuple(str, str)
    @raise UnsupportedOS: If the OS is not supported
    @raise UnsupportedArchitecture: If the architecture is not supported by
                                    that OS.
    @return: The platform for that OS and architecture.
    @rtype: L{CollectorPlatform}
    """
    platform_info = _sanitize_platform_info(platform_info)
    plat = _get_os_platform(platform_info)
    return plat(*platform_info)


def _sanitize_platform_info(platform_info):
    '''
    Sanitizes the platform info.

    This will use default values if needed.

    @param platform_info: A tuple with (os, architecture) or None.
    @type platform_info: tuple
    @return: The sanitized platform info.
    @rtype: tuple
    '''
    platform_info = platform_info or (None, None)
    os = _osm.sanitize_os(platform_info[0])
    architecture = _archm.sanitize_architecture(platform_info[1])
    return (os, architecture)


def _get_os_platform(platform_info):
    """
    Returns the class for the specified platform info.

    @param platform_info: The sanitized platform info.
    @type platform_info: tuple
    @return: The platform's class.
    @rtype: class
    @raise UnsupportedOS: If the platform was not found.
    """
    os = platform_info[0]
    if not os in _PLATFORM_MAPPINGS:
        raise UnsupportedOS(os)
    return _PLATFORM_MAPPINGS[os]
