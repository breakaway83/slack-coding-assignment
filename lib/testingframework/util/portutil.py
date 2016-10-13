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
logger=logging.getLogger("PortUtil")

class PortUtil:
    """
    Utility class for ports
    """
    @classmethod
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
        if (PORT_MAX - PORT_MIN) < tries:
            raise ValueError("Number of tries must not exceed the difference "
                             "in the port numbers.")
        targetIP = socket.gethostbyname(target)
        logger.info("Starting scan on host{IP}".format(IP=targetIP))
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        count = 0
        list_ports = []
        while count < tries:
            rand = Random()
            port = rand.randint(PORT_MIN, PORT_MAX)
            while(port in list_ports):
                port = rand.randint(PORT_MIN, PORT_MAX)
            list_ports.append(port)
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
