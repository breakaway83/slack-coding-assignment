'''
This class acts as a factory for LocalCollector and returns corresponding to the underlying OS & architecture.

@author: Weimin Ma
@contact: U{weimin@sumologic.com<mailto:weimin@sumologic.com>}
@since: 2016-06-09
'''
import os
import platform

from testingframework.log import Logging
from testingframework.collector.base import Collector
from testingframework.collector.local import LocalCollector
from testingframework.collector.windowslocal import WindowsLocalCollector

class CollectorFactory: 
     
    @classmethod
    def getCollector(self, install_home, url=None):
        '''
        This method returns Collector Instance corresponding to underlying architecture
        '''
        if(platform.system().upper()=='WINDOWS'):
            return WindowsLocalCollector(install_home, url)
        else: #posix
            return LocalCollector(install__home, url)

    @classmethod
    def getCollectorClassName(self):
        if(platform.system().upper()=='WINDOWS'):
            return WindowsLocalCollector
        else: #posix
            return LocalCollector
