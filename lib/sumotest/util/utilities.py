"""
Meta
====
    $Id$
    $DateTime$
    $Author$
    $Change$
"""

import logging
import socket
from random import Random
import logging


PORT_MIN = 8000
PORT_MAX = 65500


class PortUtil(object):
    """
    Base class to get the utility functions in your tests
    """

    def __init__(self, port_min=PORT_MIN, port_max=PORT_MAX):
        '''
        Constructor
        'port_min' and 'port_max' are the range of ports
        '''
        self.port_min = port_min
        self.port_max = port_max
        self.logger = logging.getLogger("PortUtil")
        self.list_ports = []

    def _get_random_port(self):
        '''
        generates a random int between port_min and port_max.
        @rtype: integer
        @return: returns a random port between port_min and port_max
        '''
        rand = Random()
        num = rand.randint(self.port_min, self.port_max)
        while(num in self.list_ports):
            num = rand.randint(self.port_min, self.port_max)
        self.list_ports.append(num)
        return num

    def find_open_port(self, target='localhost', tries=100):
        '''
        Checks and returns open port else returns errors

        @type target: string
        @param target: hostname

        @type tries: int
        @param tries: number of attempt to get a random port that is open

        @rtype: integer
        @return: returns a random open port
        '''
        if (self.port_max - self.port_min) < tries:
            raise ValueError("Number of tries must not exceed the difference "
                             "in the port numbers.")
        targetIP = socket.gethostbyname(target)
        self.logger.info("Starting scan on host{IP}".format(IP=targetIP))
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        count = 0
        while count < tries:
            port = self._get_random_port()
            try:
                soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                soc.connect((targetIP, port))
                soc.close()
            except socket.error as error:
                if 'refused' in error.strerror:
                    return port
            count+=1
        raise Exception("Tried for {n} times, but found no random port "
                        "that is opened.".format(n=tries))
