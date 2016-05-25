'''
This module contains all the supported platforms.

@author: Weimin Ma
@contact: U{weimin@sumologic.com<mailto:weimin@sumologic.com>}
@since: 2016-05-23
'''

__all__ = ['linux', 'osx', 'solaris', 'windows']

from ..collector_platform import CollectorPlatform
from .linux import LinuxPlatform
from .osx import OSXPlatform
from .solaris import SolarisPlatform
from .windows import WindowsPlatform
