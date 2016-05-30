'''
Module for the Windows platform.

@author: Weimin Ma
@contact: U{weimin@sumologic.com<mailto:weimin@sumologic.com>}
@since: 2016-05-23
'''
from . import CollectorPlatform
from .. import architecture as arch


class WindowsPlatform(CollectorPlatform):
    """
    Represents the Windows platform.

    Currently supported architectures are L{x86<arch.X86>} and
    L{x64<arch.X86_64>}.
    """

    @property
    def _supported_architectures(self):
        return [arch.X86, arch.X86_64]

    @property
    def _architecture_mapping(self):
        return {
            arch.X86: 'i386',
            arch.X86_64: 'amd64'
        }

    @property
    def os(self):
        if self._architecture is arch.X86:
            return 'windows'
        else:
            return 'win64'

    @property
    def package_suffix(self):
        if self.architecture == arch.X86:
            return 'windows'
        else:
            return 'win64'

    @property
    def release_directory_name(self):
        return 'windows'

