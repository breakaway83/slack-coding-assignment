'''
Module for the Linux platform.

@author: Weimin Ma
@contact: U{weimin@sumologic.com<mailto:weimin@sumologic.com>}
@since: 2016-05-23
'''
from . import CollectorPlatform
from .. import architecture as arch


class LinuxPlatform(CollectorPlatform):
    """
    Represents the Linux platform.

    Currently supported architectures are L{x86-64<arch.X86_64>} and
    L{x86<arch.X86>}.
    """

    @property
    def _supported_architectures(self):
        return [arch.X86, arch.X86_64]

    @property
    def os(self):
        return 'linux'

    @property
    def _architecture_mapping(self):
        return {
            arch.X86: '32',
            arch.X86_64: '64'
        }
