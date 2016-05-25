'''
Module for dealing with OS strings.

@var OSX: Constant denoting OS X
@type OSX: str
@var WINDOWS: Constant denoting Windows
@type WINDOWS: str
@var SOLARIS: Constant denoting Solaris
@type SOLARIS: str
@var LINUX: Constant denoting Linux
@type LINUX: str
@var OS_NAMES: A list of all supported OS's
@type OS_NAMES: list(str)
@var _OS_ALIASES: A dictionary of (regexp: OS) that can be used to sanitize an
                   OS
@type _OS_ALIASES: dict(str, str)

@author: Weimin Ma
@contact: U{weimin@sumologic.com<mailto:weimin@sumologic.com>}
@since: 2016-05-23
'''
import re
import sys

OSX = 'OS X'
WINDOWS = 'Windows'
SOLARIS = 'Solaris'
LINUX = 'Linux'

OS_NAMES = [
    OSX,
    WINDOWS,
    SOLARIS,
    LINUX,
]

_OS_ALIASES = {
    '^(mac|darwin|osx)$': OSX,
    '^(win(32|64)|cygwin)$': WINDOWS,
    'cygwin':WINDOWS,
    '^sunos*': SOLARIS,
    '^(linux.*)$': LINUX,
}


def get_current_os():
    '''
    Returns the _unsanitized_ os of this computer.

    @return: The os
    @rtype: str
    '''
    return sys.platform


def sanitize_os(os):
    """
    Sanitize the given OS string.

    @param os: The OS string to sanitize
    @type os: str
    @return: The sanitized string
    @rtype: str
    @raise UnsupportedOS: When the OS was not recognized.
    """
    os = os or get_current_os()
    sanitized_os = _find_os_by_exact_match(os)
    if sanitized_os is not None:
        return sanitized_os
    return _find_os_by_regexp(os)


def _find_os_by_exact_match(os):
    """
    Goes through the values of L{OS_NAMES} and tries to find an exact
    match (case insensitive).

    @param os: The os to sanitize.
    @type os: str
    @return: The sanitized os or None if it couldn't be found.
    @rtype: str
    """
    for sanitized_os in OS_NAMES:
        if sanitized_os.lower() == os.lower():
            return sanitized_os
    return None


def _find_os_by_regexp(os):
    """
    Goes through the keys of L{_OS_ALIASES} and tries to find an exact
    match using regexp (case insensitive).

    @param os: The os to sanitize.
    @type os: str
    @return: The sanitized os.
    @rtype: str
    @raise UnsupportedOS: If the os is unknown.
    """
    for (regexp, sanitized_os) in _OS_ALIASES.iteritems():
        if re.search(regexp, os, re.IGNORECASE):
            return sanitized_os
    raise UnsupportedOS(os)


class UnsupportedOS(BaseException):
    """
    Exception that is raised when the specified (or current) OS is not supported
    """

    def __init__(self, os):
        '''
        Creates a new exception.

        @param os: The OS that is not supported
        @type os: str
        '''
        self.os = os
        super(UnsupportedOS, self).__init__(self._error_message)

    @property
    def _error_message(self):
        '''
        The error message for this exception

        @rtype: str
        '''
        msg = "The OS '{os}' is not supported"
        return msg.format(os=self.os)
