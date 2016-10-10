from testingframework.connector.base import Connector
from testingframework.util import fileutils
from sumotest.util.VerifierBase import VerifierBase
import logging
import pytest
import time
import os
import re
import json
from conftest import params

LOGGER = logging.getLogger('TestMetrics')
METRICS_URI = "nite-api.sumologic.net/api/v1/metrics/results"
verifier = VerifierBase()

class TestMetrics(object):
    def test_metrics_query(self, remote_sumo, handle_remotetest):
        LOGGER.info("Start a metrics query and get the result")
        restconn = handle_remotetest
        restconn.update_headers('accept', 'application/json')
        restconn.update_headers('content-type', 'application/json')
        query = '{"query":[{"query":"_source=weimin_cloud_watch","rowId":"A"}],"startTime":1462094640499,\
                "endTime":1462095540499, "requestedDataPoints": 600, "maxDataPoints": 800}'
        resp, cont = restconn.make_request("POST", METRICS_URI, query)
        assert resp['status'] == '200' or resp['status'] == '201'
