'''
@author: Weimin Ma
@contact: U{weimin@sumologic.com<mailto:weimin@sumologic.com>}
@since: 2011-11-23
'''
from abc import ABCMeta

from testingframework.log import Logging


class Manager(Logging):
    __metaclass__ = ABCMeta

    def __init__(self, connector):
        self._connector = connector

        Logging.__init__(self)

    @property
    def connector(self):
        return self._connector
