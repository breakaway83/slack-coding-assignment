'''
This class acts as a factory for LocalCollector and returns corresponding to the underlying OS & architecture.

@author: Weimin Ma
@contact: U{weimin@sumologic.com<mailto:weimin@sumologic.com>}
@since: 2016-06-09
'''
import os
import platform
import pytest

from testingframework.log import Logging
from testingframework.collector.base import Collector
from testingframework.collector.local import LocalCollector
from testingframework.collector.windowslocal import WindowsLocalCollector
from testingframework.collector.osxlocal import OSXLocalCollector

class CollectorFactory: 
     
    @classmethod
    def getCollector(self, install_home):
        '''
        This method returns Collector Instance corresponding to underlying architecture
        '''
        if(platform.system().upper()=='WINDOWS'):
            return WindowsLocalCollector(install_home)
        elif(platform.system().upper()=="DARWIN"):
            return OSXLocalCollector(install_home)
        else: #posix
            return LocalCollector(install_home)

    @classmethod
    def getCollectorClassName(self):
        if(platform.system().upper()=='WINDOWS'):
            return WindowsLocalCollector
        elif(platform.system().upper()=="DARWIN"):
            return OSXLocalCollector
        else: #posix
            return LocalCollector
