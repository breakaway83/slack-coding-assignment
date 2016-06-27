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

LOGGER = logging.getLogger('TestHostMetrics')
verifier = VerifierBase()
tries = 10
time_to_wait = 10

class TestHostMetrics(object):
    def test_cpu_load_average(self, remote_sumo, handle_remotetest):
        LOGGER.info("Start a host metrics cpu load average.")
        restconn = handle_remotetest
        restconn.update_headers('accept', 'application/json')
        restconn.update_headers('content-type', 'application/json')
        # Check whether the source has been created
        COLLECTOR_URI = "%s%s" % (restconn.config.option.sumo_api_url, 'collectors')
        COLLECTOR_URI = COLLECTOR_URI.replace('https://', '')
        resp, cont = restconn.make_request("GET", COLLECTOR_URI)
        cont_json = json.loads(cont)
        outer_count_ptr = 0
        found_the_source = False
        for eachCollector in cont_json['collectors']:
            SOURCE_URI = "%s/%s/sources" % (COLLECTOR_URI, eachCollector[outer_count_ptr]['id'])
            SOURCE_URI = SORCE_URI.replace('https://', '')
            resp, cont = restconn.make_request("GET", SOURCE_URI)
            cont_json = json.loads(cont)
            inner_count_ptr = 0
            for eachSource in cont_json['sources']:
                if 'weimin_host_metrics' in eachSource[inner_count_ptr]['name']:
                    # Delete the source
                    ID_URI = "%s/%s" % (SOURCE_URI, eachSource[inner_count_ptr]['id'])
                    ID_URI = ID_URI.replace('https://', '')
                    resp, cont = restconn.make_request('DELETE', ID_URI)
                    found_the_source = True
                    break
                else:
                    inner_count_ptr += 1
            if found_the_source:
                break
            else:
                outer_count_ptr += 1
        # Create the host metrics source
        hostname = socket.gethostname()
        host_metrics_body = '{  "source":{    "name":"weimin_host_metrics",    "description":"weimin_host_metrics", \
                            "category":"weimin_host_metrics",    "automaticDateParsing":false,  \
                            "multilineProcessingEnabled":false,    "useAutolineMatching":false,    "forceTimeZone":false, \
                            "timeZone":"GMT",    "filters":[],    "cutoffTimestamp":0,    "encoding":"UTF-8",  \
                            "paused":false,    "sourceType":"SystemStats",    "interval":15000,    "hostName":"%s", \
                            "alive":true  }}'
        host_metrics_body = host_metrics_body % hostname
        resp, cont = restconn.make_request("POST", SOURCE_URI, host_metrics_body)

        # Let us get the "uptime" values first
        args = shlex.split('uptime')
        current_milli_time = lambda: int(round(time.time() * 1000))
        startTime = current_milli_time()
        p = subprocess.Popen(args, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        stddata = p.communicate()
        try:
            # This is on Linux
            cpu_load_avg_5_uptime = float(stddata[0].split('load average:')[1].split(',')[1].strip())
        except IndexError, e:
            # This is on OSX
            cpu_load_avg_5_uptime = float(stddata[0].split('load averages:')[1].split()[1].strip())
        # Get the cpu load avg from Sumo Metrics
        time.sleep(15)
        endTime = current_milli_time()
        query = '{"query":[{"query":"_source=weimin_host_metrics  metric=CPU_LoadAvg_5min","rowId":"A"}],"startTime":%s,\
                "endTime":%s, "requestedDataPoints": 600, "maxDataPoints": 800}'
        query = query % (startTime, endTime)
        METRICS_URI = "%s%s" % (restconn.config.option.sumo_api_url, 'metrics/results/')
        METRICS_URI = METRICS_URI.replace('https://', '')
        resp, cont = restconn.make_request("POST", METRICS_URI, query)
        result_json = json.loads(cont)
        cpu_load_avg_5_sumo = result_json['response'][0]['results'][0]['datapoints']['value'][0]
        logger = logging.getLogger()
        verifier.verify_true(abs(cpu_load_avg_5_uptime - cpu_load_avg_5_sumo) / cpu_load_avg_5_uptime < 0.01, \
                             "uptime %s is very different than Sumo %s" % (cpu_load_avg_5_uptime, cpu_load_avg_5_sumo))

    def test_cpu_load_average_with_collector(self, local_collector, connector_remotesumo):
        LOGGER.info("Start a host metrics cpu load average test with collector.")
        restconn = connector_remotesumo
        restconn.update_headers('accept', 'application/json')
        restconn.update_headers('content-type', 'application/json')
        # Check whether the source has been created
        COLLECTOR_URI = "%s%s" % (restconn.config.option.sumo_api_url, 'collectors')
        COLLECTOR_URI = COLLECTOR_URI.replace('https://', '')
        resp, cont = restconn.make_request("GET", COLLECTOR_URI)
        cont_json = json.loads(cont)
        for eachCollector in cont_json['collectors']:
            if eachCollector['name'] == socket.gethostname() and \
               eachCollector['alive']:
                collector_id = eachCollector['id']
                break
        individual_collector = "%s/%s" % (COLLECTOR_URI, eachCollector['id'])
        SOURCE_URI = "%s/sources" % individual_collector
        SOURCE_URI = SOURCE_URI.replace('https://', '')
        # Create the host metrics source
        hostname = socket.gethostname()
        host_metrics_body = '{  "source":{    "name":"weimin_host_metrics",    "description":"weimin_host_metrics", \
                            "category":"weimin_host_metrics",    "automaticDateParsing":false,  \
                            "multilineProcessingEnabled":false,    "useAutolineMatching":false,    "forceTimeZone":false, \
                            "timeZone":"GMT",    "filters":[],    "cutoffTimestamp":0,    "encoding":"UTF-8",  \
                            "paused":false,    "sourceType":"SystemStats",    "interval":15000,    "hostName":"%s", \
                            "alive":true  }}'
        host_metrics_body = host_metrics_body % hostname
        resp, cont = restconn.make_request("POST", SOURCE_URI, host_metrics_body)

        # Let us get the "uptime" values first
        args = shlex.split('uptime')
        current_milli_time = lambda: int(round(time.time() * 1000))
        startTime = current_milli_time()
        p = subprocess.Popen(args, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        stddata = p.communicate()
        try:
            # This is on Linux
            cpu_load_avg_5_uptime = float(stddata[0].split('load average:')[1].split(',')[1].strip())
        except IndexError, e:
            # This is on OSX
            cpu_load_avg_5_uptime = float(stddata[0].split('load averages:')[1].split()[1].strip())
        # Get the cpu load avg from Sumo Metrics
        time.sleep(15)
        endTime = current_milli_time()
        query = '{"query":[{"query":"_source=weimin_host_metrics  metric=CPU_LoadAvg_5min","rowId":"A"}],"startTime":%s,\
                "endTime":%s, "requestedDataPoints": 600, "maxDataPoints": 800}'
        query = query % (startTime, endTime)
        METRICS_URI = "%s%s" % (restconn.config.option.sumo_api_url, 'metrics/results/')
        METRICS_URI = METRICS_URI.replace('https://', '')

        for aTry in range(tries):
            resp, cont = restconn.make_request("POST", METRICS_URI, query)
            result_json = json.loads(cont)
            try:
                cpu_load_avg_5_sumo = result_json['response'][0]['results'][0]['datapoints']['value'][0]
                break
            except (IndexError, KeyError), e:
                if aTry < tries - 1:
                    time.sleep(time_to_wait)
                else:
                    raise e

        logger = logging.getLogger()
        verifier.verify_true(abs(cpu_load_avg_5_uptime - cpu_load_avg_5_sumo) / cpu_load_avg_5_uptime < 0.15, \
                             "uptime %s is very different than Sumo %s" % (cpu_load_avg_5_uptime, cpu_load_avg_5_sumo))

    def test_cpu_idle_with_graphite(self, local_collector, connector_remotesumo_graphite_source):
        LOGGER.info("Start a host metrics cpu load average test with collector.")
        restconn = connector_remotesumo_graphite_source
        restconn.update_headers('accept', 'application/json')
        restconn.update_headers('content-type', 'application/json')
        # Check whether the source has been created
        COLLECTOR_URI = "%s%s" % (restconn.config.option.sumo_api_url, 'collectors')
        COLLECTOR_URI = COLLECTOR_URI.replace('https://', '')
        resp, cont = restconn.make_request("GET", COLLECTOR_URI)
        cont_json = json.loads(cont)
        for eachCollector in cont_json['collectors']:
            if eachCollector['name'] == socket.gethostname() and \
               eachCollector['alive']:
                collector_id = eachCollector['id']
                break
        individual_collector = "%s/%s" % (COLLECTOR_URI, eachCollector['id'])
        SOURCE_URI = "%s/sources" % individual_collector
        SOURCE_URI = SOURCE_URI.replace('https://', '')
        # Create the host metrics source
        hostname = socket.gethostname()
        metrics_path = os.path.join(os.environ['TEST_DIR'], 'data', 'metrics', 'json', 'host_metrics.json')
        metrics_fd = open(metrics_path, 'r')
        content = metrics_fd.read()
        metrics_fd.close()
        content = content.replace('\n', ' ')
        host_metrics_body = content % hostname
        resp, cont = restconn.make_request("POST", SOURCE_URI, host_metrics_body)

        METRICS_URI = "%s%s" % (restconn.config.option.sumo_api_url, 'metrics/meta/catalog/query')
        METRICS_URI = METRICS_URI.replace('https://', '')
        query = '{"query":"_source=weimin_host_metrics", "offset":0, "limit":100}'
        resp, cont = restconn.make_request("POST", METRICS_URI, query)
        cont_dic = json.loads(cont)
        hash_tags = {}
	for itr in range(tries):
            try:
                for eachTag in cont_dic['results']:
                    if eachTag['name'] in hash_tags.keys():
                        hash_tags[eachTag['name']] += 1
                    else:
                        hash_tags[eachTag['name']] = 1
                break
            except KeyError, e:
                if itr < tries - 1:
                    time.sleep(time_to_wait)
                else:
                    raise e
        metrics_tags = hash_tags.keys()
        # Get host metrics list from file
        metrics_list = os.path.join(os.environ['TEST_DIR'], 'data', 'metrics', 'text', 'metrics_list')
        ml_fd = open(metrics_list, 'r')
        content = ml_fd.read()
        ml_fd.close()
        content_list = content.split('\n')
        for item in metrics_tags:
            if len(item) < 1:
                metrics_tags.remove(item)
        for item in content_list:
            if len(item) < 1:
                content_list.remove(item)
        metrics_tags.sort()
        content_list.sort()
        verifier.verify_true(len(metrics_tags) == len(content_list))
        for each in range(len(metrics_tags)):
            verifier.verify_true(str(metrics_tags[each]) == str(content_list[each]))

    def test_cpu_idle_with_graphite_service_api(self, servicerest_conn):
        restconn = servicerest_conn
        restconn.HEADERS.pop('Accept')
        restconn.HEADERS.pop('Content-Type')
        restconn.update_headers('accept', 'application/json, text/plain, */*')
        restconn.update_headers('content-type', 'application/json;charset=UTF-8')
        restconn.update_headers('connection', 'keep-alive')
        LOGIN_URI = "%s%s" % (restconn.config.option.sumo_api_url, 'authentication/loginwithcredentials')
        LOGIN_URI = LOGIN_URI.replace('https://', '')
        params = '{"email":"%s","password":"%s"}'
        params = params % (restconn.config.option.username, restconn.config.option.password)
        resp, cont = restconn.make_request('POST', LOGIN_URI, params)
        cookie = resp['set-cookie']
        restconn.update_headers('Cookie', cookie)
        cont_json = json.loads(cont)
        ApiSession = str(cont_json['apiSessionId'])

        ASID = "ASID=%s" % ApiSession
        cookie_new = "%s; %s" % (restconn.HEADERS['Cookie'], ASID)
        restconn.update_headers('Cookie', cookie_new)
        restconn.update_headers('ApiSession', ApiSession)
        # Get the folder where all the tabs exist
        MYLABS_URI = "%s%s" % (restconn.config.option.sumo_api_url, 'content/folder/mylabs')
        MYLABS_URI = MYLABS_URI.replace('https://', '')
        resp, cont = restconn.make_request('GET', MYLABS_URI)
        cont_json = json.loads(cont)
        # Grab the first children, and get its ID
        tab_id = cont_json['folder']['children'][0]['interactiveReportReference']['id']
        # Get the dashboard ID
        REPORT_URI = "%s%s" % (restconn.config.option.sumo_api_url, 'reports/%s' % tab_id)
        REPORT_URI = REPORT_URI.replace('https://', '')
        resp, cont = restconn.make_request('GET', REPORT_URI)
        cont_json = json.loads(cont)
        panel_id = cont_json['panels'][0]['id']
        # Create a session for the panel
        query_path = os.path.join(os.environ['TEST_DIR'], 'data', 'metrics', 'json', 'metrics_query.json')
        verifier.verify_true(os.path.exists(query_path))
        with codecs.open(query_path, encoding='utf-8') as data_file:
            content = data_file.read()
            content = content.replace('\n', '')

        content_fill = content % (panel_id, -900000, '_source=weimin_cloud_watch')
        SESSION_URI = "%s%s" % (restconn.config.option.sumo_api_url, 'reports/%s/sessionids' % tab_id)
        SESSION_URI = SESSION_URI.replace('https://', '')
        resp, cont = restconn.make_request('POST', SESSION_URI, str(content_fill))
        verifier.verify_true(resp.status == 200)
        cont_json = json.loads(cont)
        search_id = str(cont_json['results'][str(panel_id)]['searchQueryId'])
        QUERY_URI = "%s%s" % (restconn.config.option.sumo_api_url, 'reports/%s/sessionidsV2?sid=%s' % (tab_id, search_id))
        QUERY_URI = QUERY_URI.replace('https://', '')
        resp, cont = restconn.make_request('GET', QUERY_URI)
        verifier.verify_true(resp.status == 200)
