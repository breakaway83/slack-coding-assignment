'''
@author: Weimin Ma
@contact: U{weimin@sumologic.com<mailto:weimin@sumologic.com>}
@since: 2016-04-29
'''
from abc import abstractmethod

from testingframework.misc.collection import Collection
from testingframework.misc.manager_utils import create_wrapper_from_connector_mapping
from testingframework.manager import Manager


class Jobs(Manager, Collection):
    '''
    Jobs is the manager that handles searches.
    It does not handle pausing, resuming, etc of individual searches, it just
    spawns and lists searches.
    '''
    def __init__(self, connector):
        Manager.__init__(self, connector)
        Collection.__init__(self)

    def __new__(cls, connector):
        mappings = _CONNECTOR_TO_WRAPPER_MAPPINGS
        return create_wrapper_from_connector_mapping(cls, connector, mappings)

    @abstractmethod
    def create(self, query, **kwargs):
        pass

    @abstractmethod
    def __getitem__(self, sid):
        pass


class JobNotFound(RuntimeError):
    def __init__(self, sid):
        self.sid = sid
        super(JobNotFound, self).__init__(self._error_message)

    @property
    def _error_message(self):
        return 'Could not find a job with SID {sid}'.format(sid=self.sid)
