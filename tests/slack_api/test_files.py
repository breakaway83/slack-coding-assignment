from testingframework.connector.base import Connector
from slacktest.util.VerifierBase import VerifierBase
import logging
import pytest
import time
import os
import re
import json
from conftest import params

LOGGER = logging.getLogger('TestFiles')
SLACK_URI = "slack.com/api/files.list"
verifier = VerifierBase()

class TestFiles(object):
    def test_files_list(self, remote_slack, connector_slack):
        LOGGER.info("Start a metrics query and get the result")
        restconn = connector_slack
        restconn.update_headers('accept', 'application/json')
        restconn.update_headers('content-type', 'application/json')
        params = {'token': remote_slack.test_token}
        resp, cont = restconn.make_request("GET", SLACK_URI, urlparam=params)

        pytest.set_trace()

        assert resp['status'] == '200' or resp['status'] == '201'
