from abc import ABCMeta, abstractmethod, abstractproperty

from testingframework.log import Logging

class Collector(Logging):
    '''
    Represents a collector instance.

    This class is abstract and cannot be instantiated directly.

    @ivar path: The path of this collector instance
    @type name: str
    @ivar _logger: The logger this instance uses.
    '''
    __metaclass__ = ABCMeta


    def __init__(self, installer_path, collector_home, url=None):
        '''
        Creates a new collector instance.
        '''
        self._installer_path = installer_path
        self._collector_home = collector_home
        self._url = url

        Logging.__init__(self)

    def __str__(self):
        '''
        Casts this instance to a string.

        @return: The string representation of this object.
        @rtype: str
        '''
        return self._str_format.format(**self._str_format_arguments)

    @abstractproperty
    def _str_format(self):
        '''
        The format to use when casting this instance to a string.

        @rtype: str
        '''

    @abstractproperty
    def _str_format_arguments(self):
        '''
        The arguments for the L{_str_format} to use when casting this instance
        to a string.

        @rtype: dict
        '''

    @property
    def installer_path(self):
        '''
        The installer path of this instance.

        @rtype: str
        '''
        return self._installer_path

    @property
    def deployment(self):
        '''
        The installer path of this instance.

        @rtype: str
        '''
        return self._deployment

    @property
    def collector_home(self):
        '''
        The collector home path of this instance.

        @rtype: str
        '''
        return self._collector_home

    @property
    def url(self):
        '''
        The url of a Sumo instance.

        @rtype: str
        '''
        return self._url

    def set_credentials_to_use(self, username='admin', password='changeme'):
        '''
        This method just initializes/updates self._username to username specified & self._password to password specified
        @param username: Sumo username that gets assigned to _username property of collector class
        @param password: Sumo password for the above username.
        '''
        self._username = username
        self._password = password

    def set_url(self, url):
        self._url = url

    # Abstract methods

    @abstractmethod
    def get_host_os(self):
        '''
        Returns the os of the host.
        '''
        pass
