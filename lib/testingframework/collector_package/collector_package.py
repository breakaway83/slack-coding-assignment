'''
Module used for downloading Sumo collector.

@var SUMO_COLLECTOR: Constant denoting a regular Sumo collector package.
@type SUMO_COLLECTOR: str
@var PACKAGE_TYPES: A list of all the avaiable types of packages.
@type PACKAGE_TYPES: list(str)

@author: Weimin Ma
@contact: U{weimin@sumologic.com<mailto:weimin@sumologic.com>}
@since: 2016-05-22
'''
from abc import ABCMeta, abstractmethod
import os
import urllib
import urllib2
import types
import pytest

from testingframework import collector_platform
from testingframework.collector_platform.collector_platform import CollectorPlatform
from testingframework.log import Logging

COLLECTOR = 'SumoCollector'


class CollectorPackage(Logging):
    '''
    Represents a generic collector package.

    @cvar _ROOT_URL: The root URL to the releases page.
    @type _ROOT_URL: str
    @cvar _RELEASE_PACKAGE_FORMAT: The format of a release package name. Will
                                   contain args type, version, build and suffix.
    @type _RELEASE_PACKAGE_FORMAT: str

    @ivar _platform: The platform of the package.
    @type _platform: L{CollectorPlatform}
    @ivar _package_type: The type of package.
    @type _package_type: str
    '''
    _PACKAGE_TYPE_NAMES = {
        COLLECTOR: 'SumoCollector',
    }

    _ROOT_URL = 'https://collectors.sumologic.com/rest/download'
    _RELEASE_PACKAGE_FORMAT = '{type}-{version}-{build}-{suffix}'

    __meta__ = ABCMeta

    def __init__(self, platform):
        '''
        Creates a new package.

        @param platform: The platform of the package. Default to the current
                         platform.
        @type platform: L{CollectorPlatform}
        @raise InvalidCollectorPlatform: If the platform is not of the right type.
        @raise InvalidPackageType: If the type is not valid.
        '''
        self._platform = None
        self._installer_name = None
        self._set_platform(platform)

        Logging.__init__(self)

    @property
    def platform(self):
        '''
        The platform of the package.

        @rtype: L{CollectorPlatform}
        '''
        return self._platform

    @property
    def installer_name(self):
        '''
        Gets the filename of the installer downloaded from Sumo
        @rtype: str
        '''
        self._installer_name

    @installer_name.setter
    def installer_name(self, installer_name):
        '''
        Sets the collector's installer name
        '''
        self._installer_name = installer_name

    @platform.setter
    def platform(self, platform):
        '''
        Sets the platform of the package.

        Setting it to None resets it to the current platform.

        @param platform: The new platform.
        @type platform: L{CollectorPlatform}
        @raise InvalidCollectorPlatform: If the platform is not of the right type.
        '''
        self._set_platform(platform)

    def _set_platform(self, platform):
        '''
        Sets the platform of the package.

        Setting it to None resets it to the current platform.
        @param platform: The platform of the package. Default to the current
                         platform.
        @param platform: The new platform.
        @type platform: L{CollectorPlatform}
        @raise InvalidCollectorPlatform: If the platform is not of the right type.
        '''
        platform = platform or collector_platform.get_platform()
        if not isinstance(platform, CollectorPlatform):
            raise InvalidCollectorPlatform(platform)
        self._platform = platform


    def _get_package_name(self, version, build):
        '''
        Returns the package name for the specified arguments.

        @param version: The version of the package.
        @type version: str
        @param build: The build number of the package.
        @type build: str or int
        @return: The package name.
        @rtype: str
        '''
        args = {
            'suffix': self.platform.package_suffix,
            'version': version,
            'build': build,
        }
        return self._package_name_format.format(**args)

    @property
    def _package_name_format(self):
        '''
        The format of name of the package that this object represents.

        Will have arguments type, suffix, version and build.

        @rtype: str
        '''
        if self.debug_build:
            return self._DEBUG_PACKAGE_FORMAT
        else:
            return self._RELEASE_PACKAGE_FORMAT

    @property
    def _settings(self):
        '''
        The settings for this package.

        Subclasses should override this if they have their own settings.

        @rtype: dict
        '''
        return {
            'platform': self.platform,
            'package_type': self.package_type,
            'debug_build': self.debug_build
        }

    def download(self):
        '''
        Downloads the package to the default tempdir.

        For more info see on exceptions L{get_url}.

        @see: L{get_url}
        @return: The path to the downloaded package.
        @rtype: str
        '''
        return self.download_to(None)

    def download_to(self, target=None):
        '''
        Downloads the package to the specified file.

        For more info on exceptions see L{get_url}.

        @see: L{get_url}
        @param target: The file to download to.
        @type target: str
        @return: The path to the downloaded package.
        @rtype: str
        '''
        url = self.get_url()
        request = HeadRequest(url)
        response = urllib2.urlopen(request)
        response_headers = response.info()
        filename = response_headers.dict['content-disposition']
        filename = filename.split(';')[1].split('=')[1]
        self.installer_name = filename
        self.logger.info('Fetching package from %s' % url)
        if target is None:
            return urllib.urlretrieve(url, filename)[0]
        else:
            return urllib.urlretrieve(url, os.path.join(target, filename))[0]

    @abstractmethod
    def get_url(self):
        '''
        Returns the URL for this package.

        @return: The URL.
        @rtype: str
        @raise BuildNotFound: If the build doesn't exist.
        '''
        pass

class HeadRequest(urllib2.Request):
    def get_method(self):
        return "HEAD"


class BuildNotFound(RuntimeError):
    '''
    Raised when a build is not found.
    '''
    pass


class InvalidPackageType(RuntimeError):
    '''
    Raised when trying to set the package type to an invalid type.

    @ivar package_type: The type that is invalid.
    '''

    def __init__(self, package_type):
        '''
        Creates a new exception.

        @param package_type: The type that is invalid.
        '''
        self.package_type = package_type
        super(InvalidPackageType, self).__init__(self._error_message)

    @property
    def _error_message(self):
        '''
        The error message for this exception.

        @rtype: str
        '''
        msg = '{type} is not a valid package type. Valid types are {types}'
        return msg.format(type=self.package_type, types=PACKAGE_TYPES)


class InvalidCollectorPlatform(RuntimeError):
    '''
    Raised when trying to set the platform to an invalid value.

    @ivar platform: The platform that is invalid.
    '''

    def __init__(self, platform):
        '''
        Creates a new exception.

        @param platform: The platform that is invalid.
        '''
        self.platform = platform
        super(InvalidCollectorPlatform, self).__init__(self._error_message)

    @property
    def _error_message(self):
        '''
        The error message for this exception.

        @rtype: str
        '''
        return '{0} is not a valid platform'.format(self.platform)
