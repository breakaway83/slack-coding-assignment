'''
@author: Weimin Ma
'''

from .base import Connector
from .rest import RESTConnector
import urllib
import httplib2
import ssl
import json
import pytest
import xml.etree.ElementTree as et
from xml.dom.minidom import parseString


class ServiceConnector(RESTConnector):


    def __init__(self, sumo, username=None, password=None):

        super(ServiceConnector, self).__init__(sumo, username, password)
        self.update_headers(key='Accept', value='application/json, text/javascript')
        self.update_headers(key='Content-Type', value='application/json')

    def service_login(self):
        '''
        Seems every API access needs apiSession and cookie, which starts with login
        '''
        pass
        
