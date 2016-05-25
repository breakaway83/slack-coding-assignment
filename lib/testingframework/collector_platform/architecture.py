'''
Module for detecting a collector platform.

@var X86_64: Constant denoting the x86-64 architecture (this includes
             amd64).
@type X86_64: str
@var X86: Constant denoting the x86 architecture (this includes i386 and
           i686).
@type X86: str
@var UNIVERSAL: Constant denoting the universal architecture (OS X only).
@type UNIVERSAL: str
@var ARCHITECTURE_NAMES: A list of all supported architectures.
@type ARCHITECTURE_NAMES: list(str)
@var _ARCHITECTURE_ALIASES: A dictionary that is used to sanitize the
                            architecture string. The key should be a
                            regexp matching the architecture string and
                            the key should be the architecture.
@type _ARCHITECTURE_ALIASES: dict(str, str)

@author: Weimin Ma
@contact: U{weimin@sumologic.com<mailto:weimin@sumologic.com>}
@since: 2016-05-23
'''
import re
import platform

# Note: If you add a new architecture make sure to import it in __init__

X86_64 = 'x86-64'
X86 = 'x86'
UNIVERSAL = 'Universal'

ARCHITECTURE_NAMES = [
    X86_64,
    X86,
    UNIVERSAL
]

_ARCHITECTURE_ALIASES = {
    '^((x86_|amd|wow|x)64|i86pc)$': X86_64,
    '^((i3|i6)86|athlon)$': X86,
}


def get_current_architecture():
    '''
    Returns the _unsanitized_ architecture of this computer.

    @return: The architecture
    @rtype: str
    '''
    return platform.machine()


def sanitize_architecture(architecture):
    """
    Replaces the given architecture with a common name for that type.

    An example would be amd64 which is replaced by L{X86_64}.

    @param architecture: The architecture to sanitize.
    @type architecture: str
    @return: The sanitized architecture.
    @rtype: str
    """
    architecture = architecture or get_current_architecture()
    arch = _find_architecture_by_exact_match(architecture)
    if arch is not None:
        return arch
    return _find_architecture_by_regexp(architecture)


def _find_architecture_by_exact_match(architecture):
    """
    Goes through the values of L{ARCHITECTURE_NAMES} and tries to find
    an exact match (case insensitive).

    @param architecture: The architecture to sanitize.
    @type architecture: str
    @return: The sanitized architecture or None if it couldn't be found.
    @rtype: str
    """
    for arch in ARCHITECTURE_NAMES:
        if arch.lower() == architecture.lower():
            return arch
    return None


def _find_architecture_by_regexp(architecture):
    """
    Goes through the keys of L{_ARCHITECTURE_ALIASES} and tries to find
    an exact match using regexp (case insensitive).

    @param architecture: The architecture to sanitize.
    @type architecture: str
    @return: The sanitized architecture.
    @rtype: str
    @raise UnknownArchitecture: If the architecture is unknown.
    """
    for (regexp, arch) in _ARCHITECTURE_ALIASES.iteritems():
        if re.search(regexp, architecture, re.IGNORECASE):
            return arch
    raise UnknownArchitecture(architecture)


class UnknownArchitecture(BaseException):
    """
    Exception that is raised when the specified (or current) architecture
    is not recognized.
    """

    def __init__(self, architecture):
        '''
        Creates a new exception.

        @param architecture: The architecture that is unknown.
        @type architecture: str
        '''
        self.architecture = architecture
        super(UnknownArchitecture, self).__init__(self._error_message)

    @property
    def _error_message(self):
        '''
        The error message for this exception.

        @rtype: str
        '''
        msg = "The architecture '{arch}' is not recognized."
        return msg.format(arch=self.architecture)
