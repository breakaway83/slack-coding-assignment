#!usr/bin/env python
'''
The tools for Framework tests.
@author: tlee
@created: 2012/06/01
'''

import os
import helmut.manager.confs
import logging
import random
import socket
import splunk
import pytest
import subprocess
import tarfile
import inspect
import time
import sys
import shutil
from helmut.manager.jobs import Jobs
from helmut.splunk.ssh import SSHSplunk
from helmut.ssh.connection import SSHConnection
from helmut.connector import SDKConnector
from helmut import splunk_platform
from time import gmtime, strftime
from helmut.splunk_package.nightly import NightlyPackage
from splunk.models.clustering import (ClusterMasterBucket,
                                      ClusterMasterPeer,
                                      ClusterMasterSite,
                                      ClusterConfig,
                                      ClusterMasterGeneration,
                                      ClusterSearchheadGeneration,
                                      ClusterSlaveBucket, 
                                      ClusterMasterPeer, 
                                      ClusterMasterInfo)
from splunk.models.server_config import SplunkdConfig
from splunk.models.inputs import SplunkTCPInput
from splunktest.util.utilities import PortUtil
from helmut.splunk_factory.splunkfactory import SplunkFactory
from helmut.ssh.utils import SSHHostUtils

PORTUTIL = PortUtil()
LOGGER = logging.getLogger()
CONFIG = pytest.config


class ClusteringTest(object):
    '''A base class for tests against the clustering feature'''
    
    

    def setup_class(cls):
        '''Show when test class begins in helmut.log'''
        LOGGER.info("*** Setup class ***")
        cls.host_index = 0
    setup_class = classmethod(setup_class)

    def setup_method(self, method):
        '''Log test name'''
        LOGGER.info('*** Executing {name} ***'.format(name=method.__name__))
	self._doCleanCluster=False #flag to control cleaning of cluster b/w tests 
        self._start_during_teardown_method=True #flag to control starting of down instances during method level teardown
 
    def teardown_method(self, method): 
        '''Log method teardown'''
        LOGGER.info("*** Teardown method {name} ***"
                    .format(name=method.__name__))
        if(self._doCleanCluster==True):
            LOGGER.info('_doCleanCluster is True, so Cleaning the cluster.')
            if hasattr(self, 'cluster'):
                self.cluster.clean_cluster()
        else:
            # if one test fails in some state where few peers or master is down... next test should just see the down peers as up and running
            if hasattr(self, 'cluster'):
                if  self._start_during_teardown_method:
                    self.cluster.start_cluster_nodes_which_are_down()

    def teardown_class(cls):
        '''Log class teardown'''
        LOGGER.info("*** Teardown class ***")
        cls.host_index = 0

    teardown_class = classmethod(teardown_class)

    @property
    def doCleanCluster(self):
	'''This boolean property will dictate whether teardown_method should or should not call clean_cluster during the end of the test'''
	return self._doCleanCluster

    def new_cluster(self,
                    masters=1,
                    slaves=3,
                    search_heads=1,
                    hosts=None,
                    replication_factor=3,
                    search_factor=2,
                    multisite=False,
                    sites=1,
                    #site_replication_factor='origin:2,total:3',
                    #site_search_factor='origin:2,total:3'):
                    site_replication_factor='',
                    site_search_factor=''):
        '''
        Creates a cluster with 1 master, rep factor # of peers,
        and 1 search head in 1 site
        '''

        LOGGER.debug('Available hosts: {}'.format(hosts))
        self.cluster = Cluster(masters, slaves, search_heads, hosts, replication_factor, search_factor, multisite, sites)
        return self.cluster

    def get_diags(self, method):
        '''
        Calls 'splunk diag' on each splunk instance and copies or scp's
        the daig back to the build directory. The diags are then put into
        a tarball named after the test's docstring

        @param method: The test method passed from teardown_method.
        '''

        target = os.getcwd()
        test_name = method.__name__

        timestr = strftime("%Y-%m-%d-%H.%M.%S", gmtime())
        diag_tar_file_name = ('{test_name}_diags_{ts}.tar'
                              .format(test_name=test_name, ts=timestr))
        tarfile.open(diag_tar_file_name, mode='a')
        diag_tar_file = tarfile.open(diag_tar_file_name, mode='w')
        for instance in self.cluster.instances:
            output_tuple = instance.execute_without_common_flags('diag')
            output_string = output_tuple[1]
            LOGGER.info('diag output: {op}'.format(op=output_string))
            tokens = output_string.split('Splunk diagnosis file created: ')
            file_string = tokens[1]
            path = file_string.strip()
            LOGGER.info('Path to diag: {path}'.format(path=path))
            if (instance.host_name == self.cluster.local_ip
                    or instance.host_name in socket.gethostname()):
                try:
                    subprocess.call(['mv', path, target])
                except Exception('Cannot find file'):
                    LOGGER.error('Cannot find file {daig}'.format(daig=path))
            else:
                args = ['scp']
                args.append('{user}@{host}:{path}'
                            .format(user=CONFIG.ssh_user,
                            host=instance.host_name,
                            path=path))
                args.append(target)
                try:
                    subprocess.call(args)
                except Exception('Cannot call subprocess'):
                    LOGGER.error('Cannot scp from host {host}'
                                 .format(host=instance.host_name))
        for file_name in os.listdir(os.getcwd()):
            if 'diag-' in file_name:
                diag_tar_file.add(file_name)
                try:
                    subprocess.call(['rm', file_name])
                except Exception('Cannot rm file'):
                    LOGGER.error('Cannot remove file {fn}'
                                 .format(fn=file_name))
        diag_tar_file.close()

    def is_done_indexing_by_activity(self, splunk_instance, search_string='*', index='main', secondsToStable=60, retry_interval=30):
        resultPrev = -1
        resultSameSince = sys.maxint
        counts = []
        while True:
            time.sleep(retry_interval)
            result = self.get_event_count(splunk_instance=splunk_instance,search_string=search_string, index=index) 
            now = int(time.time()) # time()'s precision will suffice here, and in fact seconds is all we want
            if result == resultPrev:
                if (now - resultSameSince) > secondsToStable: ### we have stable state
                    LOGGER.info('Achieved stable state for index %s with totalEventCount=%s' % (index, result))
                    return (result, resultSameSince) # result <= expectedResult; stable.
                if resultSameSince == sys.maxint:             ### our first time in what could become stable state
                    LOGGER.debug('Possibly entering stable state for index %s at totalEventCount=%s' % (index, result))
                    resultSameSince = lastPolledAt
                    LOGGER.debug('Using resultSameSince=%d for index %s' % (resultSameSince, index))
                else:                                         ### our 2nd/3rd/... time in what could become stable state
                    LOGGER.debug('Confirming putative stable at totalEventCount=%s with index %s' % (result, index))
            else:                                             ### we do NOT have stable state
                LOGGER.debug('Flux at totalEventCount=%s for index %s; delta +%s' % (result, index, (result-resultPrev)))
                resultPrev = result
                resultSameSince = sys.maxint
            lastPolledAt = now

    def get_event_count(self,
                        splunk_instance,
                        search_string='*',
                        index='main',
                        expected_events=None,
                        timeout=300):
        '''
        Waits until indexing is complete to return a number

        @param splunk_instance: The splunk instance to perform the search on.
        @param timeout: the amount of time to wait for the event count.
        '''
        LOGGER.info('Getting event count')
        #if expected_events:
        #    (splunk_instance.indexes()['main']
        #     .wait_for_event_count(ecount=expected_events, timeout=timeout))
        event_count = 0
        jobs = Jobs(splunk_instance.default_connector)
        #while True:
        job = jobs.create('search %s' % search_string)
        job.wait()
        event_count = job.get_event_count()
            ## SPL-63671 - temp workaround bc job.get_event_count() no longer returns the correct # in Bubbles
            #event_count = int(splunk_instance.execute(\
            #    'search "%s | stats count" -auth admin:notchangeme' % search_string)[1].split('\n')[2])
            #if timeout <= 0 or event_count == expected_events:
            #    break
            #time.sleep(10)
            #timeout -= 10
        #event_count = splunk_instance.indexes()['main'].get_total_event_count()
        LOGGER.debug('Event count: {ec}'.format(ec=event_count))
        return event_count

    def get_sh_generation_id(self, splunk_instance):
        '''
        See http://docs.splunk.com/Splexicon:GenerationID
        @rtype: int
        '''
        splunk_instance.set_splunk_models()
        generation_id = -1
        gen_id_list = ClusterSearchheadGeneration.all()
        assert(len(gen_id_list) == 1)
        generation_id = gen_id_list[0].generation_id
        if gen_id_list[0].was_forced == True:
            LOGGER.info('generation_id = %s, was_forced = %d' % (generation_id, was_forced))
        return generation_id

    def get_last_complete_generation_id(self):
        '''
        See http://docs.splunk.com/Splexicon:GenerationID
        @rtype: int
        '''
        self.cluster.master.set_splunk_models()
        generation_id = -1
        gen_id_list = ClusterMasterGeneration.all()
        assert(len(gen_id_list) == 1)
        return gen_id_list[0].last_complete_generation_id


#Only call this class through ClusteringTests's new_cluster
class Cluster(object):
    '''
    A container for cluster nodes.
    '''
    
    def __init__(self,
                 masters=1,
                 slaves=3,
                 search_heads=1,
                 hosts=None,
                 replication_factor=3,
                 search_factor=2,
                 multisite=False,
                 sites=1,
                 #site_replication_factor='origin:2,total:3',
                 #site_search_factor='origin:2,total:3'):
                 site_replication_factor='',
                 site_search_factor=''):
        '''
        Deploy a cluster with the specified number of each type of node
        '''
        if hosts is None:
            LOGGER.info('Hosts was None. Will be setting up cluster locally')

        LOGGER.info('''Deploying a cluster with: {masters} masters
            {peers} peers
            {sh} searchheads'''
                    .format(masters=masters, peers=slaves, sh=search_heads))
        self._config = CONFIG
        self._instances = []
        self._hosts = hosts
        if not hasattr(ClusteringTest, 'host_index'):
            LOGGER.info('initializing host_index in Cluster class')
            ClusteringTest.host_index=0            
        self._current_host_index = ClusteringTest.host_index
        self._next_replication_port = CONFIG.replication_port
        self._forwarder = None
        self._forwarder_type = UniversalForwarder
        self._build_tgz = None
        self._multisite = multisite
        self._sites = sites
        self._replication_factor = replication_factor
        self._search_factor = search_factor
        self._site_replication_factor = site_replication_factor
        self._site_search_factor = site_search_factor

        if self._config.local_build != None:
            full_path = os.path.expanduser(CONFIG.local_build)
            os.system(full_path + '/bin/splunk clean all -f --accept-license --answer-yes --no-prompt')
            os.system(full_path + '/bin/splunk clone-prep-clear-config --accept-license --answer-yes --no-prompt')
            self._build_tgz = output_filename = 'tempsplunk.tgz'

            def exclude_from_tar(filename):
                if filename.endswith('etc/system/local/server.conf') or filename.endswith('etc/system/local/web.conf'):
                    return True

            with tarfile.open(output_filename, "w:gz") as tar:
                tar.add(full_path, arcname='splunk', exclude=exclude_from_tar)
            LOGGER.info('self._build_tgz = %s' % self._build_tgz)

        if hasattr(CONFIG, 'archives'):
            self._archives = CONFIG.archives
            LOGGER.info('self._archives = %s' % self._archives)
        else:
            self._archives = {}

        if multisite is True:
            if masters > 0:
                self.new_node(mode='master',multisite=True,sites=sites,
                    site_replication_factor=site_replication_factor,
                    site_search_factor=site_search_factor)
            for i in range(sites):
                for j in range(slaves):
                    self.new_node(mode='slave',multisite=True,site=i+1)
                for k in range(search_heads):
                    self.new_node(mode='searchhead',multisite=True,site=i+1)
        else:
            if masters > 0:
                self.new_node(mode='master')
            for i in range(slaves):
                self.new_node(mode='slave')
            for i in range(search_heads):
                self.new_node(mode='searchhead')

#        if masters > 0:
#            if sites > 1:
#                self.new_node(mode='master')
#            else:
#                self.new_node(mode='master',multisite=True)
#        for i in range(sites)
#            for j in range(slaves):
#                self.new_node(mode='slave',site=i)
#            for k in range(search_heads):
#                self.new_node(mode='searchhead',site=i)
        
        self.log_info()

    @property
    def instances(self):
        '''
        @return: All non-forwarder splunk instances including those
        not configured as a cluster node
        @rtype: list
        '''
        return self._instances

    @property
    def master(self):
        '''
        @rtype: Splunk
        '''
        master_list = [instance for instance in self._instances
                       if instance.mode == 'master']
        if len(master_list) > 0:
            return master_list[0]
        else:
            return None

    @property
    def slaves(self):
        '''
        @rtype: list<Splunk>
        '''
        return [instance for instance in self._instances
                if instance.mode == 'slave']

    @property
    def search_heads(self):
        '''
        @rtype: list<Splunk>
        '''
        return [instance for instance in self._instances
                if instance.mode == 'searchhead']

    @property
    def other_instances(self):
        '''
        @return: all instances not configured as a cluster node.
        @rtype: list<Splunk>
        '''
        return [instance for instance in self._instances
                if instance.mode is None]

    @property
    def hosts(self):
        '''
        @return: Hosts available to cluster.
        @rtype: list
        '''
        return self._hosts

    @property
    def forwarder(self):
        '''
        @return: A UF by default, HWF or LWF if self.forwarder_type changed
        @rtype: Splunk
        '''
        if self._forwarder is None:
            splunk_home = self._config.splunk_home
            Forwarder = type('Splunk',
                             (SplunkFactory.getSplunkClassName(connection=None), self._forwarder_type,),
                             {})
            LOGGER.debug('initializing forwarder')
            self._forwarder = Forwarder(splunk_home)
            self._forwarder.set_vars(self._config)
            self._forwarder.slaves = self.slaves
            self.instances.append(self._forwarder)
        return self._forwarder

    @property
    def forwarder_type(self):
        '''
        @return: UniversalForwarder, HWForwarder, or LWForwarder
        @rtype: ForwarderBase
        '''
        return self._forwarder_type

    @forwarder_type.setter
    def forwarder_type(self, value):
        '''
        The type of forwarder you want when you call cluster.forwarder.
        @param value: universal, heavy or light
        @type value: str
        '''
        if value == 'universal':
            self._forwarder_type = UniversalForwarder
        elif value == 'heavy':
            self._forwarder_type = HWForwarder
        elif value == 'light':
            self._forwarder_type = LWForwarder
        else:
            raise Exception("Forwarder must be universal/light/heavy")

    @property
    def generation_id(self):
        '''
        See http://docs.splunk.com/Splexicon:GenerationID
        @rtype: int
        '''
        self.master.set_splunk_models()
        generation_id = -1
        for generation in ClusterMasterGeneration.all():
            generation_id = generation.generation_id
        return generation_id

    #@property
    #def sh_generation_id(self, splunk_instance=None):
    #    '''
    #    See http://docs.splunk.com/Splexicon:GenerationID
    #    @rtype: int
    #    '''
    #    splunk_instance.set_splunk_models()
    #    generation_id = -1
    #    gen_id_list = ClusterSearchheadGeneration.all()
    #    assert(len(gen_id_list) == 1)
    #    generation_id = gen_id_list[0].generation_id
    #    return generation_id

    def start_cluster_nodes_which_are_down(self):
        for instance in self._instances:
            if(instance.is_running()==False):
                LOGGER.info('Starting splunk instance:'+instance.splunk_home+' Instance mode:'+str(instance.mode))
                instance.execute('start')
                counter = 0
                while not instance.is_running() and counter < 3: #ideall we shouldn't land here. sometimes on windows start timesout
                    time.sleep(10)
                    counter = counter + 1
                LOGGER.info('instance status: {status}'.format(status=instance.is_running()))
        if(self._forwarder!=None):
            if(self._forwarder.is_running()==False):
                LOGGER.info('Starting Splunk forwarder:'+self._forwarder.splunk_home)
                self._forwarder.start()

    def new_node(self, mode=None, host_name=None, multisite=False, sites=1, site=None,
                 replication_factor=3, search_factor=2, site_replication_factor='',
                 site_search_factor=''):
        '''
        Create a new splunk instance, optionally configured as a cluster node.
        Optionally specify a host name if you need it on a specific host.

        @param mode: master, slave, or searchhead
        @param host_name: The host_name without the scheme
        @param dev_build: path to dev build
        @return: A splunk instance
        @rtype: Splunk
        '''
        instance = None
        ssh_conn = None
        splunk_home = None

        if host_name is None:
            if self._hosts is not None:
                host_name = self.next_host()
            else:
                LOGGER.info('Setting the hostname to the localhost')
                host_name = socket.gethostbyname(socket.gethostname())
 
        LOGGER.debug('Configuring a {mode} for site{site} on {host_name} '
                     .format(mode=mode, site=site, host_name=host_name))
        
        assert host_name is not None

        if host_name in ('localhost',
                         socket.gethostname(),
                         "127.0.0.1",
                         self.local_ip):
            LOGGER.debug('Creating LocalSplunk instance')
            splunk_home = self._config.splunk_home
            Splunk = type('Splunk', (SplunkFactory.getSplunkClassName(connection=None), SplunkBase), {})
            instance = Splunk(splunk_home)
        else:
            LOGGER.debug('Creating SSHSplunk instance')
            splunk_home = self._config.remote_splunk_home
            ssh_conn = SSHConnection(host_name,
                                     22,
                                     self._config.ssh_user,
				     self._config.ssh_password,
				     self._config.ssh_domain,
                                     None)
            Splunk = type('Splunk', (SplunkFactory.getSplunkClassName(connection=ssh_conn), SplunkBase), {})
            instance = Splunk(ssh_conn, splunk_home)
            instance.ssh_conn = ssh_conn

        LOGGER.info('calling splunk.set_vars() to set properties')
        instance.archives = self._archives
        instance.build_tgz = self._build_tgz
        instance.set_vars(self._config)
        timestr = strftime("%Y-%m-%d-%H.%M.%S", gmtime())
        instance.server_name = '{}-{}'.format(host_name, timestr)

        if mode is not None:
            instance.configure_as_cluster_node(config=self._config,
                                               mode=mode,
                                               replication_port=None,
                                               master=self.master,
                                               multisite=multisite,
                                               sites=sites,
                                               site=site,
                                               replication_factor=replication_factor,
                                               search_factor=search_factor,
                                               site_replication_factor=site_replication_factor,
                                               site_search_factor=site_search_factor)
        self.instances.append(instance)
        return instance

    def next_host(self):
        '''
        @return: The next host in the list of available hosts
        @rtype: string
        '''
        assert len(self._hosts) > 0

        if self._current_host_index >= len(self._hosts):
            message='Running out of hosts. Add more hosts to the yml conf file.'
            LOGGER.error(message)
            raise Exception(message)

        host_name = self._hosts[self._current_host_index]
        self._current_host_index += 1
        ClusteringTest.host_index = self._current_host_index
        return host_name
    
    def clean_cluster(self):
        '''
        This function brings cluster back to new state by deleting existing indexed data, by removing forward-servers, by removing existing file monitors at the forwarder, also by removing already applied bundles
        '''
        #Order of calls matters. Delete_data() is followed by remove_all_forward_servers, coz in delete_data we delete only if forwarder.configured=True
        self.delete_data()
        self.forwarder.remove_all_forward_servers() #It sets the forwarder.configured to False
        self.remove_bundles()
        LOGGER.info('Done cleaning cluster')

    def delete_data(self):
        '''
        This function deletes the existing indexed data in the cluster by running clean on all slaves as well as on the forwarder. It also removes monitors.
        Note: Dont' call this function after calling remove_all_forward_servers coz the later one sets the configured to False & for optimization purposes del        ete_data delets data only if configured is True.
        '''
        if(self.forwarder.configured==True): #delete data only if fwding is configured.. so this forces testers to configure fwd & add data using clustering api's not by running add monitors/add forward-server commands at the test level.Otherwise, configure=False even they have fwd configured. Take out this if will slow down the tests coz there may be many tests which dont add data so no need to delete data in those cases
            LOGGER.info('Deleting data in the cluster')
            self.forwarder.stop()

            for source in self.forwarder.forwarded_inputs:
                    self.forwarder.execute('remove monitor {s} {auth} '.format(s=source, auth=self.forwarder.auth()))
                    LOGGER.info('Removed monitor on:' + source)

            self.forwarder.execute('clean eventdata -f --accept-license --answer-yes --no-prompt')
            self.forwarder.execute('clean globaldata -f --accept-license --answer-yes --no-prompt')
            self.forwarder.execute('clean inputdata -f --accept-license --answer-yes --no-prompt')
            LOGGER.info('Done executing clean data command on the forwarder')
            self.forwarder.start()

            self.forwarder.forwarded_inputs = []

            for slave in self.forwarder.indexer_slaves:
                slave.stop()
                slave.execute('clean eventdata -f --accept-license --answer-yes --no-prompt')
                slave.execute('clean globaldata -f --accept-license --answer-yes --no-prompt')
                slave.execute('clean inputdata -f --accept-license --answer-yes --no-prompt')	
            LOGGER.info('Done executing clean data command on all indexer slaves')
            for slave in self.forwarder.indexer_slaves:
                slave.start()
            LOGGER.info('Deleted data in the cluster')
        else:
            LOGGER.info('Fowarding is not configured for this forwarder. So no data to delete.')

    def remove_bundles(self):
        '''
        This method removes the existing bundles from the cluster.
        '''
        mappslocal=self.master.splunk_home + os.sep + 'etc' + os.sep + 'master-apps' + os.sep + '_cluster' + os.sep + 'local' + os.sep
        if(self.master.is_remote==True):
            cmd = 'python -c "import shutil; shutil.rmtree(\'"' + mappslocal.replace('\\', '/')+ '"\')"'
            (code, stdout, stderr) = self.master.connection.execute(cmd)
            message='cmd executed on master:' + cmd + ', return code:' + str(code) + ' stdout:' + stdout + ' stderr:' + stderr
            LOGGER.info(message)
            if(code!=0):
                raise Exception('Unexpected Error. {m}'.format(m=message))

            cmd1 = 'python -c "import os; os.makedirs(\'"'+mappslocal.replace('\\', '/')+ '"\')"'
            (code1, stdout1, stderr1) = self.master.connection.execute(cmd1)
            LOGGER.info('cmd executed on master:' + cmd1 + ' return code:' + str(code1) + ' stdout:' + stdout1 + ' stderr:' + stderr1)
        else: 
            LOGGER.info('Removing existing bundles under master_apps' + os.sep + 'local')
            shutil.rmtree(mappslocal)
            os.makedirs(mappslocal)
        self.apply_bundle()

    def apply_bundle(self):
        '''
        '''
        auth_str = '-auth %s:%s' %(self.master.username, self.master.password)
        output = self.master.execute('apply cluster-bundle --answer-yes %s' %auth_str)
        assert output[0] == 0
        tries = 150
        time_to_wait = 15
        for aTry in range(tries):
            output1 = self.master.execute('show cluster-bundle-status %s' %auth_str)
            LOGGER.info("output1: %s" % output1[1])
            time.sleep(time_to_wait)
            output2 = self.master.execute('show cluster-bundle-status %s' %auth_str)
            LOGGER.info("output2: %s" % output2[1])
            if output1[1] == output2[1]:
                break
            else:
                time.sleep(time_to_wait)
        assert output1[1] == output2[1]

    def wait_for_rolling_restart_to_finish(self, maxWaitTime=None): #if maxWaitTime is None, dervie wait time  basing on no of instances
        '''
        This method waits until rolling restart is finished (if happening). Note: Make sure self.cluster.master.set_splunk_models() is set before this context so that clustering splunk models have Master's valid session ifo.
        '''
        if maxWaitTime is None:
            maxWaitTime = len(self.slaves)*100 #100 seconds per slave.
        LOGGER.info('max rolling restart wait time is set to: {waitTime}'.format(waitTime=maxWaitTime))
        status = str(ClusterMasterInfo.all()[0].apply_bundle_status["status"])
        status_keyword = "Rolling restart"
       
        if(status.find(status_keyword)==-1 and status.find('in progress')==-1):
            LOGGER.info("No rolling restart happening. Status:"+status)
        else:
            pollCount=0
            pollInterval=5 #coz puttig 2 or 3 is kinda too optimistic
            maxPollCount=maxWaitTime/pollInterval
            while (status.find(status_keyword)!= -1 and status.find('in progress')!=-1 and pollCount < maxPollCount):
                status = str(ClusterMasterInfo.all()[0].apply_bundle_status["status"])
                LOGGER.info("Apply bundle status {s}".format(s=status))
                time.sleep(pollInterval)
                pollCount+=1
            if(pollCount>=maxPollCount):
                LOGGER.error('Rolling Restart is taking more than maximum expected Time. maxExpectedTime:'+str(maxWaitTime))
                LOGGER.error('Rolling restart status:'+status)
                raise Exception('Rolling Restart is taking more than maximum expected Time. maxExpectedTime:'+str(maxWaitTime))
            LOGGER.info("Done Rolling restart. Status: {s}".format(s=status))

    def wait_for_bundle_reload_to_finish(self, maxWaitTime=240):
        '''
        This method waits until bundle reload is finished (if happening). Note: Make sure self.cluster.master.set_splunk_models() is set before this context so that clustering splunk models have Master's valid session info.
        '''
        status = str(ClusterMasterInfo.all()[0].apply_bundle_status["status"])
        status_keyword = "bundleReload"
        if(status.find(status_keyword)==-1 and status.find('in progress')==-1):
            LOGGER.info("No bundle reload happening. Status:"+status)
        else:
            pollCount=0
            pollInterval=2
            maxPollCount=maxWaitTime/pollInterval
            while (status.find(status_keyword) != -1 and status.find('in progress')!=-1 and pollCount < maxPollCount):
                status = str(ClusterMasterInfo.all()[0].apply_bundle_status["status"])
                LOGGER.info("Apply bundle status {s}".format(s=status))
                time.sleep(pollInterval)
                pollCount+=1
            if(pollCount>=maxPollCount):
                LOGGER.error('Bundle reload is taking more than maximum expected Time. maxExpectedTime:'+str(maxWaitTime))
                LOGGER.error('Bundle reload status:'+status)
                raise Exception('Bundle reload is taking more than maximum expected Time. maxExpectedTime:'+str(maxWaitTime))
            LOGGER.info("Done bundle reload. Status: {s}".format(s=status))
    
    def wait_for_bundle_validation_to_finish(self, maxWaitTime=180):
        '''
        This method waits until bundle validation is finished (if happening). Note: Make sure self.cluster.master.set_splunk_models() is set before this context so that clustering splunk models have Master's valid session info.
        '''
        status = str(ClusterMasterInfo.all()[0].apply_bundle_status["status"])
        status_keyword = "Bundle validation"
        if(status.find(status_keyword)==-1 and status.find('in progress')==-1 ):
            LOGGER.info("No bundle validation happening. Status:"+status)
        else:
            pollCount=0
            pollInterval=2
            maxPollCount=maxWaitTime/pollInterval
            while (status.find(status_keyword) != -1 and status.find('in progress')!=-1  and pollCount < maxPollCount):
                status = str(ClusterMasterInfo.all()[0].apply_bundle_status["status"])
                LOGGER.info("Apply bundle status {s}".format(s=status))
                time.sleep(pollInterval)
                pollCount+=1
            if(pollCount>=maxPollCount):
                LOGGER.error('Bundle validation is taking more than maximum expected Time. maxExpectedTime:'+str(maxWaitTime))
                LOGGER.error('Bundle validation status:'+status)
                raise Exception('Bundle validation is taking more than maximum expected Time. maxExpectedTime:'+str(maxWaitTime))
            LOGGER.info("Done bundle validation. Status: {s}".format(s=status))
    
    def wait_for_bundle_creation_to_finish(self, maxWaitTime=120):
        '''
        This method waits until bundle creation event (that occur afer bundle push) gets  finished (if happening). Note: Make sure self.cluster.master.set_splunk_models() is set before this context so that clustering splunk models have Master's valid session info.
        '''
        #  Note: This particular method is not tested. Need to make sure that Bundle Creation in progress status is actual valid status (& we are grepping for right string
        status = str(ClusterMasterInfo.all()[0].apply_bundle_status["status"])
        status_keyword = "Bundle creation"
        if(status.find(status_keyword)==-1 and status.find('in progress')==-1):
            LOGGER.info("No bundle creation happeing (or) finished. Status:"+status)
        else:
            pollCount=0
            pollInterval=2
            maxPollCount=maxWaitTime/pollInterval
            while (status.find(status_keyword) != -1 and status.find('in progress')!=-1 and pollCount < maxPollCount):
                status = str(ClusterMasterInfo.all()[0].apply_bundle_status["status"])
                LOGGER.info("Apply bundle status {s}".format(s=status))
                time.sleep(1)
                pollCount+=1
            if(pollCount>=maxPollCount):
                LOGGER.error('Bundle creation is taking more than maximum expected Time. maxExpectedTime:'+str(maxWaitTime))
                LOGGER.error('Bundle creation status:'+status)
                raise Exception('Bundle creation is taking more than maximum expected Time. maxExpectedTime:'+str(maxWaitTime))
            LOGGER.info("Done bundle creation. Status: {s}".format(s=status))

    def wait_for_in_progress_bundle_update_events(self, maxWaitTime=480):
        '''
        This method waits until all in-progress events that occur afer bundle push are finished (if happening). Note: Make sure self.cluster.master.set_splunk_models() is set before this context so that clustering splunk models have Master's valid session info.
        '''
        status = str(ClusterMasterInfo.all()[0].apply_bundle_status["status"])
        status_message = "in progress"
        if(status.find(status_message)==-1):
            LOGGER.info("No bundle update related events are in progress. Status:"+status)
        else:
            pollCount=0
            pollInterval=2
            maxPollCount=maxWaitTime/pollInterval
            while (status.find(status_message) != -1 and pollCount < maxPollCount):
                status = str(ClusterMasterInfo.all()[0].apply_bundle_status["status"])
                LOGGER.info("Apply bundle status {s}".format(s=status))
                time.sleep(1)
                pollCount+=1
            if(pollCount>=maxPollCount):
                LOGGER.error('Bundle in-progress events are taking  more than maximum expected Time. maxExpectedTime:'+str(maxWaitTime))
                LOGGER.error('current Bundle apply status:'+status)
                raise Exception('Bundle in-progress events are taking  more than maximum expected Time. maxExpectedTime:'+str(maxWaitTime))
            LOGGER.info("Done with all in-progress apply bundle events. Status: {s}".format(s=status))

    def log_info(self):
        '''
        Log information about each node in the cluster including the status.
        '''
        info_string = 'Cluster info'
        for instance in self._instances:
            info_string += '\n\n=============================================='
            status = instance.execute('status')
            info_string += ('''\ns{server_name}
                \n\tMode = {mode}
                \n\tHost = {host}
                \n\tSPLUNK_HOME = {splunk_home}
                \n\tWeb-port = {web_port}
                \n\tSplunkd-port = {splunkd_port}
                \n\tStatus = {status}'''
                            .format(server_name=instance.server_name,
                            status=status[1].replace('\n', '\n\t'),
                            mode=instance.mode,
                            host=instance.host_name,
                            web_port=instance.web_port(),
                            splunkd_port=instance.splunkd_port(),
                            splunk_home=instance.splunk_home))
        LOGGER.info(info_string)

    @property
    def local_ip(self):
        '''
        @return: IPv4 address of machine running test.
        @rtype: str
        '''
        return socket.gethostbyname(socket.gethostname())

    def teardown(self):
        '''
        Force stop each splunk instance and uninstall it.
        '''
        LOGGER.info("number of instances: {n}".format(n=len(self.instances)))
        for instance in self.instances:
            LOGGER.info("mode: {m}".format(m=instance.mode))
            instance.teardown()
        for archive in self._archives:
            os.remove(self._archives[archive])
        if self._build_tgz != None:
            os.remove(self._build_tgz)

class SplunkBase(object):
    '''
    A wrapper for the helmut Splunk base class that includes properties
    useful for clustering tests.
    '''

    def set_vars(self, config):
        '''
        Apply properties from config, change splunk_home if it's taken, start
        the instance, change the password from the default.

        @param config: The global config object.
        '''
        self._config = config
        self.username = config.username
        self.password = config.password
        self.mode = None
        self.set_splunk_home()
        self.install()
        #webconf = open('{sh}/etc/system/local/web.conf'.format(sh=self.splunk_home), 'w+')
        #webconf.write("[settings]\nstartwebserver=0")
        #webconf.close()
        # (code, stdout, stderr) = self.execute('disable webserver {auth}'.format(auth=self.auth()))
        #assert code == 0
        #(code, stdout, stderr) = self.execute('start --auto-ports')
        #assert code < 2
        self.start(auto_ports=True)
        self.change_password(user_name=config.username, old_password=config.password, new_password=config.new_password)

        self.server_name = str(random.random())

    @property
    def ssh_conn(self):
        '''
        @return: The object containing the SSH info.
        @rtype: SSHConnection
        '''
        return self._ssh_conn

    @ssh_conn.setter
    def ssh_conn(self, value):
        '''
        @param value: The SSHConnection for communicating with a remote
        splunk instance
        '''
        assert type(value) is SSHConnection
        self._ssh_conn = value

    @property
    def server_name(self):
        '''
        @return: The server name found in server.conf. Must be unique
        to cluster.
        @rtype: str
        '''
        return self._server_name

    @server_name.setter
    def server_name(self, value):
        '''
        @param value: A name unique in the cluster
        '''
        self._server_name = value
        stanza = self.confs()['server']['general']
        stanza['serverName'] = value

    @property
    def host_name(self):
        '''
        @return: The host name without scheme or port
        @rtype: str
        '''
        if self.is_remote:
            return self.splunkd_host()
        else:
            return socket.gethostbyname(socket.gethostname())

    @property
    def splunk_home(self):
        '''
        @rtype: str
        '''
        return self._splunk_home

    @property
    def splunkd_port(self):
        '''
        @return: The management port.
        @rtype: int
        '''
        return self.splunkd_port()

    @property
    def web_port(self):
        '''
        @return: The Splunk web port
        @rtype: int
        '''
        output = self.execute('show web-port {}'.format(self.auth()))
        output = output[1]
        output = output.replace(' ', '')
        output = output.split(':')
        exception_message = 'splunk show web-port output not an int'
        try:
            return int(output[1])
        except Exception(exception_message):
            LOGGER.error(exception_message)
            return -1

    @property
    def tcp_input_port(self):
        '''
        @return: The tcp port on which Splunk listens for data.
        @rtype: int
        '''
        self.set_splunk_models()
        port = -1
        for input_port in SplunkTCPInput.all():
            exception_message = 'No TCP port found'''
            try:
                port = int(input_port.name)
            except Exception(exception_message):
                LOGGER.error(exception_message)
        return port

    @tcp_input_port.setter
    def tcp_input_port(self, value):
        '''
        @param value: A port for splunk to listen to data
        @type: int
        '''
        assert type(value) is int
        #stanza = self.confs()['inputs'].create_stanza('splunktcp://{port}'.format(port=value))
        self.execute('enable listen {port} {auth}'
                     .format(port=value,auth=self.auth()))
        LOGGER.info('Enabling TCP listen for {server} on {port}'
            .format(server=self.server_name, port=value))
            
    @property
    def replication_factor(self):
        '''
        @return: http://docs.splunk.com/Splexicon:Replicationfactor
        @rtype: int
        '''
        self.set_splunk_models()
        replication_factor = -1
        for config in ClusterConfig.all():
            replication_factor = config.replication_factor
        assert replication_factor > -1
        return replication_factor

    @replication_factor.setter
    def replication_factor(self, value):
        '''
        @param value: http://docs.splunk.com/Splexicon:Replicationfactor
        @type value: int
        '''
        assert type(value) is int and value > 0
        LOGGER.info('Resetting replication_factor to {val}'.format(val=value))
        stanza = self.confs()['server']['clustering']
        stanza['replication_factor'] = value
        self.restart()

    @property
    def search_factor(self):
        '''
        @return: http://docs.splunk.com/Splexicon:Searchfactor
        @rtype: int
        '''
        self.set_splunk_models()
        search_factor = -1
        for config in ClusterConfig.all():
            search_factor = config.search_factor
        assert search_factor > -1
        return search_factor

    @search_factor.setter
    def search_factor(self, value):
        '''
        @param value: http://docs.splunk.com/Splexicon:Searchfactor
        @type value: int
        '''
        assert type(value) is int and value > 0
        LOGGER.info('Resetting search_factor to {val}'.format(val=value))
        stanza = self.confs()['server']['clustering']
        stanza['search_factor'] = value
        self.restart()

    @property
    def secret(self):
        '''
        @return: A key that must match the key of other cluster nodes.
        @rtype: str
        '''
        secret = None
        try:
            stanza = self.confs()['server']['clustering']
            secret = stanza['pass4SymmKey']
        except:
            pass
        return secret

    @secret.setter
    def secret(self, value):
        '''
        @param value: A string shared with other cluster nodes
        @type value: str
        '''
        LOGGER.info('Setting secret key on {hn}'.format(hn=self.host_name))
        stanza = self.confs()['server']['clustering']
        stanza['pass4SymmKey'] = value
        self.restart()

    @property
    def buckets(self):
        '''
        @return: Buckets of all peers (if called from master).
        @rtype: dict
        '''
        self.set_splunk_models()
        buckets = []
        if self.mode == 'master':
            for bucket in ClusterMasterBucket.all():
                buckets.append(bucket)
        elif self.mode == 'slave':
            for bucket in ClusterSlaveBucket.all():
                buckets.append(bucket)
        return buckets

    @property
    def peers(self):
        '''
        @return: all peers (if called from master).
        @rtype: list
        '''
        self.set_splunk_models()
        peers = []
        if self.mode == 'master':
            for peer in ClusterMasterPeer.all():
                peers.append(peer)
        return peers

    @property
    def sites(self):
        '''
        @return: all sites (if called from master).
        @rtype: list
        '''
        self.set_splunk_models()
        sites = []
        if self.mode == 'master':
            for site in ClusterMasterSite.all():
                sites.append(site)
        return sites

    @property
    def guid(self):
        '''
        @return: The GUID of the instance.
        @rtype: str
        '''
        self.set_splunk_models()
        return SplunkdConfig.get().guid

    @property
    def is_remote(self):
        '''
        @return: Whether it's a remotely hosted splunk instance
        @rtype: bool
        '''
        return SSHSplunk in inspect.getmro(type(self))

    def teardown(self):
        try:
            if self.is_installed():
                self.execute('stop -f')
        except Exception('No previous splunk instance running'):
            LOGGER.info('No previous splunk instance running')
        try:
            self.uninstall()
        except Exception('No previous splunk instance installed'):
            LOGGER.info('No previous splunk instance installed')

    def restart():
	'''
	SPL-67752 - we used to run stop (both splunkd and splunkweb)
	followed by sleep(20) followed by start

	Changed to just stop and start splunkd and get rid of the sleep

	My guess is the sleep was for windows since windows sometimes doesn't
	release ports after stop returns, but a flat sleep for that is
	a bit overkill, we should add some smarter code to retry in case
	we encounter that issue
	'''
        self.execute('stop splunkd')
        self.execute('start splunkd')

    def set_splunk_home(self):
        '''Changes splunk_home if it already exists'''
        if isinstance(self, SSHSplunk):
            self._splunk_home = self._config.remote_splunk_home
        else:
            counter = 0
            splunk_home = self._config.splunk_home
            new_splunk_home = splunk_home
            while counter < 100:
                LOGGER.info('Setting SPLUNK_HOME. ' \
                            'Checking to see if {sh} exists on {host}'
                            .format(sh=new_splunk_home, host=self.host_name))
                if not os.path.isdir(new_splunk_home):
                    LOGGER.info('{sh} available on localhost'
                            .format(sh=new_splunk_home))
                    break
                new_splunk_home = splunk_home + str(counter)
                counter += 1
            self._splunk_home = new_splunk_home

    def set_splunk_models(self):
        '''
        Set the host path and get a session key so splunk models can be used
        '''
        LOGGER.info('Setting splunk models with mergeHostPath/getSessionKey')
        host_path = 'https://{host}:{mgmt_port}'.format(host=self.host_name,
                                                        mgmt_port=
                                                        self.splunkd_port())
        splunk.mergeHostPath(host_path, True)
        return splunk.auth.getSessionKey(username=self.username,
                                         password=self.password,
                                         hostPath=host_path)

    def configure_as_cluster_node(self,
                                  config,
                                  mode,
                                  master=None,
                                  replication_port=None,
                                  multisite=False,
                                  sites=1,
                                  site=None,
                                  replication_factor=3,
                                  search_factor=2,
                                  site_replication_factor='',
                                  site_search_factor=''):
                                  #site_replication_factor='origin:2,total:3',
                                  #site_search_factor='origin:2,total:3'):
        '''
        Configure a node as a master, slave, or searchhead.
        @param config: The pytest config object
        @param mode: master, slave, or searchhead
        @type mode: str
        @param master: The cluster master.
        @type master: Splunk
        @param replication_port: http://docs.splunk.com/Splexicon:Replicationport
        @type replication_port: int
        '''
        self.mode = mode
        if site != None:
            self.site = 'site%d' % site
        else:
            self.site = None

        if replication_port is None:
            replication_port = PORTUTIL.find_open_port(target=self.host_name)
        command = 'edit cluster-config -mode {mode}'.format(mode=self.mode)
        if self.mode is 'master':
            if multisite is True:
                command += ' -multisite 1'
                command += ' -site site1'
                if site_replication_factor != '':
                    command += ' -site_replication_factor %s' % site_replication_factor
                if site_search_factor != '':
                    command += ' -site_search_factor %s' % site_search_factor
                command += ' -available_sites'
                delim = ' '
                for i in range(sites):
                    command += delim
                    command += 'site%d' % (i+1)
                    delim = ','
            elif multisite is False:
                command += ' -replication_factor %d' % replication_factor
                command += ' -search_factor %d' % search_factor
        elif self.mode is 'slave' or self.mode is 'searchhead':
            if(master is None):
                LOGGER.error('No master specified')
                raise Exception("No Master configured yet.")
            self.tcp_input_port = PORTUTIL.find_open_port(target=self.host_name)  # self.enable_listen(listening_ports)
            LOGGER.info('Listening enabled on {}'
                        .format(self.display_listen()))
            master_host = master.host_name
            command += (' -master_uri {scheme}://{uri}:{port}'
                        .format(scheme=config.scheme,
                                uri=master_host,
                                port=master.splunkd_port()))
            if multisite is True and site is not None:
                command += (' -site %s' % self.site)
        counter = 100
        command_with_rep_port = ('{command} -replication_port {rp} {auth}'
                                 .format(command=command,
                                         rp=replication_port,
                                         auth=self.auth()))
        LOGGER.info('Executing command: %s' % command_with_rep_port)
        output = self.execute(command_with_rep_port)
        LOGGER.debug('splunk edit cluster-config output: {op}'
                     .format(op=output[2]))
        self.restart()

    def install(self):
        '''
        Install the latest build or specified build from branch specified
        in the pytest.config object.
        '''
        if self.build_tgz != None: # if dev build
            archive = self.build_tgz
            LOGGER.info('Using archive = %s' % archive)
            self.install_from_archive(archive)
        else: #if not dev build
            build = None
            config = self._config
            LOGGER.info('Installing splunk from this branch: {branch}'
                        .format(branch=config.branch))
            if not hasattr(config, 'build'):
                setattr(config, 'build', None)
            self.install_nightly(branch=config.branch, build=config.build)

    def upgrade(self):
        '''
        Upgrade existing Splunk instance to the latest build or specified build from
        branch specified in the pytest.config object.
        '''
        build = None
        config = self._config
        LOGGER.info('Upgrading Splunk to this branch: {branch}'
                    .format(branch=config.upgrade_branch))
        platform = None
        if SSHSplunk in inspect.getmro(type(self)):
            platform = SSHHostUtils._get_host_platform(self.ssh_conn)
        else:
            platform = splunk_platform.get_platform()
        platform_string = str(platform)
        archive = None
        if not hasattr(config, 'upgrade_build'):
            setattr(config, 'upgrade_build', None)
        pkg = NightlyPackage(platform=platform, branch=config.upgrade_branch)
        pkg.build = config.upgrade_build
        archive = pkg.download()
        self.archives[platform_string] = archive
        self.install_from_archive(archive)

    def roll_hot_buckets(self):
        '''
        Force roll hot buckets so they replicate to other peers.
        '''
        LOGGER.info('Rolling hot buckets')
        self.execute('_internal call /data/indexes/*/roll-hot-buckets {auth}'
            .format(auth=self.auth()))

    def display_listen(self):
        '''
        Display splunktcp ports open for listening.
        @return: List of ports
        @rtype: list<int>
        '''
        try:
            self.set_splunk_models()
            tcp_inputs = []
            for tcp_input in SplunkTCPInput.all():
                tcp_inputs.append(int(tcp_input.name))
            return tcp_inputs
        except Exception('Cannot access splunktcp REST endpoint'):
            return -1

    def auth(self):
        '''
        @return: a string to add authorization to a CLI requiring login
        '''
        return ' -auth {user}:{pwd}'.format(user=self.username,
                                            pwd=self.password)

class ForwarderBase(SplunkBase):
    '''
    A base class for the three types of forwarders.
    '''
    @property 
    def indexer_slaves(self):
        if not hasattr(self, '_indexer_slaves'):
            self._indexer_slaves=[]
        return self._indexer_slaves

    @indexer_slaves.setter
    def indexer_slaves(self, value):
        self._indexer_slaves = value

    @property 
    def forwarded_inputs(self):
        if not hasattr(self, '_forwarded_inputs'):
            self._forwarded_inputs=[]
        return self._forwarded_inputs

    @forwarded_inputs.setter
    def forwarded_inputs(self, value):
        self._forwarded_inputs = value

    @property
    def configured(self):
        '''
        Whether the forwarder has been configured to forward to
        specific servers

        @rtype: bool
        '''
        if not hasattr(self, '_configured'):
            self._configured = False
        return self._configured

    @configured.setter
    def configured(self, value):
        '''
        @param value: Whether the Forwarder has been configured.
        @type value: bool
        '''
        assert type(value) is bool
        if not hasattr(self, '_configured'):
            self._configured = False
        self._configured = value

    @property
    def cluster(self):
        '''
        The cluster the forwarder is associated with.
        @rtype: Cluster
        '''
        if hasattr(self, '_cluster'):
            return self._cluster
        else:
            return None

    @cluster.setter
    def cluster(self, value):
        '''
        @param value: The cluster the forwarder is associated with.
        @type value: Cluster
        '''
        assert type(value) is Cluster
        self._cluster = value

    def configure(self, slaves=None):
        '''
        Configure forwarding to specific slaves. Auto-lb them.

        @param slaves: The slaves to forward data to. If no slaves provided,
        self._cluster.slaves used.
        @type slaves: Splunk or list<Splunk>
        '''
        if slaves is None:
            slaves = self.slaves
            LOGGER.info('No slaves provided for configuration. using {slaves}'
                .format(slaves=self.slaves))
        elif not type(slaves) is list:
            slaves = [slaves]
        self.execute('login {auth}'.format(auth=self.auth()))
        for slave in slaves:
            (code, stdout, stderr)=self.execute('list forward-server {auth}'.format(auth=self.auth()))
            if slave.host_name + ':' + str(slave.display_listen()[0]) not in stdout:            
                self.add_forward_server(slave.host_name, slave.display_listen()[0])
        if len(slaves) > 0:
             try:
                 stanza = self.confs()['limits']['thruput']
                 stanza['maxKBps'] = 1000000
                 stanza = self.confs()['outputs']['tcpout:default-autolb-group']
                 stanza['useACK'] = 'true' 
             except:
                 LOGGER.error('Cannot access conf files on forwarder')
        self.restart()
        forward_server_info = self.execute('list forward-server {}')
        response = self.execute('list monitor'.format(self.auth()))
        monitor_info = response[1]
        self.configured = True
	self.indexer_slaves.extend(slaves) # holds the list of configured indexer slaves. Used by cluster.delete_data to clean data in an optimized way.
        LOGGER.info('Forwarding config: {servers} \n monitors: {monitors}')

    def remove_all_forward_servers(self):
        '''
        Removes all the forward-servers associated with this forwarder.
        '''
        if(self.configured == True): #just to avoid doing this operation in those scenerios where forwarding is not even configured. this forces users to configure forwarding only through clustering api's...otherwise, we cant get configured=True
            listcommand = ('list forward-server {auth}'.format(auth=self.auth()))  
            (code, stdout, stderr)=self.execute(listcommand)
            assert code == 0
            temp=stdout.split('\n')
            for value in temp:
                if(value.startswith('\t') == True):
                    if ':' in value:
                        fwd_server = value[1:]
                        removecommand = ('remove forward-server {server} {auth}'.format(server=fwd_server, auth=self.auth()))
                        (code1, stdout1, stderr1) = self.execute(removecommand)
                        LOGGER.info('Removed forward-server:' + fwd_server + ' by running command:' + removecommand)
                        if(code1 != 0):
                            error_message = 'Error while removing forward-server:' + fwd_server + '\n stdout:' + stdout1 + '\n stderr:' + stderr1
                            LOGGER.error(error_message)
                            raise Exception(error_message)
            self.configured = False # setting configured=False as we unconfigured forwarding
            self.indexer_slaves=[] # no more slaves acting as indexers for this forwarder
        else:
            LOGGER.info('forwarding is not configured, so no forward-servers to remove')	

    def forward_data(self, data_file=None):
        '''
        Monitor the data specified as an argument of the default data-file

        @param data_file: The full path to a data file
        @type data_file: str
        '''
        if not self.configured:
            self.configure()
        if data_file is None:
            data_file = self._config.data_file
        data_file = os.path.abspath(data_file)
        (code, stdout, stderr) = self.execute('add monitor {} {}'.format(data_file, self.auth()))
        if (code !=0):
            error_message='Error while adding monitor on:'+data_file +'\n stdout:'+stdout+'\n stderr:'+stderr
            LOGGER.error(error_message)
            raise Exception(error_message)

        self.forwarded_inputs.append(data_file)


class UniversalForwarder(ForwarderBase):
    '''
    A forwarder with no splunkweb and no event parsing capabilities.
    '''
    def install(self):
        '''
        Install a universal forwarder
        '''
        self.install_nightly_forwarder(CONFIG.branch)


class LWForwarder(ForwarderBase):
    '''
    A lightweight forwarder
    '''

    def install(self):
        '''
        Install a lightweight forwarder.
        '''
        self.install_nightly(CONFIG.branch)
        self.execute('start --auto-ports')
        self.execute('enable app SplunkLightForwarder -auth {usr}:{pwd}'
                     .format(usr=CONFIG.username, pwd=CONFIG.password))
        self.restart()


class HWForwarder(ForwarderBase):
    '''
    A heavyweight forwarder.
    '''

    def install(self):
        '''
        Install a heavyweight forwarder.
        '''
        self.install_nightly(CONFIG.branch)
        self.execute('start --auto-ports')
        self.execute('enable app SplunkForwarder -auth {usr}:{pwd}'
                     .format(usr=CONFIG.username, pwd=CONFIG.password))
        self.restart()

def sdk_connector(splunk, username = None, password = None):
    '''
    A connector factory passed as an argument to the splunk connector
    @param splunk: a splunk instance
    @param username: splunk username
    @param password: password associated with above username
    '''
    if username is None or password is None:
        userame = splunk.username
        password = splunk.password
    LOGGER.info('''Calling sdk_connector. 
        username = {username}, 
        password = {password}'''
        .format(username=username,password=password))
    return SDKConnector(splunk, username, password)
