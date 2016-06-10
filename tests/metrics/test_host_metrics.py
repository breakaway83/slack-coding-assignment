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

LOGGER = logging.getLogger('TestHostMetrics')
verifier = VerifierBase()

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
        verifier = VerifierBase()
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

        tries = 10
        time_to_wait = 10
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
        verifier = VerifierBase()
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
        metrics_path = source_path = os.path.join(os.environ['TEST_DIR'], 'data', 'metrics', 'json', 'host_metrics.json')
        metrics_fd = open(metrics_path, 'r')
        content = metrics_fd.read()
        metrics_fd.close()
        content = content.replace('\n', ' ')
        host_metrics_body = content % hostname
        resp, cont = restconn.make_request("POST", SOURCE_URI, host_metrics_body)

        pytest.set_trace()

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

        tries = 10
        time_to_wait = 10
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
        verifier = VerifierBase()
        verifier.verify_true(abs(cpu_load_avg_5_uptime - cpu_load_avg_5_sumo) / cpu_load_avg_5_uptime < 0.15, \
                             "uptime %s is very different than Sumo %s" % (cpu_load_avg_5_uptime, cpu_load_avg_5_sumo))
