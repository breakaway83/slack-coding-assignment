from testingframework.connector.base import Connector
from testingframework.log import Logging
from testingframework.util.fileutils import FileUtils
from slacktest.util.VerifierBase import VerifierBase
import pytest
import time
import os
import re
import json
import urllib
from conftest import params

logging = Logging()
LOGGER = logging.logger
verifier = VerifierBase()
fileutils = FileUtils()

class TestFiles(object):
    @params([
        { 'slack_uri': 'slack.com/api/files.list', 'file_count': 4, 'testname': 'files.list' },
    ])
    def test_files_list(self, remote_slack, connector_slack, slack_uri, file_count, testname):
        LOGGER.info("List files currently exisit on Slack.")
        restconn = connector_slack
        restconn.update_headers('accept', 'application/json')
        restconn.update_headers('content-type', 'application/json')
        params = {'token': remote_slack.test_token}
        resp, cont = restconn.make_request("GET", slack_uri, urlparam=params)


    @params([
        { 'slack_uri_list': 'slack.com/api/files.list', 'slack_uri_upload': 'slack.com/api/files.upload', 'filename': 'Uber.py', 'testname': 'upload Python file' },
    ])
    def test_files_upload(self, remote_slack, connector_slack, slack_uri_list, slack_uri_upload, filename, testname):
        LOGGER.info("Upload a file located at data/files directory.")
        # upload a lookup file via REST
        path_to_file = os.path.abspath(os.path.join(os.path.abspath(os.path.curdir), '..', '..', 'data', 'files', filename))
        content = fileutils.get_file_contents(path_to_file)
        restconn = connector_slack
        restconn.update_headers('accept', '*/*')
        restconn.update_headers('content-type', 'multipart/form-data; image/jpeg')
        urlparams = {'token': remote_slack.test_token, 'content': content, 'filename': filename}
        resp, cont = restconn.make_request("POST", slack_uri_upload, urlparam=urllib.urlencode(urlparams))
        verifier.verify_true(int(resp['status']) == 200)
        cont_dic = json.loads(cont)
        verifier.verify_true(cont_dic['ok'])
