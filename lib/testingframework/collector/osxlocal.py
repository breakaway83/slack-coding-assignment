'''
Module for dealing with local Mac collector instances

@author: Weimin Ma
@contact: U{weimin@sumologic.com<mailto:weimin@sumologic.com>}
@since: 2016-05-31
'''

import subprocess
import os
import tempfile
import shlex
import urllib2
import platform
import socket
import time
import fileinput
import pytest

import testingframework.util.archiver as archiver

from testingframework.collector_platform.collector_platform import CollectorPlatform
from .base import Collector
from .local import LocalCollector
from .local import CouldNotStopCollector
from .local import CouldNotStartCollector
from testingframework.util import fileutils
from testingframework.collector_package.collector_nightly import NightlyPackage
from testingframework.collector_package.collector_release import ReleasedPackage
from testingframework.exceptions.command_execution import CommandExecutionFailure


class OSXLocalCollector(LocalCollector):
    '''
    Represents a Mac version of local collector instance.

    Local means there is access to the collector binaries, conf files etc.

    @ivar _installer_path: The path to the collector installations root.
    @cvar COMMON_FLAGS: The most flags that are most commonly used. They are
                        recommended when installing the collector
    @type COMMON_FLAGS: str
    '''
    _instance_count=0
    COMMON_FLAGS = '-q'

    def __init__(self, installer_path, name=None):
        '''
        Creates a new  OSXLocalCollector instance.

        @param installer_path: The local that collector is/will be installed.
        @type installer_path: str
        @raise InvalidCollectorHome: If installer_path is not a string.
        '''
        super(OSXLocalCollector, self).__init__(installer_path)
        OSXLocalCollector._instance_count +=1
        self._instance_id = OSXLocalCollector._instance_count
        self._pkg_installer_name = None
        self._cmd_binary = None

    def uninstall(self):
        '''
        Uninstalls collector by running uninstall command

        This assumes that the collector is installed at the following location:
            /Applications/Sumo\ Logic\ Collector/
        '''
        self.logger.info('Uninstalling Collector...')
        try:
            # Standalone Installer
            collector_home = os.path.join('/', 'Applications', 'Sumo Logic Collector', 'Sumo Logic Collector Uninstaller.app')
            os.chdir(collector_home)
            uninstall_bin = os.path.join('./Contents', 'MacOS', 'JavaApplicationStub')
            cmd_binary = '{0} {1}'.format(uninstall_bin, self.COMMON_FLAGS)
            proc = subprocess.Popen(shlex.split(cmd_binary, posix=False), stderr=subprocess.PIPE, stdout=subprocess.PIPE)
            stddata = proc.communicate()
        finally:
            pass

        self.logger.info('Collector has been uninstalled.')

    def install_from_archive(self, uninstall_existing=False):
        '''
        Installs this collector instance from an archive.

        The archive must be extractable by the L{archiver}

        @param archive_path: The path to the archive
        @type archive_path: str
        @param upgrade: Boolean flag that indicates if the archive install \
                        should/shouldn't override the existing collector_home
        @type upgrade: bool
        '''
        msg = 'Installing Collector from archive={0}'.format(self.installer_path)
        self.logger.info(msg)
        pkg = NightlyPackage(deployment=self._deployment)
        archive = pkg.download_to(self.installer_path)
        self._pkg_installer_name = pkg._installer_name 

        if(uninstall_existing==True):
            self.uninstall()

        try:
            # Standalone Installer
            # Mount the disk image
            cmd_binary = 'hdiutil attach -mountpoint %s %s' % (self.installer_path, os.path.join(self.installer_path, self._pkg_installer_name))
            proc = subprocess.Popen(shlex.split(cmd_binary), stderr=subprocess.PIPE, stdout=subprocess.PIPE)
            stddata = proc.communicate()
            # CD to "Sumo Logic Collector Installer.app/Contents/MacOS"
            contents_path = os.path.join(self.installer_path, 'Sumo Logic Collector Installer.app', 'Contents', 'MacOS')
            os.chdir(contents_path)

            if(self.xstr(self._username) != '' and self.xstr(self._password) != ''):
                cmd_binary = './JavaApplicationStub -Vsumo.email=%s -Vsumo.password=%s -Vcollector.url=%s -Vollector.name=%s'
                cmd_binary = '{0} {1}'.format(cmd_binary, self.COMMON_FLAGS)
                if self._name is None:
                    cmd_binary = cmd_binary % (self._username, self._password, self._url, \
                                 "%s%s" % (socket.gethostname(), self._instance_count))
                else:
                    cmd_binary = cmd_binary % (installer_bin , self._username, self._password, self._url, \
                                 os.path.join(self.installer_path, 'SumoCollector'), self._name)
            else:
                cmd_binary = './JavaApplicationStub -Vsumo.accessid=%s -Vsumo.accesskey=%s -Vcollector.url=%s -Vollector.name=%s'
                cmd_binary = '{0} {1}'.format(cmd_binary, self.COMMON_FLAGS)
                if self._name is None:
                    cmd_binary = cmd_binary % (self._accessid, self._accesskey, self._url, \
                                 "%s%s" % (socket.gethostname(), self._instance_count))
                else:
                    cmd_binary = cmd_binary % (installer_bin , self._accessid, self._accesskey, self._url, \
                                 os.path.join(self.installer_path, 'SumoCollector'), self._name)
            self._cmd_binary = cmd_binary
            proc = subprocess.Popen(shlex.split(cmd_binary, posix=False), stderr=subprocess.PIPE, stdout=subprocess.PIPE)
            stddata = proc.communicate()

        except Exception, e:
            cmd_binary = 'hdiutil detach -force %s' % self.installer_path
            proc = subprocess.Popen(shlex.split(cmd_binary), stderr=subprocess.PIPE, stdout=subprocess.PIPE)
            stddata = proc.communicate()
        finally:
            cmd_binary = 'hdiutil detach -force %s' % self.installer_path
            proc = subprocess.Popen(shlex.split(cmd_binary), stderr=subprocess.PIPE, stdout=subprocess.PIPE)
            stddata = proc.communicate()

        self.logger.info('Collector has been installed.')

    def xstr(self, s):
        return s if s else ''
