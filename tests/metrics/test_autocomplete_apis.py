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
import datetime
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
        time_time = time.time()
        end_milli_time = lambda: int(round(time_time * 1000))
        start_milli_seconds = lambda: int(round((time_time + datetime.timedelta(minutes=-15).total_seconds()) * 1000))
        query = "_source=weimin_cloud_watch"
        content_fill = content % (1, query, len(query), start_milli_seconds(), end_milli_time(), 1)
        resp, cont = restconn.make_request("POST", AUTOCOMPLETE_URI, str(content_fill))
        cont_dict = json.loads(cont)
        verifier.verify_true(len(cont_dict['suggestions']) > 0)

        query = "_sourceCategory=weimin_graphite  _3=cpu-idle | avg"
        content_fill = content % (1, query, len(query) + 1, start_milli_seconds(), end_milli_time(), 1)
        resp, cont = restconn.make_request("POST", AUTOCOMPLETE_URI, str(content_fill))
        cont_dict = json.loads(cont)
        verifier.verify_true(len(cont_dict['suggestions']) > 0)

        pytest.set_trace()
