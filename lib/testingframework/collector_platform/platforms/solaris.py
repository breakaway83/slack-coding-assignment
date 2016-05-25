'''
Module for the Solaris/SunOS platform.

@author: Weimin Ma
@contact: U{weimin@sumologic.com<mailto:weimin@sumologic.com>}
@since: 2016-05-23
'''
from . import CollectorPlatform
from .. import architecture as arch


class SolarisPlatform(CollectorPlatform):
    """
    Represents the Solaris/SunOS platform.

    Supported architectures are L{sparc<arch.SPARC>}, L{x86<arch.X86>} and
    L{x86-64<arch.X86_64>}.
    """

    @property
    def _supported_architectures(self):
        return [arch.SPARC, arch.X86, arch.X86_64]

    @property
    def os(self):
        return 'SunOS'

    @property
    def _architecture_mapping(self):
        return {
            arch.SPARC: 'sparc',
            arch.X86: 'i386',
            arch.X86_64: 'x86_64'
        }

    @property
    def package_suffix(self):
        return '{os}-{arch}.tar.Z'.format(os=self.os, arch=self.architecture)

    @property
    def release_directory_name(self):
        return 'solaris'
