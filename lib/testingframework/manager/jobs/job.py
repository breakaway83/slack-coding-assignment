'''
@author: Weimin Ma
@contact: U{weimin@sumologic.com<mailto:weimin@sumologic.com>}
@since: 2016-04-29
'''

from abc import abstractmethod
import time

from testingframework.manager.object import ItemFromManager
from testingframework.exceptions.wait import WaitTimedOut
from testingframework.exceptions.search import SearchFailure


class Job(ItemFromManager):
    '''
    Job handles the individual searches that spawn jobs. This manager has the
    ability to stop, pause, finalize, etc jobs. You can also retrieve
    different data about the job such as event count.
    '''

    _SECONDS_BETWEEN_JOB_IS_DONE_CHECKS = 1

    @abstractmethod
    def get_results(self, **kwargs):
        pass

    @abstractmethod
    def is_done(self):
        pass

    def wait(self, timeout=None):
        """
        Waits for this search to finish.

        @param timeout: The maximum time to wait in seconds. None or 0
                        means no limit, None is default.
        @type timeout: int
        @return: self
        @rtype: L{SDKJobWrapper}
        @raise WaitTimedOut: If the search isn't done after
                                  C{timeout} seconds.
        """
        self.logger.debug("Waiting for job to finish.")
        if timeout == 0:
            timeout = None

        self.start_time = time.time()
        while not self.is_done():
            _check_if_wait_has_timed_out(self.start_time, timeout)
            time.sleep(self._SECONDS_BETWEEN_JOB_IS_DONE_CHECKS)
        else:
            self.finish_wait_time = time.time()
        return self

    def wait_time_cost(self):
        if not self.start_time or not self.finish_wait_time:
            return None
        else:
            return self.finish_wait_time - self.start_time

    def check_message(self):
        if self.get_messages():
            message = self.get_messages()
            for key in message:
                if key == 'error':
                    raise SearchFailure(message[key])


def _check_if_wait_has_timed_out(start_time, timeout):
    if timeout is None:
        return
    if _wait_timed_out(start_time, timeout):
        raise WaitTimedOut(timeout)


def _wait_timed_out(start_time, timeout):
    return time.time() > start_time + timeout
