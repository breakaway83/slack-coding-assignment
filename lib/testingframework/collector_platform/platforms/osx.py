'''
Module for the OSX platform.

@author: Weimin Ma
@contact: U{weimin@sumologic.com<mailto:weimin@sumologic.com>}
@since: 2016-05-23
'''
from . import CollectorPlatform
from .. import architecture as arch


class OSXPlatform(CollectorPlatform):
    """
    Represents the OSX platform.

    Currently supported architectures are L{universal<arch.UNIVERSAL>},
    L{PowerPC<arch.POWERPC>}, L{x86<arch.X86>} and L{x86-64<arch.X86_64>}.
    """

    @property
    def _supported_architectures(self):
        return [arch.X86_64]

    @property
    def os(self):
        return 'macos'


    @property
    def architecture(self):
        return ''

    @property
    def release_directory_name(self):
        return 'macos'
