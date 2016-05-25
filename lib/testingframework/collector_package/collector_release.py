'''
Module used for downloading released collector builds.

@author: Weimin Ma
@contact: U{weimin@sumologic.com<mailto:weimin@sumologic.com>}
@since: 2016-05-22
'''
import re
import urllib

from .collector_package import CollectorPackage, COLLECTOR
from .collector_version import CollectorVersion
from testingframework.collector_package.collector_package import BuildNotFound


class ReleasedPackage(CollectorPackage):
    '''
    @cvar _DIRECTORY_NAME_FOR_TYPE: A mapping of <package_type>:<directory_name>
    @type _DIRECTORY_NAME_FOR_TYPE: dict(str, str)
    @cvar _PACKAGES_DIRECTORY: The URL to the root directory where all the
                               versions are located.
    @type _PACKAGES_DIRECTORY: str
    @cvar _FIND_VERSION_REGEXP: A regexp that is used to find all the versions
                               in the _PACKAGED_DIRECTORY.
    @type _FIND_VERSION_REGEXP: str
    @cvar _RELEASE_PACKAGE_DIRECTORY: The URL to the directory where a release
                                      build is kept.
    @type _RELEASE_PACKAGE_DIRECTORY: str

    @ivar version: The version of the package.
    @type version: str
    @ivar _latest_version: The cached value for the latest version for the
                           current platform. Might be invalid if the platform
                           is changed.
    @type _latest_version: str
    '''
    _DIRECTORY_NAME_FOR_TYPE = {
        COLLECTOR: 'SumoCollector',
    }

    _ROOT_URL = {
        'NITE': 'https://nite-events.sumologic.net/rest/download/',
        'STAG': 'https://stag-events.sumologic.net/rest/download/',
        'LONG': 'https://long-events.sumologic.net/rest/download/',
        'PROD': '',
        'US2': '',
        'US4': '',
        'SYD': '',
        'DUB': '',
    }

    _RELEASE_PACKAGE_DIRECTORY = '{platform}/{type}/{version}'

    def __init__(self, platform=None, version=None, deployment=None):
        '''
        Creates a new package.

        @param platform: The platform of the package.
        @type platform: L{CollectorPlatform}
        @param version: The version of the package (19.144-6, etc). Default is
                        the latest version.
        @type version: str
        '''
        super(ReleasedPackage, self).__init__(platform, deployment)
        self.version = version
        self._latest_version = None

    def _set_platform(self, platform):
        CollectorPackage._set_platform(self, platform)
        self._latest_version = None

    def get_url(self):
        '''
        Returns the URL for this package.

        @return: The URL.
        @rtype: str
        @raise ReleaseNotFound: When the package could not be located.
        '''
        return self._build_url()

    def _build_url(self):
        '''
        Builds the URL for the package.
        '''
        url = self._get_package_directory()
        version = self._get_version()
        build = self._get_build_number()
        package = self._get_package_name(build=build, version=version)
        return '{0}/{1}'.format(url, package)

    def _get_package_directory(self, version=None):
        '''
        Returns the URL to the directory where this package is in.

        @param version: The version of the package. Default is L{_get_version}
        @type version: str
        @return: The URL
        @rtype: str
        '''
        return self._package_directory_format.format(
            root=self._PACKAGES_DIRECTORY,
            type=self._DIRECTORY_NAME_FOR_TYPE[self.package_type],
            version=version or self._get_version(),
            platform=self.platform.release_directory_name,
        )

    @property
    def _package_directory_format(self):
        '''
        The format for the directory URL that this package is in.

        @rtype: str
        '''
        if self.debug_build:
            return self._DEBUG_PACKAGE_DIRECTORY
        else:
            return self._RELEASE_PACKAGE_DIRECTORY

    def _get_version(self):
        '''
        Returns the version of this package.

        If self.version is None then the latest version is fetched.

        @return: The version.
        @rtype: str
        '''
        if self.version is not None:
            return self.version
        return self._get_latest_version_for_platform()

    def _get_latest_version_for_platform(self):
        '''
        Returns the latest version for the current platform.

        This value is cached.

        @return: The latest version.
        @rtype: str
        '''
        if self._latest_version is None:
            self._latest_version = self._find_latest_version_for_platform()
        return self._latest_version

    def _find_latest_version_for_platform(self):
        '''
        Queries the server to find the latest version for this platform.

        Since all versions doesn't contain all platforms the versions are tried
        in descending order until a version that contains the current platform
        is found.

        @return: The latest version.
        @rtype: str
        '''
        versions = self._get_sorted_released_versions()
        for version in versions:
            if self._version_contains_platform(version):
                return str(version)
        raise RuntimeError('WTF! No releases found :(')

    def _get_sorted_released_versions(self):
        '''
        Returns a list of all known versions.

        This does not include special version, only versions that consists of
        2-4 components (4.2.3 for example but not XXXXX).

        They will be sorted in descending order.

        @return: All released versions of the collector.
        @rtype: list(L{CollectorVersion})
        '''
        contents = self._get_packages_directory_contents()
        versions = self._FIND_VERSION_REGEXP.findall(contents)
        versions = [CollectorVersion(version) for version in versions]
        versions.sort(reverse=True)
        return versions

    def _get_packages_directory_contents(self):
        '''
        Returns the contents of the directory where releases are kept.

        @return: The contents
        @rtype: str
        '''
        data = urllib.urlopen(self._PACKAGES_DIRECTORY)
        return ''.join(data.readlines())

    def _version_contains_platform(self, version):
        '''
        Check if the specified version exists for the current platform.

        @param version: The version to check.
        @type version: str or CollectorVersion
        @return: True if it exists
        @rtype: bool
        '''
        url = self._get_package_directory(version)
        response = urllib.urlopen(url)
        return response.getcode() == 200

    def _get_build_number(self):
        '''
        Returns the build number for the current settings.

        @return: The build number
        @rtype: str
        '''
        contents = self._get_package_directory_contents()
        regexp = self._get_build_number_regexp()
        match = regexp.search(contents)

        if not match:
            raise RuntimeError('Could not find the build number')

        return match.group(1)

    def _get_package_directory_contents(self):
        '''
        Returns the contents of the directory where the package is kept.

        @return: The contents
        @rtype: str
        '''
        url = self._get_package_directory()
        response = urllib.urlopen(url)

        code = response.getcode()
        if code != 200:
            raise ReleaseNotFound(self._exception_message(url, code))

        return ''.join(response.readlines())

    def _exception_message(self, url, code):
        '''
        Returns the message for the exception that will be raised if the release
        isn't found.

        @param url: The URL that failed.
        @type url: str
        @param code: The code that the server returned.
        @type code: int
        @return: The message
        @rtype: str
        '''
        msg = (
            'When requesting URL {url} the server responded with HTTP '
            'code {code}. The setings was {settings}')
        return msg.format(url=url, code=code, settings=self._settings)

    @property
    def _settings(self):
        s = CollectorPackage._settings.fget(self)  # @UndefinedVariable
        s['version'] = self.version
        return s

    def _get_build_number_regexp(self):
        '''
        Returns a regexp that matches picks out the build number from a package
        name.

        The build number will be captured in the first group.

        @return: The compiled regexp.
        '''
        version = self._get_version()
        build = '(\d+)'
        r = self._get_package_name(version=version, build=build)
        return re.compile(r)


class ReleaseNotFound(BuildNotFound):
    '''
    Raised when the release package wasn't found.
    '''
    pass
