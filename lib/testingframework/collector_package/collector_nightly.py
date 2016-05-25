'''
Module used for downloading collector builds.

@author: Weimin Ma
@contact: U{weimin@sumologic.com<mailto:weimin@sumologic.com>}
@since: 2016-05-23
'''
import urllib2

from testingframework.collector_package.collector_package import CollectorPackage
from testingframework.log import Logging

DEFAULT_BUILD = ''
DEPLOYMENT_COLLECTOR_URL_MAP = {
    'NITE': 'https://nite-events.sumologic.net/rest/download',
    'STAG': 'https://stag-events.sumologic.net/rest/download',
    'LONG': 'https://long-events.sumologic.net/rest/download',
    'PROD': 'https://collectors.sumologic.com/rest/download',
    'DUB': 'https://collectors.sumologic.com/rest/download',
    'SYD': 'https://collectors.sumologic.com/rest/download',
    'US2': 'https://collectors.sumologic.com/rest/download',
    'US4': 'https://collectors.sumologic.com/rest/download',
}

class NightlyPackage(CollectorPackage, Logging):
    '''
    This represents a collector package.
    The package can be created even though the package does not exist.

    @ivar _deployment: The deployment to download the package
    @type _deployment: str
    @ivar _build: The build number of the package. None means the latest.
    @type _build: int or str
    '''
    def __init__(self, platform=None, deployment=None, build=None):
        '''
        Creates a new packages.

        @param platform: The platform of the package. Default is the current
                         platform.
        @type platform: L{CollectorPlatform}
        @param build: The build number of the package. Value None returns
                    the latest package.
        @type build: int
        '''
        super(NightlyPackage, self).__init__(platform)
        self._deployment = deployment
        self._build = build
        Logging.__init__(self)

    @property
    def build(self):
        '''
        The build number of the package.

        This will return the default build (latest) if the build is set to None.

        @rtype: str
        '''
        return self._build or self.DEFAULT_BUILD

    @build.setter
    def build(self, build):
        '''
        Sets the build number of the package.

        Settings it to None resets it to the default build number (latest).

        @param build: The new build.
        @type build: str
        '''
        self._build = build

    def get_url(self):
        '''
        Returns the URL for the specified package.

        @return: The URL.
        @rtype: str
        @raise BuildNotFound: If the package was not found.
        '''
        return self._get_url_from_deployment(self._deployment)

    def _get_url_from_deployment(self, deployment):
        '''
        Returns the URL for the specified package using corresponding deployment url.

        @return: The URL.
        @rtype: str
        '''
        url = '/'.join((DEPLOYMENT_COLLECTOR_URL_MAP[deployment.upper()], self.platform.package_suffix))
        #return ''.join(urllib2.urlopen(url)).rstrip()
        return url


    @property
    def _exception_message(self):
        '''
        The message for the exception that will be raised if no build is found.

        It will contain the current settings.

        @rtype: str
        '''
        msg = 'Could not find a successful build with settings: {settings}'
        return msg.format(settings=self._settings)
