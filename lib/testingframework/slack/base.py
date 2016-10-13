'''
This module has things regarding a generic slack deployment.

@author: Weimin Ma
@contact: U{wma.utd@gmail.com<mailto:wma.utd@gmail.com>}
@since: 2016-10-12
'''
from abc import ABCMeta, abstractmethod, abstractproperty
from testingframework.exceptions import UnsupportedConnectorError
from testingframework.log import Logging
from testingframework.connector.base import Connector
from testingframework.connector.rest import RESTConnector

class Slack(Logging):
    '''
    Represents a Slack deployment.
    This class is abstract and cannot be instantiated directly.

    @ivar connector_factory: The factory to use when creating the connector.
    @type connector_factory: function
    @ivar _default_connector: The default connector. Is None at first and is
                              later created when L{default_connector} is used.
    @type _default_connector: L{Connector}
    @ivar _start_listeners: A collection of start listeners
    @type _start_listeners: set
    @ivar name: The name of this instance. Defaults to the ID of this object.
    @type name: str
    @ivar _logger: The logger this instance uses.
    '''
    _name = ''
    _test_token = ''

    __metaclass__ = ABCMeta

    _CONNECTOR_TYPE_TO_CLASS_MAPPINGS = {Connector.REST: RESTConnector}

    def __init__(self, name):
        '''
        Creates a new Slack deployment.
        '''
        self._default_connector = None
        self._start_listeners = set()
        self._connectors = {}

        self._name = name or id(self)

        Logging.__init__(self)

    def __str__(self):
        '''
        Casts this instance to a string.

        @return: The string representation of this object.
        @rtype: str
        '''
        return self._str_format.format(**self._str_format_arguments)

    @abstractproperty
    def _str_format(self):
        '''
        The format to use when casting this instance to a string.

        @rtype: str
        '''

    @abstractproperty
    def _str_format_arguments(self):
        '''
        The arguments for the L{_str_format} to use when casting this instance
        to a string.

        @rtype: dict
        '''

    @property
    def name(self):
        '''
        The name of this instance.

        @rtype: str
        '''
        return self._name

    @property
    def test_token(self):
        return self._test_token

    @test_token.setter
    def test_token(self, value):
        self._test_token = value

    def uri_base(self):
        return 'https://'

    def register_start_listener(self, listener):
        '''
        Adds a listener that will be notified when connection to slack is lost.
        The listener must be a function (respond to C{__call__} to be more
        precise)

        @param listener: The start listener
        @raise InvalidStartListener: If the listener is not callable.
        '''
        _validate_start_listener(listener)
        self._start_listeners.add(listener)

    def unregister_start_listener(self, listener):
        '''
        Removes the specified start listener.
        If the listener is not in the list this call has no effect.
        @param listener: The listener to remove
        '''
        try:
            self._start_listeners.remove(listener)
        except KeyError:
            pass

    def create_connector(self, contype=None, *args, **kwargs):
        '''
        Creates and returns a new connector of the type specified or
        REST connector if none specified

        This connector will not be logged in, for that see
        L{create_logged_in_connector}

        Any argument specified to this method will be passed to the connector's
        initialization method

        @param contype: Type of connector to create, defined in Connector class,
           defaults to Connector.REST

        @return: The newly created connector
        '''
        contype = contype or Connector.REST

        if contype not in self._CONNECTOR_TYPE_TO_CLASS_MAPPINGS:
            raise UnsupportedConnectorError

        conn = self._CONNECTOR_TYPE_TO_CLASS_MAPPINGS[contype](self,
                                                               *args,
                                                               **kwargs)

        connector_id = self._get_connector_id(contype=contype,
                                              test_token=conn.test_token)

        if connector_id in self._connectors.keys():
            self.logger.warn("Connector {id} is being replaced".format(
                id=connector_id))
            del self._connectors[connector_id]
        self._connectors[connector_id] = conn

        return self._connectors[connector_id]

    def create_logged_in_connector(self, set_as_default=None, contype=None,
                                   *args, **kwargs):
        '''
        Creates and returns a new connector of type specified or of type
        L{SDKConnector} if none specified.

        This method is identical to the L{create_connector} except that this
        method also logs the connector in.

        Any argument specified to this method will be passed to the connector's
        initialization method

        @param set_as_default: Determines whether the created connector is set
                               as the default connector too. True as default.
        @type bool
        @param contype: type of connector to create, available types defined in
            L{Connector} class. Connector.REST as default

        @return: The newly created, logged in, connector
        '''
        contype = contype or Connector.REST
        conn = self.create_connector(contype, *args, **kwargs)
        if set_as_default:
            self._default_connector = conn
        return conn

    def set_default_connector(self, contype, test_token):
        '''
        Sets the default connector to an already existing connector

        @param contype: type of connector, defined in L{Connector} class
        @param test_token: slack test token used by connector
        @type test_token: string
        '''
        self._default_connector = self.connector(contype, test_token)

    def remove_connector(self, contype, test_token):
        '''
        removes a  connector, sets default connector to None if removing the
        default connector

        @param contype: type of connector, defined in L{Connector} class
        @param test_token: slack test token used by connector
        @type test_token: string
        '''
        if self.default_connector == self.connector(contype, test_token):
            self._default_connector = None

        connector_id = self._get_connector_id(contype, test_token)
        del self._connectors[connector_id]

    def _get_connector_id(self, contype, test_token):
        '''
        Returns the connector id

        @param contype: type of connector, defined in L{Connector} class
        @param test_token: slack test token used by connector
        @type test_token: string
        '''
        connector_id = '{contype}:{test_token}'.format(contype=contype, test_token=test_token)
        return connector_id

    def set_test_token_to_use(self, test_token=''):
        '''
        This method just initializes/updates self._test_token to test_token specified
        @param test_token: slack test_token that gets assigned to _test_token property of slack class
        It is asssumed that credentials specified here are already valid credentials.
        '''
        self._test_token = test_token

    @property
    def default_connector(self):
        '''
        Returns the default connector for this slack deployment.

        This method caches the value so it isn't created on every call.
        '''
        if self._default_connector is None:
            self._default_connector = self.create_logged_in_connector(
                set_as_default=True, test_token=self.test_token)
        return self._default_connector

    def connector(self, contype=None, test_token=None):
        '''
        Returns the connector specified by type and test_token, defaults to
        the default connector if none specified

        @param contype: type of connector, defined in L{Connector} class
        @param test_token: connector's test_token
        @type test_token: string
        '''
        if contype is None and test_token is None:
            return self.default_connector

        connector_id = self._get_connector_id(contype, test_token)
        if connector_id not in self._connectors.keys():
            raise InvalidConnector("Connector {id} does not exist".format(
                id=connector_id))

        return self._connectors[connector_id]

def _validate_start_listener(listener):
    '''
    Validates the start listener making sure it can be called.

    @param listener: The start listener
    @raise InvalidStartListener: If the listener is invalid
    '''
    if not _variable_is_a_function(listener):
        raise InvalidStartListener


def _variable_is_a_function(variable):
    '''
    Checks if a specified variable is a function by checking if it implements
    the __call__ method.

    This means that the object doesn't have to be a function to pass this
    function, just implement __call__

    @return: True if the variable is a function
    @rtype: bool
    '''
    return hasattr(variable, '__call__')


class InvalidConnector(KeyError):
    '''
    Raised when accessing an invalid connector
    '''
    pass
