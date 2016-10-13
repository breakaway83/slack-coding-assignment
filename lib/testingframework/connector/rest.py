'''
@author: Weimin Ma
'''

from .base import Connector
import urllib
import httplib2
import ssl
import json
import xml.etree.ElementTree as et
from xml.dom.minidom import parseString


class RESTConnector(Connector):
    """
    This represents to access REST thru HTTP client library httplib2

    Associated with each object is a C{http} object from the httplib which in
    turn contains connection info and auth.

    When a connector is logged in a sessionkey is generated and will be kept
    until the point that you logout or the server is restarted.

    When slack is restarted or upgraded the connector {tries} to login again

    @ivar _service: The underlying service, aka the http request object
    @cvar HEADERS: The default headers to pass with http request. this will
    get appended with the 'Authorization' key when sessionkey is used

    """
    HEADERS = {'content-type': 'text/xml; charset=utf-8'}
    METHODS = ['GET', 'POST', 'PUT', 'DELETE']
    SUCCESS = {'GET': '200', 'POST': '201', 'DELETE': '200', 'PUT': '200'}


    def __init__(self, slack, test_token=None):
        """
         Creates a new REST connector.
         The connector will logged in when created with default values

         @param slack: The slack deployment
         @type slack: L{testingframework.slack.Slack}
         @param test_token: The test_token to use. If None (default)
                          L{Connector.DEFAULT_TEST_TOKEN} is used.
         @type test_token: str

        """
        if test_token is None:
            test_token = ''
        super(RESTConnector, self).__init__(slack, test_token)
        self.uri_base = slack.uri_base()
        self._test_token = test_token
        self._timeout = 60
        self._debug_level = 0
        self._disable_ssl_certificate = True
        self._follow_redirects = False
        httplib2.debuglevel = self._debug_level
        self._service = httplib2.Http(timeout=self._timeout,
                                      disable_ssl_certificate_validation=
                                      self._disable_ssl_certificate)
        self._service.follow_redirects = self._follow_redirects
        #self._service.add_credentials(self._test_token)
        slack.register_start_listener(self)

    def make_request(self, method, uri, body=None, urlparam=None,
                     use_sessionkey=False):
        """
        Make a HTTP request to an endpoint

        @type  method: string
        @param method: HTTP valid methods: PUT, GET, POST, DELETE
        @type  uri: string
        @param uri: URI of the REST endpoint
        @type  body: string or dictionary or a sequence of two-element tuples
        @param body: the request body
        @type  urlparam: string/ dictionary or a sequence of two-element tuples
        @param urlparam: the URL parameters
        @type  use_sessionkey: bool
        @param use_sessionkey: toggle for using sessionkey or not

        >>> conn.make_request('POST', '/services/receivers/simple',
        urlparam={'host': 'foo'}, body="my event")

        """
        if body is None:
            body = ''
        if type(body) != str:
            body = urllib.urlencode(body)
        if urlparam is None:
            urlparam = ''
        if type(urlparam) != str:
            urlparam = urllib.urlencode(urlparam)
        if urlparam != '':
            url = "%s%s?%s" % (self.uri_base, uri, urlparam)
        else:
            url = "%s%s" % (self.uri_base, uri)

        if use_sessionkey:
            self._service.clear_credentials()
            self.update_headers('Authorization',
                                'Sumo %s' % self.sessionkey)
        else:
            if not self._service.credentials:
                self._service.add_credentials(self._username, self._password)
            if 'Authorization' in self.HEADERS:
                self.HEADERS.pop('Authorization')
        response, content = self._service.request(
            url, method, body=body, headers=self.HEADERS)

        self.logger.info("Request  => {r}".format(r={
            'method': method,
            'url': url,
            'body': body,
            #'auth': '{u}:{p}'.format(u=self._username, p=self._password),
            'header': self.HEADERS
            }))
        self.logger.info("Response => {r}".format(r=response))
        self.logger.debug("Content  => {c}".format(c=content))

        return response, content

    def parse_content_json(self, content):
        """
        Parses the content object (in json format) to python dict

        @type content: json
        @param content: content object from http request in json format
        """

        return json.loads(str(content))

    def update_headers(self, key=None, value=None):
        """
        Appends a key,value pair to the HEADERS

        @type key: str
        @param key: key to append to  HEADERS
        @type value: str
        @param value: value for that key to append to  HEADERS

        """
        if key in self.HEADERS:
            self.HEADERS.pop(key)
        self.HEADERS.update({key: value})

    def debug_level(self, value):
        """
        Overrides default value for debug_level  for httplib service

        @type value: int
        @param value: debugging level

        """

        self._debug_level = value

    def timeout(self, value):
        """
        Overrides default value for timout for http request

        @type value: int
        @param value: timeout for the http request in seconds

        """

        self._timeout = value

    def disable_ssl_certificate(self, value):
        """
        Overrides disable sssl certificate condition

        @type value: bool
        @param value: enable/disable ssl certificate for auth

        """

        self._disable_ssl_certificate = value

    def follow_redirects(self, value):
        """
        Overrides default value of the follow_redircets

        @type value: bool
        @param value: follow redirects

        """

        self._follow_redirects = value

    def __del__(self):
        """
        Called when the object is being deallocated.

        It unregisters itself with the Sumo start listeners.

        """
        self.slack.unregister_start_listener(self)

    def __call__(self):
        """
        Called when the Sumo deployment class notifies REST connector listener

        Need it as local deployment notify method invokes l() and then
        service will be recreated and initialized with default values
        """
        self._recreate_service()

    def parse_content_xml(self, content, tag):
        """
        Parses the content object (in xml format)

        @type content: xml
        @param content: content object from http request in xml format

        """
        dom = parseString(content)
        xmlTag = dom.getElementsByTagName(tag)[0].toxml()
        return xmlTag
