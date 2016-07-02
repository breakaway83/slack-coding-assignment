import subprocess
import os
import tempfile
import shlex
import urllib2
import platform
import time
import sys
import re
import logging
import socket

import testingframework.util.archiver as archiver
from .base import Collector
from testingframework.util.fileutils import FileUtils
from testingframework.collector_package.collector_nightly import NightlyPackage
from testingframework.collector_package.collector_release import ReleasedPackage
from testingframework.exceptions.command_execution import CommandExecutionFailure
from testingframework.util.portutil import PortUtil


LOGGER = logging.getLogger('LocalCollector')

class LocalCollector(Collector):
    '''
    Represents a local collector instance.

    @ivar _installer_path: The path to the collector installations root.
    @type _installer_path: str
    @cvar COMMON_FLAGS: The most flags that are most commonly used. They are
                        recommended when installing the collector
    @type COMMON_FLAGS: str
    '''
    COMMON_FLAGS = '-q'

    def __init__(self, installer_path, name=None):
        '''
        Creates a new LocalCollector instance.

        @param installer_path: The local that collector is/will be installed.
        @type installer_path: str
        @raise InvalidCollectorHome: If installer_path is not a string.
        '''
        super(LocalCollector, self).__init__(installer_path)
        self._validate_collector_home(installer_path)

        self._installer_path = os.path.abspath(installer_path)
        self._name = name
        self._file_utils = FileUtils()
        self._is_windows = platform.system() == 'Windows'
        self._collector_name = None

    @classmethod
    def _validate_collector_home(cls, collector_home):
        '''
        Validates the collector_home variable.

        Currently these are the requirements:
          - Must be a string

        @raise InvalidCollectorHome: If the collector_home variable is invalid.
        '''
        if not isinstance(collector_home, str):
            raise InvalidCollectorHome('collector_home must be a string')

    @property 
    def fileutils(self):
        return self._file_utils
    
    @property
    def _str_format(self):
        return '<{cls} name="{name}" collector_home="{collector_home}>'
    
    @property
    def _str_format_arguments(self):
        return {
            'cls': self.__class__.__name__,
            'name': self.name,
            'collector_home': self.collector_home
        }
    

    def _binary_exists(self, binary=None):
        '''
        Checks if the specified collector binary exists.

        If the binary is not specified the collector binary is checked.

        This calls the L{get_binary_path} method.

        @param binary: The binary to look for or None
        @type binary: str
        @return: True if it exists
        @rtype: bool
        '''
        binary = self.get_binary_path(binary or self.collector_binary)
        return os.path.isfile(binary or self.collector_binary)

    @property
    def collector_binary(self):
        '''
        Returns the absolute path to the collector binary

        @rtype: str
        '''
        if self._is_windows:
           return self.get_binary_path('collector.bat')
        return self.get_binary_path('collector')

    def get_binary_path(self, binary):
        '''
        Returns the absolute path to the specified binary.

        If the path is already absolute it is returned as is.

        @param binary: The binary to return the path for
        @type binary: str
        @rtype: str
        @return: The absolute path to the binary
        '''
        if os.path.isabs(binary):
            return binary
        return os.path.join(os.path.join(self._installer_path, 'SumoCollector'), binary)

    def is_installed(self):
        '''
        Checks if this collector instance is installed.

        It checks if the collector binary exists.
        Also checks binary status returns "SumoLogic Collector is running"

        @rtype: bool
        @return: True if collector is installed.
        '''
        self.logger.info('Checking if collector is installed...')
        r = self._binary_exists()
        self.logger.info('Collector is{0} installed'.format('' if r else ' not'))
        return r

    def execute(self, command):
        '''
        Executes the specified command using the collector binary.

        This will add the L{common flags<COMMON_FLAGS>} to the command.

        @param command: The command to execute. Remember to quote strings with
                        spaces.
        @type command: str
        @return: (code, stdout, stderr)
        @rtype: tuple(int, str, str)
        @raise CollectorNotInstalled: If the collector binary doesn't exist
        '''
        #command = '{0} {1}'.format(command, self.COMMON_FLAGS)
        return self.execute_with_binary(self.collector_binary, command)

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
        cmd.extend(shlex.split(command))

        self.logger.info('Executing command {0}'.format(' '.join(cmd)))

        process = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        (stdout, stderr) = process.communicate()
        self.logger.info('Done! Exit code {0}'.format(process.returncode))
        return (process.returncode, stdout, stderr)

    def start(self, auto_ports=False):
        '''
        Starts collector.

        @return: The exit code of the command.
        @rtype: int
        @raise CouldNotStartCollector: If collector is not running after starting it.
        '''
        if not self.is_running():
            self.logger.info('Starting collector...')
            cmd = 'start'
            (code, stdout, stderr) = self.execute(cmd)
            self.logger.info('Collector has been started with version {version}'.format(version=self.version()))
            counter = 0            
            while not self.is_running() and counter < 6:
                time.sleep(10)
                counter = counter + 1
            self._verify_collector_is_running(cmd, code, stdout, stderr)
            return code
        else:
            self.logger.info('Collector is already running')

    def _verify_collector_is_running(self, command, code, stdout, stderr):
        '''
        Checks if collector is running raising an exception if not.

        @param command: The command that was run
        @type command: str
        @param code: The exit code.
        @type code: int
        @param stdout: The stdout that was printed by the command.
        @type stdout: str
        @param stderr: The stderr that was printed by the command.
        @type stderr: str
        @raise CouldNotStartCollector: If collector is not running.
        '''
        self.logger.info('Verifying that collector is running...')
        if not self.is_running():
            self.logger.info('Collector is not running')
            raise CouldNotStartCollector(command, code, stdout, stderr)
        self.logger.info('Collector is running')

    def stop(self):
        '''
        Stops Collector.

        @return: The exit code of the command.
        @rtype: int
        @raise CouldNotStopCollector: If Collector is still running after stopping it.
        '''
        self.logger.info('Stopping Collector...')
        cmd = 'stop'
        (code, stdout, stderr) = self.execute(cmd)
        self.logger.info('Collector has been stopped')
        self._verify_collector_is_not_running(cmd, code, stdout, stderr)
        return code

    def _verify_collector_is_not_running(self, command, code, stdout, stderr):
        '''
        Checks if Collector is running raising an exception if it is.

        @param command: The command that was run
        @type command: str
        @param code: The exit code.
        @type code: int
        @param stdout: The stdout that was printed by the command.
        @type stdout: str
        @param stderr: The stderr that was printed by the command.
        @type stderr: str
        @raise CouldNotStopCollector: If Collector is running.
        '''
        self.logger.info('Verifying that Collector is not running...')
        if self.is_running():
            self.logger.info('Collector is running')
            raise CouldNotStopCollector(command, code, stdout, stderr)
        self.logger.info('Collector is not running')

    def restart(self):
        '''
        Restarts Collector.

        Calls L{stop} and then L{start}

        @return: Always 0 (for compatibility with L{start}/L{stop}).
        @rtype: int
        @raise CouldNotRestartCollector: If collector failed to restart.
        '''
        self.logger.info('Restarting collector...')
        try:
            self.logger.debug('Stopping collector inside .restart()')
            cmd = 'restart'
            (code, stdout, stderr) = self.execute(cmd)
            time.sleep(4)
            counter = 0

            while not self.is_running() and counter < 6:
                time.sleep(10)
                counter = counter + 1

            self._verify_collector_is_running(cmd, code, stdout, stderr)
        except CommandExecutionFailure, err:
            self.logger.info('Restarting collector failed')
            raise CouldNotRestartCollector(err.command, err.code, err.stdout,
                                        err.stderr)
        self.logger.info('Collector has been restarted')
        return code

    def is_running(self):
        '''
        Checks to see if Collector is started.

        It does this by calling C{status} on the Collector binary.

        @rtype: bool
        @return: True if Collector is started.
        '''
        is_running = False
        self.logger.info('Checking if Collector is running...')
        if self.is_installed():
            (_, stdout, _) = self.execute('status')
            is_running = 'SumoLogic Collector is running' in stdout
        msg = 'Collector {0} running'.format('is' if is_running else 'is not')
        self.logger.info(msg)
        return is_running

    def get_host_os(self):
        '''
        Returns the host os.
        '''
        return  platform.system()
 
    def uninstall(self):
        '''
        Uninstalls collector by running uninstall command
        '''
        self.logger.info('Uninstalling Collector...')
        try:
            # Standalone Installer
            cmd_binary = '%s%suninstall' % (os.path.join(self.installer_path, 'SumoCollector'), os.sep)
            cmd_binary = '{0} {1}'.format(cmd_binary, self.COMMON_FLAGS)
            p = subprocess.Popen(shlex.split(cmd_binary), stderr=subprocess.PIPE, stdout=subprocess.PIPE)
            stddata = p.communicate()
        finally:
            pass

        self.logger.info('Collector has been uninstalled.')

    def _stop_collector_if_needed(self):
        '''
        Stops Collector if it is running.
        '''
        if self.is_running():
            self.logger.debug("Stopping Collector inside "
                              "._stop_collector_if_needed()")
            self.stop()

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
            if(self._username is not None and self._password is not None):
                cmd_binary = 'sh %s -Vsumo.email=%s -Vsumo.password=%s -Vcollector.url=%s -dir %s -Vollector.name=%s'
                cmd_binary = '{0} {1}'.format(cmd_binary, self.COMMON_FLAGS)
                installer_bin = os.path.join(self.installer_path, pkg._installer_name)
                if self._name is None:
                    self._collector_name = socket.gethostname()
                    cmd_binary = cmd_binary % (installer_bin , self._username, self._password, self._url, \
                                 os.path.join(self.installer_path, 'SumoCollector'), socket.gethostname())
                else:
                    self._collector_name = self._name
                    cmd_binary = cmd_binary % (installer_bin , self._username, self._password, self._url, \
                                 os.path.join(self.installer_path, 'SumoCollector'), self._name)
            else:
                cmd_binary = 'sh %s -Vsumo.accessid=%s -Vsumo.accesskey=%s -Vcollector.url=%s -dir %s -Vollector.name=%s'
                cmd_binary = '{0} {1}'.format(cmd_binary, self.COMMON_FLAGS)
                installer_bin = os.path.join(self.installer_path, pkg._installer_name)
                if self._name is None:
                    self._collector_name = socket.gethostname()
                    cmd_binary = cmd_binary % (installer_bin , self._accessid, self._accesskey, self._url, \
                                 os.path.join(self.installer_path, 'SumoCollector'), socket.gethostname())
                else:
                    self._collector_name = self._name
                    cmd_binary = cmd_binary % (installer_bin , self._accessid, self._accesskey, self._url, \
                                 os.path.join(self.installer_path, 'SumoCollector'), self._name)
            p = subprocess.Popen(shlex.split(cmd_binary), stderr=subprocess.PIPE, stdout=subprocess.PIPE)
            stddata = p.communicate()
        finally:
            pass

        self.logger.info('Collector has been installed.')

    def _find_archive_directory_name(self, directory):
        """
        Tries to find the directory name of an extracted Collector archive.

        It will iterate over L{_POSSIBLE_ARCHIVE_DIRECTORIES} and see if that
        entry exists.

        @param directory: The directory that the package was extracted to.
        @type directory: str
        @return: The path to the Collector directory.
        @rtype: str
        @raise CouldNotFindCollectorDirectory: If the directory could not be
                                            guessed.
        """
        self.logger.info('Trying to find extracted directory name')
        entries = os.listdir(directory)
        for name in self._POSSIBLE_ARCHIVE_DIRECTORIES:
            if name in entries:
                self.logger.info("{0} - Exists".format(name))
                return os.path.join(directory, name)
            else:
                self.logger.info("{0} - Doesn't exist".format(name))
        raise CouldNotFindCollectorDirectory


class InvalidCollectorHome(RuntimeError):
    '''
    Raised when the given collector_home variable is invalid
    '''
    pass


class CollectorNotInstalled(RuntimeError):
    '''
    Raised when an action that requires collector to be installed is called but
    collector is not installed.
    '''


class BinaryMissing(RuntimeError):
    '''
    Raised when trying to execute a command with a non existent binary.
    '''

    def __init__(self, binary):
        '''
        Creates the exception.

        @param binary: The binary that is missing
        @type binary: str
        '''
        message = "The {0} binary doesn't exist".format(binary)
        super(BinaryMissing, self).__init__(message)


class CouldNotFindCollectorirectory(RuntimeError):
    """
    Raised when the name of the directory in a collector package could not be
    guessed.
    """

    def __init__(self, msg=None):
        msg = msg or 'Could not find the collector build inside the archive.'
        RuntimeError.__init__(self, msg)


class CouldNotStartCollector(CommandExecutionFailure):
    '''
    Raised when a collector start fails.
    '''
    pass


class CouldNotStopCollector(CommandExecutionFailure):
    '''
    Raised when a collector stop fails.
    '''
    pass
