from testingframework.connector.base import Connector
from testingframework.util import fileutils
from sumotest.util.VerifierBase import VerifierBase
import logging
import pytest
import time
import os
import re
import json
import subprocess
import shlex
import socket
import codecs
from conftest import params

LOGGER = logging.getLogger('TestAutocompleteAPIs')
verifier = VerifierBase()
tries = 10
time_to_wait = 10

class TestAutocompleteAPIs(object):

    def test_autocomplate_api(self, handle_remotetest):
        restconn = handle_remotetest
        restconn.update_headers('accept', 'application/json, text/plain, */*')
        restconn.update_headers('content-type', 'application/json;charset=UTF-8')
        restconn.update_headers('connection', 'keep-alive')
        AUTOCOMPLETE_URI = "%s%s" % (restconn.config.option.sumo_api_url, 'metrics/suggest/autocomplete')
        AUTOCOMPLETE_URI = AUTOCOMPLETE_URI.replace('https://', '')
        autocomplete_path = os.path.join(os.environ['TEST_DIR'], 'data', 'metrics', 'json', 'metrics_autocomplete.json')
        verifier.verify_true(os.path.exists(autocomplete_path))
        with codecs.open(autocomplete_path, encoding='utf-8') as data_file:
            content = data_file.read()
            content = content.replace('\n', '')

        pytest.set_trace()
