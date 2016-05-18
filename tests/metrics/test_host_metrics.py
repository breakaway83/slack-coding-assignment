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
from conftest import params

LOGGER = logging.getLogger('TestHostMetrics')
METRICS_URI = "nite-api.sumologic.net/api/v1/metrics/results"
verifier = VerifierBase()

class TestHostMetrics(object):
    def test_cpu_load_average(self, remote_sumo, handle_remotetest):
        LOGGER.info("Start a host metrics cpu load average.")
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
        restconn = handle_remotetest
        restconn.update_headers('accept', 'application/json')
        restconn.update_headers('content-type', 'application/json')
        time.sleep(15)
        endTime = current_milli_time()
        query = '{"query":[{"query":"_source=weimin_host_metrics  metric=CPU_LoadAvg_5min","rowId":"A"}],"startTime":%s,\
                "endTime":%s, "requestedDataPoints": 600, "maxDataPoints": 800}'
        query = query % (startTime, endTime)
        resp, cont = restconn.make_request("POST", METRICS_URI, query)
        result_json = json.loads(cont)
        cpu_load_avg_5_sumo = result_json['response'][0]['results'][0]['datapoints']['value'][0]
        logger = logging.getLogger()
        verifier = VerifierBase()
        verifier.verify_true(abs(cpu_load_avg_5_uptime - cpu_load_avg_5_sumo) / cpu_load_avg_5_uptime < 0.01, \
                             "uptime %s is very different than Sumo %s" % (cpu_load_avg_5_uptime, cpu_load_avg_5_sumo))
