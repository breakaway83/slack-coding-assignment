'''
Created on May 10, 2016

@author: weimin
'''

#if __name__ == '__main__':
#    pass


class UnfinishedClassInterrupt(NotImplementedError):
    pass


def unfinished(cls):
    raise UnfinishedClassInterrupt("%s is unfinished and should not be used" %
                                   cls)
