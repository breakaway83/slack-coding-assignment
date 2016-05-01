'''
Created on Oct 21, 2012

@author: parhamfh
'''

#if __name__ == '__main__':
#    pass


class UnfinishedClassInterrupt(NotImplementedError):
    pass


def unfinished(cls):
    raise UnfinishedClassInterrupt("%s is unfinished and should not be used" %
                                   cls)
