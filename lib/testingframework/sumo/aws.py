'''
Module for dealing with local Sumo deployment

@author: Weimin Ma
@contact: U{weimin@sumologic.com<mailto:weimin@sumologic.com>}
@since: 2016-04-25
'''

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

import testingframework.util.archiver as archiver
from .base import Sumo
from testingframework.util.fileutils import FileUtils
from testingframework.manager.jobs import Jobs


LOGGER = logging.getLogger('AWSSumo')

class AWSSumo(Sumo):
    '''
    Represents a AWS Sumo deployment.

    @ivar _sumo_url: The HTTP URL to an AWS Sumo deployment.
    @type _sumo_url: str
    '''

    def __init__(self, sumo_url, name=None):
        '''
        Creates a new AWS Sumo instance.

        @param : The AWS Sumo that the test runs against.
        @type sumo_url: str
        @raise InvalidSumoURL: If sumo_url is not a string.
        '''
        super(AWSSumo, self).__init__(name)
        self._validate_aws_url(sumo_url)
        self._sumo_url = sumo_url

    @classmethod
    def _validate_aws_url(cls, sumo_url):
        '''
        Validates the AWS URL variable.

        Currently these are the requirements:
          - Must be a string

        @raise InvalidSumoURL: If the sumo_url variable is invalid.
        '''
        if not isinstance(sumo_url, str):
            raise InvalidSumoURL('sumo_url must be a string')

    @property
    def _str_format(self):
        return '<{cls}@{id} name="{name}" sumo_url="{sumo_url}>'
    
    @property
    def _str_format_arguments(self):
        return {
            'cls': self.__class__.__name__,
            'id': id(self),
            'name': self.name,
            'sumo_url': self.sumo_url
        }
    

    @property
    def sumo_url(self):
        '''
        Returns the URL to a AWS Sumo deployment

        @rtype: str
        '''
        return self._sumo_url

    def get_event_count(self, search_string='*'):
        '''
        Displatches a search job and returns an event count without waiting for indexing to finish
        @param search_string: The search string
        '''
        LOGGER.info('Getting event count')
        event_count = 0
        jobs = Jobs(self.default_connector)
        job = jobs.create('search %s' % search_string)
        job.wait()
        event_count = job.get_event_count()
        LOGGER.debug('Event count: {ec}'.format(ec=event_count))
        return event_count

    def get_final_event_count(self, search_string='*', secondsToStable=60, retry_interval=30):
        '''
        Waits until indexing is done and then gives the final event count that the search reported.
        @param search_string: The search string
        @param secondsToStable: The time to wait with stable index before we decide indexing is done
        @param retry_interval: wait time b/w two successive search jobs
        '''
        resultPrev = -1
        resultSameSince = sys.maxint
        counts = []
        while True:
            time.sleep(retry_interval)
            result = self.get_event_count(search_string=search_string)
            now = int(time.time()) # time()'s precision will suffice here, and in fact seconds is all we want
            if result == resultPrev:
                if (now - resultSameSince) > secondsToStable: ### we have stable state
                    LOGGER.info('Achieved stable state for search %s with totalEventCount=%s' % (search_string, result))
                    return result # returns the final event count...
                if resultSameSince == sys.maxint:             ### our first time in what could become stable state
                    LOGGER.debug('Possibly entering stable state for search %s at totalEventCount=%s' % (search_string, result))
                    resultSameSince = lastPolledAt
                    LOGGER.debug('Using resultSameSince=%d ' % (resultSameSince))
                else:                                         ### our 2nd/3rd/... time in what could become stable state
                    LOGGER.debug('Confirming putative stable at totalEventCount=%s for search_string %s ' % (result, search_string))
            else:                                             ### we do NOT have stable state
                LOGGER.debug('Flux at totalEventCount=%s for search_string %s; delta +%s' % (result, search_string, (result-resultPrev)))
                resultPrev = result
                resultSameSince = sys.maxint
            lastPolledAt = now

    def install_collector_from_archive(self, archive_path, uninstall_existing=True):
        '''
        Installs this collector instance from an archive.

        The archive must be extractable by the L{archiver}

        @param archive_path: The path to the archive
        @type archive_path: str
        @param upgrade: Boolean flag that indicates if the archive install should/shouldn't override the existing collector
        @type upgrade: bool
        '''
        msg = 'Installing Collector from archive={0}'.format(archive_path)
        self.logger.info(msg)

        if(uninstall_existing==True):
            self.uninstall()

        collector_dir = os.path.join(archive_path, 'SumoCollector')
        try:
            # ./SumoCollector_linux_amd64_20_1-2684.sh -Vsumo.accesskey=ksjaWPMnQw4uuw2OYOpDpL7Ua7HM40A3i3ds6KWljHNs6DKmOoLPKUeoWv0dzIDg 
            # -Vsumo.accessid=su1y380CfPZUxG -Vcollector.url=https://stag-events.sumologic.net -dir ~/SumoCollector -Vcollector.name=52.91.186.149 -q

        finally:
            msg = 'Removing extracted files from {0}'.format(directory)
            self.logger.info(msg)
            self._file_utils.force_remove_directory(directory)

        self.logger.info('Collector has been installed.')


class InvalidSumoURL(RuntimeError):
    '''
    Raised when the given sumo_url is invalid
    '''
    pass
