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
from testingframework.slack.base import Slack
from testingframework.slack.aws import AWSSlack
from testingframework.connector.base import Connector
from testingframework.log import Logging

LOGGER = Logging().logger


@pytest.fixture(scope="session")
def remote_slack(request):
    '''
    Slack Deployment
    '''
    LOGGER.info("Inside remote slack deployment fixture")
    slack_base_url = request.config.option.slack_base_url \
            if hasattr(request.config.option, 'slack_base_url') else \
            ''
    test_token = request.config.option.test_token \
            if hasattr(request.config.option, 'test_token') else \
            ''
    remote_slack= AWSSlack(slack_base_url)
    remote_slack.set_test_token_to_use(test_token)
    return remote_slack

@pytest.fixture(scope="session")
def connector_slack(request, remote_slack):
    '''
    This is setup & teardown. Creates restconnector,
    cleans connector in finalizer for slack APIs.
    '''
    LOGGER.info("Inside connector_slack.")
    test_token = request.config.option.test_token \
            if hasattr(request.config.option, 'test_token') else \
            ''
    slack_base_url = request.config.option.slack_base_url \
            if hasattr(request.config.option, 'slack_base_url') else \
            ''

    xstr = lambda s: s is not '' and s or None
    if(xstr(slack_base_url) != '' and xstr(test_token) != ''):
        remote_slack.create_logged_in_connector(contype=Connector.REST,
                                               test_token=test_token)

    restconn = remote_slack.connector(Connector.REST, test_token)
    restconn.config = request.config

    def fin():
        try:
            LOGGER.info("Teardown: removing remote slack connectors")
            remote_slack.remove_connector(Connector.REST, test_token)
        except Exception, err:
            LOGGER.warn("Failed to tear down rest connectors %s" % err)
    request.addfinalizer(fin)
    return restconn
