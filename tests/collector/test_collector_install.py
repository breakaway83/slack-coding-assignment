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
import random
import sys
from conftest import params
from datetime import datetime, timedelta

LOGGER = logging.getLogger('TestCollectorInstall')
verifier = VerifierBase()
tries = 20
time_to_wait = 30

class TestCollectorInstall(object):
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
            except (KeyError, AssertionError), e:
                if aTry < tries - 1:
                    time.sleep(time_to_wait)
                else:
                    raise e

        resp, cont = restconn.make_request('GET', source_api)
        cont_json = json.loads(cont)
        individual_source = "%s/%s" % (source_api, cont_json['sources'][0]['id'])
        resp, cont = restconn.make_request('DELETE', individual_source)
        verifier.verify_true(resp.status == 200)

    def test_collector_upgrade(self, remote_sumo, local_collector, connector_remotesumo):
        restconn = connector_remotesumo
        restconn.update_headers('accept', 'application/json')
        restconn.update_headers('content-type', 'application/json')
        collector_uri = "%s%s" % (restconn.config.option.sumo_api_url, 'collectors')
        collector_uri = collector_uri.replace('https://', '')
        resp, cont = restconn.make_request("GET", collector_uri)
        cont_json = json.loads(cont)
        collector_id = None
        for eachCollector in cont_json['collectors']:
            if socket.gethostname() in str(eachCollector['name']):
                if eachCollector['alive']:
                    collector_id = eachCollector['id']
                    break
        verifier.verify_false(collector_id is None)

        collector_builds = "%s%s" % (restconn.config.option.sumo_api_url, 'collectors/upgrades/targets')
        collector_builds = collector_builds.replace('https://', '')
        resp, cont = restconn.make_request("GET", collector_builds)
        cont_json = json.loads(cont)
        other_versions = []
        for each in cont_json['targets']:
            if each['latest'] == True:
                current_version = str(each['version'])
            else:
                other_versions.append(each)
        upgrade_version = str(other_versions[random.randint(0, len(other_versions))]['version'])

        collector_upgrade_api = "%s%s" % (restconn.config.option.sumo_api_url, 'collectors/upgrades')
        collector_upgrade_api = collector_upgrade_api.replace('https://', '')
        if sys.platform == 'win32':
            rest_params = "{\"collectorId\":%s,\"toVersion\":\"%s\"}" % (collector_id, upgrade_version)
        else:
            rest_params = '{"collectorId":%s,"toVersion":"%s"}' % (collector_id, upgrade_version)
        for aTry in range(tries):
            try:
                resp, cont = restconn.make_request("POST", collector_upgrade_api, rest_params)
                verifier.verify_false(resp.status == 400)
                break
            except AssertionError, e:
                if aTry < tries - 1:
                    time.sleep(time_to_wait)
                else:
                    raise e
        cont_json = json.loads(cont)

        status_uri = "%s%s" % (restconn.config.option.sumo_api_url, "collectors/upgrades/%s" % cont_json['id'])
        status_uri = status_uri.replace('https://', '')
        upgrade_done = False
        for aTry in range(tries):
            resp, cont = restconn.make_request("GET", status_uri)
            cont_json = json.loads(cont)
            if cont_json['upgrade']['status'] == 2:
                upgrade_done = True
                break
        verifier.verify_true(upgrade_done)
