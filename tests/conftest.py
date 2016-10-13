import logging
import time
import os
import platform
import pytest
import os
import shutil
import shlex
import socket
import json
import subprocess

LOGGER = logging.getLogger()


def pytest_generate_tests(metafunc):
    for funcargs in getattr(metafunc.function, 'funcarglist', ()):
        if 'testname' in funcargs:
            testname = "%s" % funcargs['testname']
        metafunc.addcall(funcargs=funcargs, id=testname)


def params(funcarglist):
    """
    method used with generated/parameterized tests, can be used to decorate
    your test function with the parameters.  Each dict in your list
    represents on generated test.  The keys in that dict are the parameters
    to be used for that generated test
    """
    def wrapper(function):
        function.funcarglist = funcarglist
        return function
    return wrapper


def pytest_addoption(parser):
    '''
    This is a pytest hook to add options from the command line so that
    we can use it later.
    '''
    splk_group = parser.getgroup("Slack Coding Assignment")
    splk_group.addoption('--slack_base_url', dest='slack_base_url',
                     help='slack\'s base url',
                     default="https://slack.com/api/")
    splk_group.addoption('--test_token', dest='test_token',
                     help='test token to access slack APIs',
                     default='')
