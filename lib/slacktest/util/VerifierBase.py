from testingframework.log import Logging

class VerifierBase(object):
    """
    Base class to verify stuff in your tests
    """

    def __init__(self, name='verifier'):
        logging = Logging(name)
        self.logger = logging.logger
        self.logger.info("VerifierBase")

    def fail(self, msg=''):
        '''
        Fail this test.

        @type msg: string
        @param msg: The message to fail with.

        >>> v = VerifierBase()
        >>> v.fail('test failed')
        Traceback (most recent call last):
        AssertionError: test failed
        '''
        self.logger.error('%s ==> FAIL' % msg)
        raise AssertionError(msg)

    def verify_true(self, expression, msg='', verbose=True):
        '''
        Verify the expression evaluates to true.
        Fails the test if it does not.

        @type expression: bool
        @param expression: The expression to evaluate
        @type msg: string
        @param msg: A message describing this verification

        >>> v = VerifierBase()
        >>> v.verify_true(False, 'test failed')
        Traceback (most recent call last):
        AssertionError: test failed
        '''
        if not expression:
            self.fail(msg)
        if verbose:
            self.logger.info('%s ==> PASS' % msg)
        return True

    def matchDict(self, original, target):
        '''
        Match name-value pair with JSON output_mode dictionary
        @type original: dict
        @param original: JSON output dictionary
        @type target: str
        @param target: name to be matched
        @return: True or False
        '''

        if target in original.keys():
            return True

        for key in original.keys():
            val = original[key]
            if type(val) == dict:
                return self.matchDict(val, target)
            elif type(val) == list:
                if type(val[0]) == dict:
                    return self.matchDict(val[0], target)
                else:
                    return val[0] == target
        return False

    def verify_false(self, expression, msg='', verbose=True):
        '''
        Verify the expression evaluates to false.
        Fails the test if it does not.

        @type expression: bool
        @param expression: The expression to evaluate
        @type msg: string
        @param msg: A message describing this verification

        >>> v = VerifierBase()
        >>> v.verify_false(True, 'test failed')
        Traceback (most recent call last):
        AssertionError: test failed
        '''
        if expression:
            self.fail(msg)
        if verbose:
            self.logger.info('%s ==> PASS' % msg)
        return True

    def verify_equals(self, actual, expected, msg='', verbose=True):
        '''
        Verify that 2 objects are equal

        @type actual: object
        @param actual: One object to evaluate against
        @type expected: object
        @param expected: The other object to evaluate against
        @type msg: string
        @param msg: A message describing this verification

        >>> v = VerifierBase()
        >>> v.verify_equals(1, 2, 'test failed')
        Traceback (most recent call last):
        AssertionError: Verify: <1> = <2> (test failed)
        '''

        logmsg = 'Verify: <%s> = <%s>' % (actual, expected)
        if msg:
            logmsg += ' (%s)' % msg
        if actual != expected:
            self.fail(logmsg)
        if verbose:
            logmsg += ' ==> PASS'
            self.logger.info(logmsg)
        return True

    def verify_not_equals(self, actual, expected, msg='', verbose=True):
        '''
        Verify that 2 objects are not equal

        @type actual: object
        @param actual: One object to evaluate against
        @type expected: object
        @param expected: The other object to evaluate against
        @type msg: string
        @param msg: A message describing this verification

        >>> v = VerifierBase()
        >>> v.verify_not_equals(1, 1, 'test failed')
        Traceback (most recent call last):
        AssertionError: Verify: <1> != <1> (test failed)
        '''

        logmsg = 'Verify: <%s> != <%s>' % (actual, expected)
        if msg:
            logmsg += ' (%s)' % msg
        if actual == expected:
            self.fail(logmsg)
        if verbose:
            logmsg += ' ==> PASS'
            self.logger.info(logmsg)
        return True

    def verify_in(self, obj1, obj2, msg='', verbose=True):
        '''
        Verify that the obj1 is in the obj2. 
         - equivalent to: return bool(<obj1> in <obj2>)

        @type obj1: object
        @param obj1: One object to evaluate if it's in another
        @type obj2: object
        @param obj2: The other object to evaluate if 
                          it contains the other
        @type msg: string
        @param msg: A message describing this verification

        >>> veribase = VerifierBase()
        >>> veribase.verify_in('a', 'abc', )
        >>> veribase.verify_in('abc', 'fooabdbar', 'test failed')
        Traceback (most recent call last):
        AssertionError: Verify: <abc> in <fooabdbar> (test failed)
        '''
        logmsg = "Verify: <{i}> in <{c}>".format(i=obj1, c=obj2)
        if msg:
            logmsg += ' ({msg})'.format(msg=msg)
        if obj1 not in obj2:
            self.fail(logmsg)
        if verbose:
            logmsg += ' ==> PASS'
            self.logger.info(logmsg)
        return True

    def verify_not_in(self, obj1, obj2, msg='', verbose=True):
        '''
        Verify that the obj1 is not in the obj2. 
         - equivalent to: return bool(<obj1> in <obj2>)

        @type obj1: object
        @param obj1: One object to evaluate if it's in another
        @type obj2: object
        @param obj2: The other object to evaluate if 
                          it contains the other
        @type msg: string
        @param msg: A message describing this verification

        >>> veribase = VerifierBase()
        >>> veribase.verify_not_in('d', 'abc', )
        >>> veribase.verify_not_in('foo', 'fooabdbar', 'test failed')
        Traceback (most recent call last):
        AssertionError: Verify: <abc> not in <fooabdbar> (test failed)
        '''
        logmsg = "Verify: <{i}> not in <{c}>".format(i=obj1, c=obj2)
        if msg:
            logmsg += ' ({msg})'.format(msg=msg)
        if obj1 in obj2:
            self.fail(logmsg)
        if verbose:
            logmsg += ' ==> PASS'
            self.logger.info(logmsg)
        return True

if __name__ == "__main__":

    import doctest
    doctest.testmod()
