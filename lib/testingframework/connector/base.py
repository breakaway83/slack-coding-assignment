'''
Module for handling generic connections with a slack deployment.

@author: Weimin Ma
@contact: U{wma.utd@gmail.com<mailto:wma.utd@gmail.com>}
@since: 2016-10-13
'''

from abc import ABCMeta
from testingframework.log import Logging

class Connector(Logging):
    '''
    A connector is an object that handles connections with slack APIs.
    This is the abstract base class for all connectors.

    @cvar DEFAULT_TEST_TOKEN: The test_token that will be used if a test_token is not
                            explicitly specified.
    @ivar _slack: The slack deployment associated with this connector.
    @ivar _test_token: The test token that this connector uses.
    '''

    __metaclass__ = ABCMeta
    DEFAULT_TEST_TOKEN = ''

    # types of connectors
    (REST, SDK) = range(0, 2)

    def __init__(self, slack, test_token=None):
        '''
        Creates a new Connector instance.

        @param slack: The slack deployment we are communicating with.
        @type slack: L{Slack<testingfraework.slack.Slack>}
        @param test_token: The test_token to use (or None for default)
        @type test_token: str
        '''

        self._slack= slack
        self._test_token= test_token or self.DEFAULT_TEST_TOKEN

        Logging.__init__(self)

    @property
    def slack(self):
        '''
        The Slack object associated with this connector.

        @rtype: L{Slack<testingframework.slack.Slack>}
        '''
        return self._slack

    @property
    def test_token(self):
        '''
        The test_token for this connector.

        @rtype: str
        '''
        return self._test_token
    
    @test_token.setter
    def test_token(self, value):
        '''
        Setter for the test_token property
        '''
        self._test_token = value
