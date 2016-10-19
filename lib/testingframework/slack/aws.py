'''
Module for dealing with cloud slack deployment

@author: Weimin Ma
@contact: U{wma.utd@gmail.com<mailto:wma.utd@gmail.com>}
@since: 2016-10-13
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
from testingframework.log import Logging
from .base import Slack


LOGGER = Logging('AWSSlack').logger

class AWSSlack(Slack):
    '''
    Represents a AWS slack deployment.

    @ivar _slack_url: The HTTP URL to an AWS slack deployment.
    @type _slack_url: str
    '''

    def __init__(self, slack_url, name=None):
        '''
        Creates a new AWS slack instance.

        @param : The AWS slack that the test runs against.
        @type slack_url: str
        @raise InvalidSlackURL: If slack_url is not a string.
        '''
        super(AWSSlack, self).__init__(name)
        self._validate_aws_url(slack_url)
        self._slack_url = slack_url

    @classmethod
    def _validate_aws_url(cls, slack_url):
        '''
        Validates the Slack URL variable.

        Currently these are the requirements:
          - Must be a string

        @raise InvalidSlackURL: If the slack_url variable is invalid.
        '''
        if not isinstance(slack_url, str):
            raise InvalidSlackURL('slack_url must be a string')

    @property
    def _str_format(self):
        return '<{cls}@{id} name="{name}" slack_url="{slack_url}>'
    
    @property
    def _str_format_arguments(self):
        return {
            'cls': self.__class__.__name__,
            'id': id(self),
            'name': self.name,
            'slack_url': self.slack_url
        }
    

    @property
    def slack_url(self):
        '''
        Returns the URL to a AWS Slack deployment

        @rtype: str
        '''
        return self._slack_url

class InvalidSlackURL(RuntimeError):
    '''
    Raised when the given slack_url is invalid
    '''
    pass
