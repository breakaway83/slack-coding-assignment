'''
Module used for comparing collector version numbers.

@author: Weimin Ma
@contact: U{weimin@sumologic.com<mailto:weimin@sumologic.com>}
@since: 2016-05-23
'''
import re


class CollectorVersion(object):
    '''
    Represents a collector version number.

    A version number looks like this: XX.XXX-X or XX.XXX-XX

    Examples are: 19.144-2, 19.144-10

    Internally the version will be stored as both a string and as an integer.
    The version is immutable.

    @cvar _VERSION_REGEXP: A regexp to match a valid version number.
    @type _VERSION_REGEXP: regexp

    @ivar _string_version: The version as the original string.
    @type _string_version: str
    '''
    _VERSION_REGEXP = re.compile('(\d+)\.(\d+)-(\d+)?')

    def __init__(self, version=None):
        '''
        Creates a new version.

        @param version: The version.
        @type version: str
        @raise InvalidVersion: If the version could not be parsed.
        '''
        if not self._version_is_valid(version):
            raise InvalidVersion(version)

        self._string_version = version

    def _version_is_valid(self, version):
        '''
        Checks if the version matches the version regexp.

        Returns True if version=None

        @param version: True if it matches (it's valid).
        @type version: bool
        '''
        if version is None:
            return True
        return self._VERSION_REGEXP.match(version) is not None

    def __str__(self):
        '''
        Returns this version as a string.

        @return: The string representation.
        @rtype: str
        '''
        return self.version

    def __repr__(self):
        '''
        Synonym to __str__

        @return: The string representation.
        @rtype: str
        '''
        return self.version

    @property
    def version(self):
        '''
        The version as a string.

        @rtype: str
        '''
        return self._string_version

    @property
    def _version_numbers(self):
        '''
        The version components of this version.

        @rtype: tuple(int, int, int, int)
        '''
        m = self._VERSION_REGEXP.match(self._string_version)
        major, minor, _, hotfix, _, patch = m.groups()
        return (int(major), int(minor), int(hotfix or '0'), int(patch or '0'))

    def __cmp__(self, other_version):
        '''
        Compares this version to another version.

        @param other_version: The other version.
        @type other_version: str
        '''
        mapping = {
            str: self._cmp_with_string,
        }
        if type(other_version) not in mapping:
            err = 'Cannot compare version with {0}'.format(other_version)
            raise RuntimeError(err)

        return mapping[type(other_version)](other_version)

    def _cmp_with_string(self, other):
        '''
        Compares this version with a string.

        Just creates a new CollectorVersion and compares self to that.

        @param other: The other version
        @type other: str
        '''
        return cmp(self, CollectorVersion(other))

class InvalidVersion(RuntimeError):
    '''
    Raised when a version is invalid.
    '''

    def __init__(self, version):
        '''
        Creates the exception.

        @param version: The version that is invalid.
        @type version: str
        '''
        msg = '"{0}" is not a valid version'.format(version)
        RuntimeError.__init__(self, msg)
