from testingframework.connector.base import Connector
from testingframework.log import Logging
from testingframework.util.fileutils import FileUtils
from slacktest.util.VerifierBase import VerifierBase
from slacktest.util.multipart_formdata import encode_multipart_formdata
import pytest
import time
import os
import re
import json
import urllib
import mimetypes
import string
import random
from conftest import params

logging = Logging("TestFiles")
LOGGER = logging.logger
verifier = VerifierBase()
fileutils = FileUtils()
tries = 10
time_to_wait = 10

class TestFiles(object):
    @params([
        { 'slack_uri_list': 'slack.com/api/files.list', 
            'slack_uri_upload': 'slack.com/api/files.upload', 
            'filename': 'slack_api_test.png', 'testname': 'upload PNG file' },
    ])
    def test_files_upload(self, remote_slack, connector_slack, slack_uri_list, slack_uri_upload, filename, testname):
        '''
        This is to test both files.upload and files.list of a PNG file
        '''
        LOGGER.info("Upload a PNG file located at data/files directory.")
        # upload a file in different format via REST
        path_to_file = os.path.abspath(os.path.join(os.path.abspath(os.path.curdir), '..', '..', 'data', 'files', filename))
        content = fileutils.get_file_contents(path_to_file)
        restconn = connector_slack
        # This is to get the correct content type as well as the HTTP body for multipart formdata
        fields = []
        files = [('file', filename, content)]
        content_type, body = encode_multipart_formdata(fields, files)
        restconn.update_headers('accept', '*/*')
        restconn.update_headers('content-type', '%s' % content_type)
        # This is to add the test token to access Slack APIs
        urlparams = {'token': remote_slack.test_token}
        # This is to actually issue the HTTP request to Slack's APIs
        resp, cont = restconn.make_request("POST", slack_uri_upload, body=body, urlparam=urlparams)
        verifier.verify_true(int(resp['status']) == 200)
        cont_dic = json.loads(cont)
        verifier.verify_true(cont_dic['ok'])
        # Verify that files.list lists the file
        # According to my observation, sometime the posted files take sometime to show up in
        # the files.list result, consider using pooling
        # List only by type:images when calling the endpoint
        urlparams.update({'types':'images'})
        for i in range(tries):
            try:
                resp, cont = restconn.make_request("GET", slack_uri_list, urlparam=urlparams)
                cont_dict = json.loads(cont)
                thumbs_dic = cont_dic['file']
                for j in thumbs_dic.keys():
                    # Matching thumbnail URLs
                    # thumbnail URLs appear to be the filename in lowercase
                    if(re.match('thumb_[\d]+$', str(j))):
                        verifier.verify_true(filename.lower().split('.')[0] in str(thumbs_dic[j]))
                break
            except AssertionError as e:
                if(i < tries - 1):
                    time.sleep(time_to_wait)
                else:
                    raise type(e)("filename %s does not exist in files.list result." % filename)
            except SSLError as e:
                if(i < tries - 1):
                    time.sleep(time_to_wait)
                else:
                    raise type(e)("Internet connection is still not there.")

    @params([
        { 'slack_uri_list': 'slack.com/api/files.list', 
            'slack_uri_upload': 'slack.com/api/files.upload',
            'content': 'Julie Bort (March 9, 2015). "Salesforce, Evernote, Slack, and other Apple Watch business apps - Business Insider". Business Insider.', 
            'filename': 'content.txt', 
            'testname': 'upload content' },
    ])
    def test_files_upload_content(self, remote_slack, connector_slack, slack_uri_list, slack_uri_upload, content, filename, testname):
        '''
        This is to test upload through Content field, not File field
        '''
        LOGGER.info("Upload Content.")
        # upload a file defined in Content via REST
        restconn = connector_slack
        # Update HTTP request headers
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
        { 'slack_uri_list': 'slack.com/api/files.list', 
            'slack_uri_delete': 'slack.com/api/files.delete', 
            'filename': 'slack_api_test.png', 
            'testname': 'delete PNG file' },
        { 'slack_uri_list': 'slack.com/api/files.list', 
            'slack_uri_delete': 'slack.com/api/files.delete', 
            'filename': 'content.txt', 
            'testname': 'delete file uploaded through Content' },
        { 'slack_uri_list': 'slack.com/api/files.list', 
            'slack_uri_delete': 'slack.com/api/files.delete', 
            'filename': 'nonexistence.txt', 
            'testname': 'delete nonexistent file' },
    ])
    def test_files_delete(self, remote_slack, connector_slack, slack_uri_list, slack_uri_delete, filename, testname):
        '''
        This is to test files.delete API, and both the PNG file and file uploaded through
        Content field are deleted.
        '''
        restconn = connector_slack
        urlparams = {'token': remote_slack.test_token}
        resp, cont = restconn.make_request("GET", slack_uri_list, urlparam=urlparams)
        cont_dic = json.loads(cont)
        files_list = cont_dic['files']
        found = False
        for file in files_list:
            if(str(file['name']) == filename):
                urlparams = {'token': remote_slack.test_token, 'file': str(file['id'])}
                for i in range(tries):
                    try:
                        resp, cont = restconn.make_request("DELETE", slack_uri_delete, urlparam=urlparams)
                        verifier.verify_true(int(resp['status']) == 200)
                        cont_dic = json.loads(cont)
                        verifier.verify_true(cont_dic['ok'])
                        break
                    except SSLError as e:
                        if(i < tries - 1):
                            time.sleep(time_to_wait)
                        else:
                            raise type(e)("Internet connection is still broken.")
                # This is the normal path where the file to be deleted exists
                for i in range(tries):
                    try:
                        resp, cont = restconn.make_request("GET", slack_uri_list, urlparam=urlparams)
                        verifier.verify_false(filename in cont)
                    except SSLError as e:
                        if(i < tries - 1):
                            time.sleep(time_to_wait)
                        else:
                            raise type(e)("Internet connection is still broken.")
                found = True
                break

        if(not found):
            # Handle the non-existent file
            # Generate a alphanumeric string with length of 10
            thumb_id = ''.join(random.sample((string.ascii_uppercase+string.digits),10))
            urlparams = {'token': remote_slack.test_token, 'file': thumb_id}
            for i in range(tries):
                try:
                    resp, cont = restconn.make_request("DELETE", slack_uri_delete, urlparam=urlparams)
                    cont_dic = json.loads(cont)
                    verifier.verify_true(str(cont_dic['error']) == "file_not_found")
                    break
                except SSLError as e:
                    if(i < tries - 1):
                        time.sleep(time_to_wait)
                    else:
                        raise type(e)("Internet connection is still broken.")
