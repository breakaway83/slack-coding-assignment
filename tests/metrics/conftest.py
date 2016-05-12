import logging
import time
import os
import platform
import pytest

from testingframework.sumo.aws import AWSSumo
from testingframework.connector.base import Connector


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
    splk_group.addoption('--remote_url', dest='remote_url',
                     help='Sumo deployment url',
                     default="")
    splk_group.addoption('--username', dest='username',
                     help='Sumo username to access Sumo deployment',
                     default="Administrator")
    splk_group.addoption('--password', dest='password',
                     help='Sumo password to access Sumo deployment',
                     default="")

@pytest.fixture(scope="session")
def remote_sumo(request):
    '''
    Sumo Deployment
    '''
    LOGGER.info("Inside remote sumo deployment fixture")
    remote_url = request.config.option.remote_url \
               if hasattr(request.config.option, 'remote_url') else \
               ''
    username = request.config.option.username \
               if hasattr(request.config.option, 'username') else \
               'Administrator'
    password = request.config.option.password \
               if hasattr(request.config.option, 'password') else \
               'Testing123@'
    remote_sumo = AWSSumo(remote_url)
    return remote_sumo


@pytest.fixture(scope="class")
def handle_remotetest(request, remote_sumo):
    '''
    This is setup & teardown. Creates restconnector,
    cleans connector in finalizer for remote sumo.
    '''
    LOGGER.info("Inside handle_remotetest")
    username = request.config.option.username \
               if hasattr(request.config.option, 'username') else \
               'Administrator'
    password = request.config.option.password \
               if hasattr(request.config.option, 'password') else \
               'Testing123@'

    remote_sumo.create_logged_in_connector(contype=Connector.REST,
                                           username=username,
                                           password=password)
    restconn = remote_sumo.connector(Connector.REST, username)
    restconn.config = request.config

    def fin():
        try:
            LOGGER.info("Teardown: removing remote sumo connectors")
            remote_sumo.remove_connector(Connector.REST, username)
        except Exception, err:
            LOGGER.warn("Failed to tear down rest connectors %s" % err)
    request.addfinalizer(fin)
    return restconn
