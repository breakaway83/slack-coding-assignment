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
import mimetypes
from conftest import params

logging = Logging()
LOGGER = logging.logger
verifier = VerifierBase()
fileutils = FileUtils()
tries = 10
time_to_wait = 30

class TestFiles(object):
    @params([
        { 'slack_uri': 'slack.com/api/files.list', 'file_count': 4, 'testname': 'files.list' },
    ])
    def test_files_list(self, remote_slack, connector_slack, slack_uri, file_count, testname):
        LOGGER.info("List files currently exisit on Slack.")
        restconn = connector_slack
        restconn.update_headers('accept', '*/*')
        restconn.update_headers('content-type', 'application/json')
        params = {'token': remote_slack.test_token}
        resp, cont = restconn.make_request("GET", slack_uri, urlparam=params)


    @params([
        { 'slack_uri_list': 'slack.com/api/files.list', 'slack_uri_upload': 'slack.com/api/files.upload', 'filename': 'Uber.py', 'testname': 'upload Python file' },
        { 'slack_uri_list': 'slack.com/api/files.list', 'slack_uri_upload': 'slack.com/api/files.upload', 'filename': 'LeaseRental.pdf', 'testname': 'upload PDF file' },
        { 'slack_uri_list': 'slack.com/api/files.list', 'slack_uri_upload': 'slack.com/api/files.upload', 'filename': 'Image1.jpg', 'testname': 'upload image file' },
        { 'slack_uri_list': 'slack.com/api/files.list', 'slack_uri_upload': 'slack.com/api/files.upload', 'filename': 'SDE.DOCX', 'testname': 'upload Word file' },
        { 'slack_uri_list': 'slack.com/api/files.list', 'slack_uri_upload': 'slack.com/api/files.upload', 'filename': 'databricks.zip', 'testname': 'upload ZIP file' },
    ])
    def test_files_upload(self, remote_slack, connector_slack, slack_uri_list, slack_uri_upload, filename, testname):
        LOGGER.info("Upload a file located at data/files directory.")
        # upload a file in different format via REST
        path_to_file = os.path.abspath(os.path.join(os.path.abspath(os.path.curdir), '..', '..', 'data', 'files', filename))
        content = fileutils.get_file_contents(path_to_file)
        restconn = connector_slack

        fields = []
        files = [('file', filename, content)]
        content_type, body = self.encode_multipart_formdata(fields, files)
        restconn.update_headers('accept', '*/*')
        restconn.update_headers('content-type', '%s' % content_type)
        urlparams = {'token': remote_slack.test_token}
        resp, cont = restconn.make_request("POST", slack_uri_upload, body=body, urlparam=urlparams)
        verifier.verify_true(int(resp['status']) == 200)
        cont_dic = json.loads(cont)
        verifier.verify_true(cont_dic['ok'])
        # Verify that files.list shows the file
        # Due to the fact that sometime the posted files take sometime to show up in
        # the files.list result, consider using pooling
        for i in range(tries):
            try:
                resp, cont = restconn.make_request("GET", slack_uri_list, urlparam=urlparams)
                verifier.verify_true(filename in cont)
                break
            except AssertionError as e:
                if(i < tries - 1):
                    time.sleep(time_to_wait)
                else:
                    raise type(e)("filename %s does not exist in files.list result." % filename)

    @params([
        { 'slack_uri_list': 'slack.com/api/files.list', 'slack_uri_upload': 'slack.com/api/files.upload', \
                'content': 'Julie Bort (March 9, 2015). "Salesforce, Evernote, Slack, and other Apple Watch \
                business apps - Business Insider". Business Insider.', 'filename': 'content.txt', 'testname': 'upload content' },
    ])
    def test_files_upload_content(self, remote_slack, connector_slack, slack_uri_list, slack_uri_upload, content, filename, testname):
        LOGGER.info("Upload Content.")
        # upload a file defined in Content via REST
        restconn = connector_slack

        restconn.update_headers('accept', '*/*')
        restconn.update_headers('content-type', 'application/json')
        urlparams = {'token': remote_slack.test_token, 'content': content, 'filename': filename}
        resp, cont = restconn.make_request("POST", slack_uri_upload, urlparam=urlparams)
        verifier.verify_true(int(resp['status']) == 200)
        cont_dic = json.loads(cont)
        verifier.verify_true(cont_dic['ok'])
        # Verify that files.list shows the file
        for i in range(tries):
            try:
                resp, cont = restconn.make_request("GET", slack_uri_list, urlparam=urlparams)
                verifier.verify_true(filename in cont)
                break
            except AssertionError as e:
                if(i < tries - 1):
                    time.sleep(time_to_wait)
                else:
                    raise type(e)("filename %s does not exist in files.list result." % filename)

    @params([
        { 'slack_uri_list': 'slack.com/api/files.list', 'slack_uri_delete': 'slack.com/api/files.delete', 'filename': 'Uber.py', 'testname': 'delete Python file' },
        { 'slack_uri_list': 'slack.com/api/files.list', 'slack_uri_delete': 'slack.com/api/files.delete', 'filename': 'LeaseRental.pdf', 'testname': 'delete PDF file' },
        { 'slack_uri_list': 'slack.com/api/files.list', 'slack_uri_delete': 'slack.com/api/files.delete', 'filename': 'Image1.jpg', 'testname': 'delete image file' },
        { 'slack_uri_list': 'slack.com/api/files.list', 'slack_uri_delete': 'slack.com/api/files.delete', 'filename': 'SDE.DOCX', 'testname': 'delete Word file' },
        { 'slack_uri_list': 'slack.com/api/files.list', 'slack_uri_delete': 'slack.com/api/files.delete', 'filename': 'databricks.zip', 'testname': 'delete ZIP file' },
        { 'slack_uri_list': 'slack.com/api/files.list', 'slack_uri_delete': 'slack.com/api/files.delete', 'filename': 'content.txt', 'testname': 'delete file uploaded through Content' },
    ])
    def test_files_delete(self, remote_slack, connector_slack, slack_uri_list, slack_uri_delete, filename, testname):
        restconn = connector_slack
        urlparams = {'token': remote_slack.test_token}
        resp, cont = restconn.make_request("GET", slack_uri_list, urlparam=urlparams)
        cont_dic = json.loads(cont)
        files_list = cont_dic['files']
        for file in files_list:
            if(str(file['name']) == filename):
                urlparams = {'token': remote_slack.test_token, 'file': str(file['id'])}
                resp, cont = restconn.make_request("DELETE", slack_uri_delete, urlparam=urlparams)
                verifier.verify_true(int(resp['status']) == 200)
                cont_dic = json.loads(cont)
                verifier.verify_true(cont_dic['ok'])

    def encode_multipart_formdata(self, fields, files):
        """
        fields is a sequence of (name, value) elements for regular form fields.
        files is a sequence of (name, filename, value) elements for data to be uploaded as files
        Return (content_type, body) ready for httplib.HTTP instance
        """
        BOUNDARY = '----------bound@ry_$'
        CRLF = '\r\n'
        L = []
        for (key, value) in fields:
            L.append('--' + BOUNDARY)
            L.append('Content-Disposition: form-data; name="%s"' % key)
            L.append('')
            L.append(value)
        for (key, filename, value) in files:
            L.append('--' + BOUNDARY)
            L.append('Content-Disposition: form-data; name="%s"; filename="%s"' % (key, filename))
            L.append('Content-Type: %s' % self.get_content_type(filename))
            L.append('')
            L.append(value)
        L.append('--' + BOUNDARY + '--')
        L.append('')
        body = CRLF.join(L)
        content_type = 'multipart/form-data; boundary=%s' % BOUNDARY
        return content_type, body

    def get_content_type(self, filename):
        return mimetypes.guess_type(filename)[0] or 'application/octet-stream'
