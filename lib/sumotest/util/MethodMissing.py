"""
Meta
====
    $Id$
    $DateTime$
    $Author$
    $Change$
"""

import logging


class MethodMissing(object):
    """
    A Python version of Ruby's method_missing function.
    Ruby is so much cleaner :)

    Found online at http://log.chemica.co.uk/?cat=12
    """
    def __init__(self):
        '''
        Init
        '''
        self.logger = logging.getLogger('MethodMissing')

    def method_missing(self, attr, *args, **kwargs):
        """
        Stub: override this function
        """
        raise NotImplementedError(
            "Missing method '{s}' called.".format(s=attr))

    def __getattr__(self, attr):
        '''
        Returns a function def 'callable' that wraps method_missing
        '''
        if not hasattr(attr, '__call__'):
            # self.logger.info("no call in method missing")
            return self.method_missing(attr)

        def callable(*args, **kwargs):
            '''
            Returns a method that will be calling an overloaded method_missing
            '''
            return self.method_missing(attr, *args, **kwargs)
        return callable
