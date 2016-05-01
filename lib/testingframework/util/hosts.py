from helmut.ssh.connection import SSHConnection

class Host(object):
    def __init__(self, host_name, ssh_user, ssh_password, splunk_home, ssh_domain = '.'):
        self.host_name = host_name
        self.ssh_user = ssh_user
        self.ssh_password = ssh_password
        self.splunk_home = splunk_home
        self.ssh_domain = ssh_domain

class Hosts(object):
    def __init__(self, hosts=[]):
        self.hosts = hosts
        self.cur_host_index = 0

    def add_host(self, host):
        self.hosts.append(host)
                
    def get_next_host(self):
        if self.hosts is None:
            return None
        if self.cur_host_index < len(self.hosts):
            cur_host =  self.hosts[self.cur_host_index]
            self.cur_host_index+=1
            return cur_host
        else:
            return None
 
    def reset_hosts_index(self, yaml_file):
        self.cur_host_index = 0
 
    def get_next_host_connection(self):
        next_host=self.get_next_host()
        if next_host is None:
            return None
        else:
            return SSHConnection(next_host.host_name,
                                 port=22,
                                 user=next_host.ssh_user,
                                 password=next_host.ssh_password,
                                 domain=next_host.ssh_domain,
                                 identity=None)
