import imaplib
import logging
import email
import urllib
from mailbox import mbox
import re
import os
from helmut.util.Constants import Constants as const
from helmut.connector.base import Connector
from helmut.util import rip


LOGGER = logging.getLogger('search helper log')
class SearchHelpers(object):

    searchheads = []
    searchpeers = []
    
    def setup_dist_searchhead(self,searchhead):
        LOGGER.info("setting up search head")
        searchheads.add(searchhead)   
        
        LOGGER.info("check if there are search peers existing already. If so link them to the new search head")   
        if(len(searchpeers) > 0):
            self.setup_dist_search()
        #Can be a searchhead even if there is no search peer
        #Add to the list of search heads
        #If there are searchpeers already link them to the new search head
        
    def setup_dist_searchpeer(self,searchpeer):
        LOGGER.info("setting up search peer")
        if(len(searchhead) > 0):
            searchpeers.add(searchpeer)
            self.setup_dist_search()
        else:
            searchheads.add(searchpeer)
        #Check if there is atleast one search head
        # If there is then add it to the search peer list
        # If not add it to the search head list

    def get_searchheads(self):
        return searchheads
    
    def get_searchpeers(self):
        return searchpeers
    
    def update_conf_files(self,splunk,conffile,stanza,variable,value):
        stanza = nightlysplunk.confs()[conffile][stanza]
        stanza[variable] = value
        splunk.restart()

    def check_geobin(self, nightlysplunk, statsfunc, geobin):
        query = 'search index=geo checkin.geolong>=%s checkin.geolong<%s checkin.geolat>=%s checkin.geolat<%s | stats %s' % (geobin['_geo_bounds_west'], geobin['_geo_bounds_east'], geobin['_geo_bounds_south'], geobin['_geo_bounds_north'], statsfunc)
        job = nightlysplunk.jobs().create(query)
        job.wait()
        result = job.get_results()[0]
        for key in result:
            self.logger.info(result)
            assert result[key] == geobin[key]
            
    def has_bloomfilter(self, indexName, dbType, wait=30, tries=10):
        """
        Checks if the bloomfilter file is existed in the bucket
        @param wait: poll wait time in seconds, defaults to 30 seconds
        @param tries: max number of times to poll, defaults to 10
        """
        start = time.time()
        bloom_file = None
        for item in os.listdir(os.path.join(_SPLUNK_DB, indexName, dbType)):
            if os.path.isdir(os.path.join(_SPLUNK_DB, indexName, dbType, item)) and re.search("^db_\d+_\d+_\d+", item):
                bloom_file = os.path.join(_SPLUNK_DB, indexName, dbType, item, 'bloomfilter')
                for x in range(tries):
                    if os.path.exists(bloom_file):
                        self.logger.info("Find bloomfilter file in %s seconds." % (time.time()-start))
                        return True
                    sleep(wait)
                    self.logger.debug("Still waiting for the bloomfilter presents")
                self.logger.error("Bloomfilter file detection failed due to timeout in %s seconds" % (time.time()-start))
                return False
            else:
                self.logger.debug("The bucket is not found yet")
        self.logger.error("Why's there not any bucket in the db? Please investigate this error!")
        return False
    
    def remove_bloomfilter(self, indexName, dbType):
        """
        Delete the existing bloomfilter file in the bucket
        """
        try:
            for item in os.listdir(os.path.join(_SPLUNK_DB, indexName, dbType)):
                if os.path.isdir(os.path.join(_SPLUNK_DB, indexName, dbType, item)) and re.search("^db_\d+_\d+_\d+", item):
                    os.remove(os.path.join(_SPLUNK_DB, indexName, dbType, item, 'bloomfilter'))
                    return
            self.fail("Why's there not any bucket in the db? Please investigate this error!")
        except Exception:
            raise
    
    def setup_dist_search(self):
        LOGGER.info("setup distributed search")
        for searchead in searchheads:
            for searchpeer in searchpeers:
                ds_url = const.TestConstants['ADD_DIST_PEER'].format(fieldname)
                searchpeername = searchpeer.splunkd_host()+":"+searchpeer.splunkd_port()
                ds_args = {'name':searchpeername,'remotePassword':'admin','remoteUsername':'changed'}
                request_type = 'POST'
                response,content = self.make_http_request(searchhead,request_type,ds_url,ds_args) 
    
    def edit_tag(self,splunk,fieldname,fieldvalue, tagname,tag_action):
        """
        creates/edits/deletes a tag
        REST EDNPOINT - search/fields/{field_name}/tags
        """
        tag_url = const.TestConstants['ADD_TAG'].format(fieldname)
        tag_args = {'value': fieldvalue,tag_action:tagname}
        request_type = 'POST'
        response,content = self.make_http_request(splunk,request_type,tag_url,tag_args)            
   
    
    def edit_eventtype(self,splunk,eventtypename,search):
        '''
        '''
        LOGGER.info("create new eventtype")
        eventyype_url = const.TestConstants['EDIT_EVENTTYPE']
        eventtype_args = {'name':eventtypename, 'search':search}
        urllib.urlencode(eventtype_args)
        request_type = 'POST'
        response,content = self.make_http_request(splunk,request_type,eventyype_url,eventtype_args) 
    
    def edit_field_transform(self,splunk,fieldExtractionName,stanza,extractiontype,fieldtobeExtracted):
        '''
        '''
        LOGGER.info("create field transform using interactive field extractor")
        ifx_url = const.TestConstants['EDIT_IFX']
        ifx_args = {'name':fieldExtractionName,'stanza':stanza,'type':extractiontype,'value':fieldtobeExtracted}
        request_type = 'POST'
        response,content = self.make_http_request(splunk,request_type,ifx_url,ifx_args)
        

    def edit_sourcetype_rename(self,splunk,oldsourcetypename, newsourcetypename):
        '''
        '''
        LOGGER.info("Perform source type rename")
        source_url = const.TestConstants['SOURCE_TYPE_RENAME']
        source_args = {'name':oldsourcetypename,'value':newsourcetypename}
        request_type = 'POST'
        response,content = self.make_http_request(splunk,request_type,source_url,source_args) 
               
        
    def make_http_request(self,splunk,request_type,request_url,request_args,
                          splunk_user='admin', splunk_pwd='changeme'):
        """
        This is a REST helper that will generate a http request
        using request_type - GET/POST/...
        request_url and request_args
        """
        restconn = splunk.create_logged_in_connector(contype=Connector.REST,
                                                     username=splunk_user,
                                                     password=splunk_pwd)
        try:
            response, content = restconn.make_request(request_type,
                                                      request_url,
                                                      request_args)
            return response,content

        except urllib2.HTTPError, err:
            print "Http error code is ({0}): {1} : {2}".format(err.code,
                                                                   e.errno,
                                                                   e.strerror)
    