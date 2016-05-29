'''
Module for dealing with local Windows collector instances

@author: Weimin Ma
@contact: U{weimin@sumologic.com<mailto:weimin@sumologic.com>}
@since: 2016-05-29
'''

import subprocess
import os
import tempfile
import shlex
import urllib2
import platform
import socket

import testingframework.util.archiver as archiver

from testingframework.collector_platform.collector_platform import CollectorPlatform
from .base import Collector
from .local import LocalCollector
from testingframework.util import fileutils
from testingframework.collector_package.collector_nightly import NightlyPackage
from testingframework.collector_package.collector_release import ReleasedPackage
from testingframework.exceptions.command_execution import CommandExecutionFailure


class WindowsLocalCollector(LocalCollector):
    '''
    Represents a windows version of local collector instance.

    Local means there is access to the collector binaries, conf files etc.

    @ivar _installer_path: The path to the collector installations root.
    @cvar COMMON_FLAGS: The most flags that are most commonly used. They are
                        recommended when installing the collector
    @type COMMON_FLAGS: str
    '''
    _instance_count=0
    COMMON_FLAGS = '-q -console'

    def __init__(self, installer_path, name=None):
        '''
        Creates a new  WindowsLocalCollector instance.

        @param installer_path: The local that collector is/will be installed.
        @type installer_path: str
        @raise InvalidCollectorHome: If installer_path is not a string.
        '''
        super(WindowsLocalCollector, self).__init__(installer_path)
        WindowsLocalCollector._instance_count +=1
        self._instance_id = WindowsLocalCollector._instance_count
        self._pkg_installer_name = None
        self._cmd_binary = None

    @property
    def collector_binary(self):
        '''
        Returns the absolute path to the splunk binary

        @rtype: str
        '''
        binary='collector'
        binary=binary+'.bat'
        return self.get_binary_path(binary)


    def execute_with_binary(self, binary, command):
        '''
        Executes the specified command with the given binary.

        @param binary: The binary to execute with. Can be relative to the bin
                       directory or an absolute path.
        @type binary: str
        @param command: The command to execute. Remember to quote your strings
                        if the contain spaces.
        @type command: str
        @return: (exit_code, stdout, stderr)
        @rtype: tuple(int, str, str)
        @raise BinaryMissing: If the binary doesn't exist
        '''
        binary = self.get_binary_path(binary)
        #self._validate_binary(binary)

        cmd = [binary]
        cmd.extend(shlex.split(command, posix=False))
        self.logger.info('Executing command {0}'.format(' '.join(cmd)))

        process = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        (stdout, stderr) = process.communicate()
        self.logger.info('Done! Exit code {0}'.format(process.returncode))
        return (process.returncode, stdout, stderr)

    def is_running(self):
        '''
        Checks to see if collector is started.

        It does this by calling C{status} on the collector binary.

        @rtype: bool
        @return: True if collector is started.
        '''
        is_running = False
        self.logger.info('Checking if Collector is running...')
        if self.is_installed():
            self.logger.info('Checking if '+ process_string + ' is Running on windows...')
            (_, stdout, _) = self.execute('status')
            is_running = 'SumoLogic Collector is running' in stdout
            self.logger.info(process_string + str(self._instance_id) + ' Running on windows:'+str(is_running))
        msg = 'Collector {0} running'.format('is' if is_running else 'is not')
        self.logger.info(msg)
        return is_running

    def uninstall(self):
        '''
        Uninstalls collector by running uninstall command
        '''
        self.logger.info('Uninstalling Collector...')
        try:
            # Standalone Installer
            cmd_binary = '%s%suninstall.exe' % (os.path.join(self.installer_path, 'SumoCollector'), os.sep)
            cmd_binary = '{0} {1}'.format(cmd_binary, self.COMMON_FLAGS)
            p = subprocess.Popen(shlex.split(cmd_binary), stderr=subprocess.PIPE, stdout=subprocess.PIPE)
            stddata = p.communicate()
        finally:
            pass

        self.logger.info('Collector has been uninstalled.')

    def install_from_archive(self, uninstall_existing=False):
        '''
        Installs this collector instance from an archive.

        The archive must be extractable by the L{archiver}

        @param archive_path: The path to the archive
        @type archive_path: str
        @param upgrade: Boolean flag that indicates if the archive install should/shouldn't override the existing collector_home
        @type upgrade: bool
        '''
        msg = 'Installing Collector from archive={0}'.format(self.installer_path)
        self.logger.info(msg)
        pkg = NightlyPackage(deployment=self._deployment)
        archive = pkg.download_to(self.installer_path)

        if(uninstall_existing==True):
            self.uninstall()

        try:
            # Standalone Installer
            cmd_binary = '%s -Vsumo.accessid=%s -Vsumo.accesskey=%s -Vcollector.url=%s -dir %s -Vollector.name=%s'
            cmd_binary = '{0} {1}'.format(cmd_binary, self.COMMON_FLAGS)
            self._pkg_installer_name = pkg._installer_name 
            installer_bin = os.path.join(self.installer_path, self._pkg_installer_name)
            os.mkdir(os.path.join(self.installer_path, 'SumoCollector'))
            if self._name is None:
                cmd_binary = cmd_binary % (installer_bin , self._username, self._password, self._url, \
                             os.path.join(self.installer_path, 'SumoCollector'), socket.gethostname())
            else:
                cmd_binary = cmd_binary % (installer_bin , self._username, self._password, self._url, \
                             os.path.join(self.installer_path, 'SumoCollector'), self._name)
            self._cmd_binary = cmd_binary
            p = subprocess.Popen(shlex.split(cmd_binary, posix=False), stderr=subprocess.PIPE, stdout=subprocess.PIPE)
            stddata = p.communicate()
        finally:
            pass

        self.logger.info('Collector has been installed.')
