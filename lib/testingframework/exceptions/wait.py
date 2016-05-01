class WaitTimedOut(RuntimeError):
    '''
    This exception is raised when a designated wait period times out.
    '''
    def __init__(self, seconds_waited):
        self.seconds_waited = seconds_waited
        super(WaitTimedOut, self).__init__(self._error_message)

    @property
    def _error_message(self):
        message = 'Search was not done after {0} seconds'
        return message.format(self.seconds_waited)
