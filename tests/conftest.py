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
    splk_group = parser.getgroup("Sumo Options")
    splk_group.addoption('--sumo_api_url', dest='sumo_api_url',
                     help='Sumo deployment API url',
                     default="")
    splk_group.addoption('--collector_url', dest='collector_url',
                     help='Collector registration url',
                     default="")
    splk_group.addoption('--deployment', dest='deployment',
                     help='Name of Sumo deployment',
                     default="")
    splk_group.addoption('--username', dest='username',
                     help='Sumo username to access Sumo deployment',
                     default="")
    splk_group.addoption('--password', dest='password',
                     help='Sumo password to access Sumo deployment',
                     default="")
    splk_group.addoption('--accessid', dest='accessid',
                     help='Sumo accessid to access Sumo deployment',
                     default="")
    splk_group.addoption('--accesskey', dest='accesskey',
                     help='Sumo accesskey to access Sumo deployment',
                     default="")
