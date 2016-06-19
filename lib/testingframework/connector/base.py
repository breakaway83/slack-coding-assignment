'''
Module for handling generic connections with a Sumo deployment.

@author: Weimin Ma
@contact: U{weimin@sumologic.com<mailto:weimin@sumologic.com>}
@since: 2016-04-23
'''

from abc import ABCMeta

from testingframework.log import Logging


class Connector(Logging):
    '''
    A connector is an object that handles connections with Sumo.

    This is the abstract base class for all connectors.

    @cvar DEFAULT_USERNAME: The username that will be used if a username is not
                            explicitly specified.
    @cvar DEFAULT_PASSWORD: The password that will be used if a password is not
                            explicitly specified.
    @ivar _sumo: The Sumo deployment associated with this connector.
    @ivar _username: The username that this connector uses.
    @ivar _password: The password that this connector uses.
    @ivar _namespace: The namespace that this connector uses.
    '''

    __metaclass__ = ABCMeta
    DEFAULT_USERNAME = 'Administrator'
    DEFAULT_PASSWORD = ''
    #DEFAULT_NAMESPACE = 'nobody:system'

    # types of connectors
    (REST, SERVICEREST, SDK) = range(0, 3)

    def __init__(self, sumo, username=None, password=None):
        '''
        Creates a new Connector instance.

        @param sumo: The Sumo deployment we are communicating with.
        @type Sumo: L{Sumo<testingfraework.sumo.Sumo>}
        @param username: The username to use (or None for default)
        @type username: str
        @param password: The password to use (or None for default)
        @type password: str
        '''

        self._sumo = sumo
        self._username = username or self.DEFAULT_USERNAME
        self._password = password or self.DEFAULT_PASSWORD

        Logging.__init__(self)

    @property
    def sumo(self):
        '''
        The Sumo object associated with this connector.

        @rtype: L{Sumo<testingframework.sumo.Sumo>}
        '''
        return self._sumo

    @property
    def username(self):
        '''
        The username for this connector.

        @rtype: str
        '''
        return self._username
    
    @username.setter
    def username(self, value):
        '''
        Setter for the username property
        '''
        self._username = value

    @property
    def password(self):
        '''
        The password for this connector.

        @rtype: str
        '''
        return self._password
    
    @password.setter
    def password(self, value):
        '''
        Setter for the password property
        '''
        self._password = value
