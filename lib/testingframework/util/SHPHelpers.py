import json
import logging
from helmut.util.Constants import Constants as const
from helmut.connector.base import Connector
import urllib2
import urllib

LOGGER = logging.getLogger('SHPHelpers')

class SHPHelpers(object):

    def __init__(self):
        LOGGER.info("Performs SHP initialisation")
        self.shpool = [] # list of all splunk instances in the shp
        self.guid_lookup = dict() #guid to hostname mapping
        self.hostdetails = dict() # contains splunk vs mode infomration s1:slave, s2:master
        self.master_uri = None

    def addPeer(self,splunk,role, replication_port=9997):
        '''
        Adding a peer to search head cluster/pool
        @param param: splunk instance and role='mster/slave/adhoc'
        Adds every new peer to the shpool list
        Adds hostname:role mapping to hostdetails dictionary
        '''
        LOGGER.info("add a search head to the search head pool")
        self.configure_peer(splunk,role, replication_port)

        self.shpool.append(splunk)
        self.hostdetails[splunk.splunkd_host()] = role
        
#        self.create_guid_lookup(splunk)

    def configure_peer(self,splunk,mode, replication_port=9997,
                       request_type="POST"):
        '''
        @summary: Configures peer to either master/slave/adhoc
        @param param: splunk instance and mode='master/slave/adhoc'
        @return: None
        '''
        request_url = const.TestConstants['SHP_CONFIG_PEER']

        if(mode=='master'):
            LOGGER.info("Configuring splunk instance as a master")
            request_args = {'mode_master': 'True'}
            self.master_hostname = splunk.splunkd_host()
            self.master_uri = splunk.uri_base()
        elif(mode=='master , slave'):
            LOGGER.info("Configuring splunk instance as a Master and Slave")
            request_args = {'mode': 'master, slave',
                            'replication_port':replication_port}
            self.master_hostname = splunk.splunkd_host()
            self.master_uri = splunk.uri_base()

        else:
            if(mode == 'slave'):
                LOGGER.info("configuring splunk instance as a slave")
                request_args = {'mode': 'slave',
                                'master_uri': self.master_uri,
                                'replication_port':replication_port}


        response,content = self.make_http_request(splunk, request_type,
                                                  request_url, request_args)
    
    def create_guid_lookup(self):
        LOGGER.info("For the given splunk instance create an entry in guid lookup")
    
    def get_host_from_guid(self,splunk):
        LOGGER.info("Get the hostname from the guid.. use the shpool/master/peers")
        # Use peers endpoint of the master to convert guid to hostname
        
        return origin_peer

    def get_artifact_disk_size(self,splunk,artifact_id):
        LOGGER.info("Get the md5 checksum size of artifacts on all replicated peers")
        # the call to this should be like for each peer where this artifact resides invoke get_artifact_size
        # each artifact object will have origin_peer and replicated_peers.
        # Use the ssh connection for each peer to navigate to $SPLUNK_HOME/var/run/splunk/dispatch folder
        # Perform a check sum md5 on that folder
        return artifact_size
    
   
    def get_artifact_list(self,splunk):
        '''
        @summary: Gets the list of all the artifacts in a peer
        @param param: splunk instance
        @return: list of artifact objects
        '''
        LOGGER.info("getting the list of artifacts in a peer")
        role = self.get_Role(splunk)
        artifactlist = []
        request_url = const.TestConstants['SHP_ARTIFACT'].format(role)
        request_type = 'GET'
        request_args ={'output_mode':'json'}
        response,content = self.make_http_request(splunk, request_type,
                                                  request_url, request_args)
        parsedresponse = json.loads(content)
        
        for artfct in  parsedresponse['entry']: 
            for key, value in artfct['content']['peers'].iteritems():
                artifact = Artifact()   
                artifact_id, artifact_origin = self.get_artifact_id_origin(artfct['id'])
                
                artifact.id = artifact_id    
                artifact.origin_peer = artifact_origin  
                artifact.target_peer = key
                artifact.size = artfct['content']['artifact_size']
                artifact.status = value['status']                
                artifactlist.append(artifact)
            

        return artifactlist

    def get_artifact_id_origin(self,artifact_link):
        LOGGER.info("Get the artifact id from the artifact link")
        artifact_temp = artifact_link.split('artifacts/')
        artifact_array = artifact_temp[1].split('~')
        
        return artifact_array[0],artifact_array[1]
        

        
    def artifact_action(self,splunk,artifact_id,action="",peer=None):
        '''
        @summary: Delete an artifact on a peer
                : remove - delete an artifact from the peer
                : remove_all - delete all artifacts from the peer
                : remove_from_peer - remove an artifact from a particular peer
        @param param: splunk instance
        @return: None
        '''
        LOGGER.info("deleting  artifact")
        request_url = '/services/shpool/{0}/artifacts/{1}/{2}'.format(self.get_Role(splunk),artifact_id,action)
        request_type = 'POST'

        if (action == 'remove' | action == 'remove_from_peer'):
            request_type = 'DELETE'
            request_args = {'peer':peer}

        if (action == 'remove_all'):
            request_args = {}

        if (action == 'fix'):
            request_args = {}

        if (action == 'replicate'):
            request_args = {'peer':'','host_port_pair':'','replication_port':'',\
                            'replication_use_ssl':''}


        self.make_http_request(splunk, request_type, request_url, request_args)
    
    def peer_actions(self,splunk,action=""):
        '''
        @summary: performs actions on a peer
        @param: splunk instance, action = 'maintenance|decommission|restart|re-add-peer'
        @return: none
        '''
        role = self.get_Role(splunk)
        request_url = '/services/shpool/{0}/control/{1}'.format(role,action)
        request_type = 'POST'

        if(action=="maintenace"):
            request_args = {'mode':True}

        if(action=="decommission"):
            request_args = {'enforce_counts':''}

        if(action=="restart" or action=="re-add-peer"):
            request_args={}

        self.make_http_request(splunk, request_type, request_url, request_args)

    def get_Role(self,splunk):
        '''
        @summary: Checks if a given splunk instance is Master
        @param param: splunk instance
        @return: Boolean
        '''
        splunk_name = splunk.splunkd_host()
        return self.hostdetails[splunk_name]

    def get_replication(self,splunk):
        '''
        @summary: Gets the list of all the replication in a peer
        @param param: splunk instance
        @return: list of replication objects
        '''
        role = self.get_Role(splunk)
        replicationlist = []
        request_url = '/services/shpool/{0}/replications'.format(role)
        request_type = 'GET'
        request_args ={'output_mode':'json'}
        response,content = self.make_http_request(splunk, request_type,
                                                  request_url, request_args)
        parsedresponse = json.loads(content)
        for repl in  parsedresponse['entry']:
            replication = Replication()
            replication.artifact_id = repl['content']['artifact_id']
            replication.sourcePeer = repl['content']['source_peer']
            replication.targetPeer = repl['content']['target_peer']
            replicationlist.append(replication)

        return replicationlist

    
    def get_Config(self,splunk):
        '''
        '''
        role = self.get_Role(splunk)
        peerlist = []
        request_url = '/services/shpool/config/config'.format(role)
        request_args = {'output_mode':'json'}
        request_type = "GET"
        response,content = self.make_http_request(splunk, request_type,
                                                  request_url, request_args)
        
        parsedresponse = json.loads(content) 
        for aconfig in parsedresponse['entry']:
            config = Config()
            config.heartbeat_period=aconfig['content']['heartbeat_period']
            config.heartbeat_timeout=aconfig['content']['heartbeat_timeout']
            config.master_uri=aconfig['content']['master_uri']
            config.max_peer_rep_load=aconfig['content']['max_peer_rep_load']
            config.mode=aconfig['content']['mode']
            config.percent_peers_to_restart=aconfig['content']['percent_peers_to_restart']
            config.ping_flag=aconfig['content']['ping_flag']
            config.register_replication_address=aconfig['content']['register_replication_address']
            config.replication_factor=aconfig['content']['replication_factor']
            config.replication_port=aconfig['content']['replication_port']
            config.replication_use_ssl=aconfig['content']['replication_use_ssl']
            
        return config, response
            
    def get_Peers(self,splunk):
        '''
        @summary: Gets the list of all the peers in a master
        @param param: splunk instance
        @return: list of peer objects
        '''
        role = self.get_Role(splunk)
        peerlist = []
        request_url = '/services/shpool/{0}/peers'.format(role)
        request_type = 'GET'
        request_args = {'output_mode':'json'}
        response,content = self.make_http_request(splunk, request_type,
                                                  request_url, request_args)
        parsedresponse = json.loads(content)
        for apeer in  parsedresponse['entry']:
            peer = Peer()
            peer.peerName=apeer['content']['label']
            peer.peerId=apeer['id']
            peer.peerupdateTime=apeer['updated']
            peer.host_port_pair=apeer['content']['host_port_pair']
            peer.label=apeer['content']['label']
            peer.last_heartbeat=apeer['content']['last_heartbeat']
            peer.pending_job_count=apeer['content']['pending_job_count']
            peer.replication_count=apeer['content']['replication_count']
            peer.replication_port=apeer['content']['replication_port']
            peer.replication_use_ssl=apeer['content']['replication_use_ssl']
            peer.site=apeer['content']['site']
            peer.status=apeer['content']['status']
            peerlist.append(peer)

        return peerlist,response

    def get_job_details(self,splunk,jobid):
        LOGGER.info("Get the job details - scheduled node, replicated node, job run time, artifact size, jobId, job permission/scope, job owner")
        
    def get_repl_object(self,splunk):
        LOGGER.info("Get details of replicated object")
        
    def monitor_job_distribution(self,splunk):
        LOGGER.info("Get details  - no of jobs running on each peer, no of replicated jobs and other statistics needed to know how much the peer is loaded")
        LOGGER.info("TODO")
  
    def introspect_Conf_replication(self,splunk):
        LOGGER.info("Gets the details of conf replication like state, nodes replicated to")
        LOGGER.info("TODO")
           
    def trigger_Conf_replication(self,splunk):
        LOGGER.info("Trigger conf replication")   
        LOGGER.info("TODO")
    
    def setup_Indexer(self,searchhead,indexer):
        LOGGER.info("add a indexer as a search peer of a search head")
        
        request_url = const.TestConstants['ADD_DIST_PEER']
        searchpeername = indexer.splunkd_host()+":"+str(indexer.splunkd_port())
        request_args = {'name':searchpeername,'remotePassword':'changed','remoteUsername':'admin'}
        request_type = 'POST'
        
        self.shpool.append(indexer)
        self.hostdetails[indexer.splunkd_host()] = 'indexer'
        
        response,content = self.make_http_request(searchhead, request_type,
                                                  request_url, request_args)
    
    def make_http_request(self,splunk,request_type,request_url,request_args,
                          splunk_user='admin', splunk_pwd='changed'):
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

                


class Artifact(object):
    """
    @summary: Definition of an artifact object

    """

    @property
    def id(self):
        return self._id

    @property
    def origin_peer(self):
        return self._origin_peer
    
    @property
    def target_peer(self):
        return self._target_peer   

    @property
    def artifact_size(self):
        return self._artifact_size
    
    @property
    def repl_status(self):
        return self._repl_status       
        
    @id.setter
    def id(self,value):
        self._id= value
        
    @origin_peer.setter
    def origin_peer(self,value):
        self._origin_peer= value        

    @target_peer.setter
    def target_peer(self,value):
        self._target_peer= value          
                                
    @artifact_size.setter
    def artifact_size(self,value):
        self._artifact_size= value   
                                        
    @target_peer.setter
    def repl_status(self,value):
        self._repl_status= value 
    
class Replication(object):
    """
    @summary: defintion of a replication object
    """

    @property
    def artifact_id(self):
        return self._artifact_id

    @property
    def sourcePeer(self):
        return self._sourcePeer

    @property
    def targetPeer(self):
        return self._targetPeer


    @artifact_id.setter
    def artifact_id(self,value):
        self._artifact_id= value


    @sourcePeer.setter
    def sourcePeer(self,value):
        self._sourcePeer = value

    @targetPeer.setter
    def targetPeer(self,value):
        self._targetPeer = value



class Peer(object):
    """
    @summary: definition of a peer object
    """

    @property
    def peerName(self):
        return self._peerName

    @property
    def peerId(self):
        return self._peerId

    @property
    def peerupdateTime(self):
        return self._peerupdateTime

    @property
    def host_port_pair(self):
        return self._host_port_pair

    @property
    def label(self):
        return self._label

    @property
    def last_heartbeat(self):
        return self._last_heartbeat

    @property
    def pending_job_count(self):
        return self._pending_job_count

    @property
    def replication_count(self):
        return self._replication_count

    @property
    def replication_port(self):
        return self._replication_port
    @property
    def replication_use_ssl(self):
        return self._replication_use_ssl

    @property
    def site(self):
        return self._replication_use_ssl

    @property
    def status(self):
        return self._status

    @peerName.setter
    def peerName(self,value):
        self._peerName = value

    @peerId.setter
    def peerId(self,value):
        self._peerId = value

    @peerupdateTime.setter
    def peerupdateTime(self,value):
        self._peerupdateTime = value

    @host_port_pair.setter
    def host_port_pair(self,value):
        self._host_port_pair = value

    @label.setter
    def label(self,value):
        self._label = value

    @last_heartbeat.setter
    def last_heartbeat(self,value):
        self._last_heartbeat = value

    @pending_job_count.setter
    def pending_job_count(self,value):
        self._pending_job_count = value

    @replication_count.setter
    def replication_count(self,value):
        self._replication_count = value

    @replication_port.setter
    def replication_port(self,value):
        self._replication_port = value

    @replication_use_ssl.setter
    def replication_use_ssl(self,value):
        self._replication_use_ssl = value

    @site.setter
    def site(self,value):
        self._site = value

    @status.setter
    def status(self,value):
        self._status = value


class Config(object):

    @property
    def heartbeat_period(self):
        return self._heartbeat_period

    @property
    def heartbeat_timeout(self):
        return self._heartbeat_timeout

    @property
    def master_uri(self):
        return self._master_uri

    @property
    def max_peer_rep_load(self):
        return self._max_peer_rep_load

    @property
    def mode(self):
        return self._mode

    @property
    def percent_peers_to_restart(self):
        return self._heartbeat_timeout

    @property
    def ping_flag(self):
        return self._ping_flag
    
    @property
    def register_replication_address(self):
        return self._register_replication_address
    
    @property
    def replication_factor(self):
        return self._replication_factor        

    @property
    def replication_port(self):
        return self._replication_port
    
    @property
    def replication_use_ssl(self):
        return self._replication_use_ssl
    

    @heartbeat_period.setter
    def heartbeat_period(self,value):
        self._heartbeat_period = value

    @heartbeat_timeout.setter
    def heartbeat_timeout(self,value):
        self._heartbeat_timeout = value

    @master_uri.setter
    def master_uri(self,value):
        self._master_uri = value

    @max_peer_rep_load.setter
    def max_peer_rep_load(self,value):
        self._max_peer_rep_load = value

    @mode.setter
    def mode(self,value):
        self._mode = value

    @percent_peers_to_restart.setter
    def percent_peers_to_restart(self,value):
        self._heartbeat_timeout = value

    @ping_flag.setter
    def ping_flag(self,value):
        self._ping_flag = value
    
    @register_replication_address.setter
    def register_replication_address(self,value):
        self._register_replication_address = value
    
    @replication_factor.setter
    def replication_factor(self,value):
        self._replication_factor = value      

    @replication_port.setter
    def replication_port(self,value):
        self._replication_port = value
    
    @replication_use_ssl.setter
    def replication_use_ssl(self,value):
        self._replication_use_ssl = value  
        
      
class ReplicatedObject(object):
        LOGGER.info("define a knowledge object class to cover lookups, sourcetype_rename, IFX, tags, alias, SS, alerts")
        LOGGER.info("Get details of the node on which it was created, replicated nodes and so on")
