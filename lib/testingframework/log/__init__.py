'''
Created on October, 2016

@author: weimin
'''

import datetime
import logging

from logging import FileHandler, Formatter

_LOG_FORMAT = '[%(asctime)s] %(levelname)s - %(name)s: %(message)s'
_DATE_FORMAT = '%Y-%m-%d %H:%M:%S.%f'
_FILE_NAME = "testingframework.log"


def setup_logger(debug=False):
    """
    Setups up the logging library

    @param debug: If debug log messages are to be outputted
    @type debug: bool
    """
    logger = logging.getLogger('')
    handler = FileHandler(filename=_FILE_NAME, mode="w")
    handler.setFormatter(HelmutFormatter(_LOG_FORMAT))
    level = logging.INFO
    if debug:
        level = logging.DEBUG
    logger.addHandler(handler)
    logger.setLevel(level)
    logger.debug('Logger: DEBUG logging is enabled')


class TestingFrameworkFormatter(Formatter):

    # Disabling error b/c function overrides old style Python function
    # pylint: disable=C0103
    def formatTime(self, record, datefmt=None):
        t = datetime.datetime.now()
        # The [:-3] is put there to trim the last three digits of the
        # microseconds, remove it if you intend to remove microseconds
        # from the _DATE_FORMAT
        return t.strftime(_DATE_FORMAT)[:-3]

from abc import ABCMeta


class Logging(object):

    __metaclass__ = ABCMeta

    def __init__(self):
        self._logger = self._get_logger()
        # self._log_init_message()  # commenting out, not useful and annoying

    def _get_logger(self):
        '''
        Creates a new logger for this instance, should only be called once.

        @return: The newly created logger.
        '''
        return logging.getLogger(self._logger_name)

    @property
    def _logger_name(self):
        '''
        The name of the logger.

        @rtype: str
        '''
        return self.__class__.__name__

    @property
    def logger(self):
        '''
        The logger of this Slack object.

        @return: The associated logger.
        '''
        return self._logger

    def _log_init_message(self):
        '''
        Logs a message saying this instance has been created.
        '''
        self.logger.info('Created {self}'.format(self=self))
