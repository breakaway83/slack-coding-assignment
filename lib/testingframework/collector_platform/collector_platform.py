'''
This module contains the Platform class

@author: Weimin Ma
@contact: U{weimin@sumologic.com<mailto:weimin@sumologic.com>}
@since: 2016-05-22
'''

from abc import ABCMeta, abstractproperty


class CollectorPlatform(object):
    """
    Represents a platform that Sumo collector can run on.

    When creating a subclass you can choose to either implement
    L{_supported_architectures} or L{architecture}

    @cvar _DEFAULT_SUFFIX: The package_suffix that is used per default.
    @type _DEFAULT_SUFFIX: str

    @ivar _os: The OS string that was passed to the constructor or sys.platform.
    @type _os: str
    @ivar _architecture: The sanitized architecture that was passed to the
                         constructor or platform.machine()
    @type _architecture: str
    @ivar _supported_architectures: A regexp matching all valid architectures
                                    for that platform.
    @type _supported_architecture: str
    """
    __meta__ = ABCMeta

    _DEFAULT_SUFFIX = '{os}/{arch}'

    def __init__(self, os, architecture):
        """
        Creates a new platform.

        Cannot be invoked directly.

        @param os: The OS string.
        @type os: str
        @param architecture: The architecture string. Must be sanitized.
        @type architecture: str
        """
        self._os = os
        self._architecture = architecture

        self._verify_architecture_supported()

    def _verify_architecture_supported(self):
        """
        Checks if the architecture is supported for this platform throwing an
        exception if it isn't.

        @raise UnsupportedArchitecture: If the architecture isn't supported.
        """
        if not self._architecture_is_supported():
            raise UnsupportedArchitecture(self._os, self._architecture)

    @abstractproperty
    def _supported_architectures(self):
        """
        Should return a list of supported architectures for this platform.

        @rtype: list(str)
        """
        pass

    def _architecture_is_supported(self):
        """
        Checks if the architecture is supported.

        @return: True if the architecture is supported.
        @rtype: bool
        """
        return self._architecture in self._supported_architectures

    @property
    def package_suffix(self):
        """
        The package suffix for this platform.

        It's usually {OS}-{architecture}.tgz

        @rtype: str
        """
        return self._DEFAULT_SUFFIX.format(os=self.os, arch=self.architecture)

    @abstractproperty
    def os(self):
        """
        The OS for this platform.

        @rtype: str
        """
        pass

    @property
    def _architecture_mapping(self):
        """
        A dictionary of architectures and their replacements.

        @rtype: dict(str, str)
        """
        raise RuntimeError('A CollectorPlatform subclass must either'
                           'implement _architecture_mapping or '
                           'architecture!')

    @property
    def architecture(self):
        """
        The architecture for this platform.

        @rtype: str
        """
        return self._architecture_mapping[self._architecture]

    @property
    def release_directory_name(self):
        '''
        The directory name that released builds are kept in.

        Usually this is just the lower case OS name but not always.

        @rtype: str
        '''
        return self.os.lower()

    def __repr__(self):
        '''
        Returns a human readable representation of this object.

        @return: The human readable representation of this object.
        @rtype: str
        '''
        msg = "{cls} with OS '{os}' and architecture '{arch}'"
        return msg.format(cls=type(self).__name__, os=self._os,
                          arch=self._architecture)

    def __str__(self):
        '''
        Returns a string representation of this object.

        @return: The string representation of this object.
        @rtype: str
        '''
        msg = "<{cls} object at {addr} os='{os}' architecture='{arch}'>"
        return msg.format(cls=type(self).__name__, addr=hex(id(self)),
                          os=self._os, arch=self._architecture)


class UnsupportedArchitecture(BaseException):
    '''
    Raised when the specified architecture is not supported with the specified
    OS.

    @param os: The OS that has been specified.
    @type os: str
    @param architecture: The architecture that is not supported.
    @type architecture: str
    '''
    def __init__(self, os, architecture):
        self.os = os
        self.architecture = architecture
        super(UnsupportedArchitecture, self).__init__(self._error_message)

    @property
    def _error_message(self):
        '''
        The error message for this exception.

        @rtype: str
        '''
        msg = "The architecture '{arch}' is not supported for OS '{os}'"
        return msg.format(os=self.os, arch=self.architecture)
