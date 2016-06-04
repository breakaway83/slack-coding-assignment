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
from conftest import params
from datetime import datetime, timedelta

LOGGER = logging.getLogger('TestCollectorInstall')
verifier = VerifierBase()

class TestCollector(object):
    def test_local_file_source(self, remote_sumo, local_collector, connector_remotesumo):
        restconn = connector_remotesumo
        restconn.update_headers('accept', 'application/json')
        restconn.update_headers('content-type', 'application/json')
        # Check whether the source has been created
        collector_api = "%s%s" % (restconn.config.option.sumo_api_url, 'collectors')
        collector_api = collector_api.replace('https://', '')
        resp, cont = restconn.make_request("GET", collector_api)
        cont_json = json.loads(cont)
        for eachCollector in cont_json['collectors']:
            if eachCollector['name'] == socket.gethostname() and \
               eachCollector['alive']:
                collector_id = eachCollector['id']
                break
        source_path = os.path.join(os.environ['TEST_DIR'], 'data', 'collector', 'json', 'source.json')
        source_fd = open(source_path, 'r')
        content = source_fd.read()
        source_fd.close()
        content = content.replace('\n', ' ')
        content = content % (socket.gethostname(), os.path.join(local_collector.get_binary_path('logs'), 'collector.log'))

        source_api = "%s/%s/sources" % (collector_api, collector_id)
        resp, cont = restconn.make_request("POST", source_api, content)
        # Search for the newly created source
        search_path = os.path.join(os.environ['TEST_DIR'], 'data', 'search', 'json', 'local_file_search_job.json')
        search_fd = open(search_path, 'r')
        original_content = search_fd.read()
        search_fd.close()
        urlparam = {'limit': 100, 'offset': 0}
        tries = 10
        time_to_wait = 10

        for aTry in range(tries):
            content = original_content.replace('\n', ' ')
            content = content % ('weimin_local_file', (datetime.now() + timedelta(minutes=-15)).replace(microsecond=0).isoformat(), \
                                 datetime.now().replace(microsecond=0).isoformat())
            SEARCH_API = "%s/search/jobs" % '/'.join(collector_api.split('/')[:-1])
            resp, cont = restconn.make_request("POST", SEARCH_API, content)
            cont_json = json.loads(cont)
            RESULT_API = "%s/%s/messages" % (SEARCH_API, cont_json['id'])
            resp, cont = restconn.make_request('GET', RESULT_API, urlparam=urlparam)
            cont_json = json.loads(cont)
            try:
                verifier.verify_true(len(cont_json['messages']) > 0)
                break
            except KeyError, e:
                if aTry < tries - 1:
                    time.sleep(time_to_wait)
                else:
                    raise e

        resp, cont = restconn.make_request('GET', source_api)
        cont_json = json.loads(cont)
        individual_source = "%s/%s" % (source_api, cont_json['sources'][0]['id'])
        resp, cont = restconn.make_request('DELETE', individual_source)
        verifier.verify_true(resp.status == 200)
