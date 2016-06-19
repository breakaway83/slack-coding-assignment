'''
Module for handling generic connections with a Sumo deployment.

@author: Weimin Ma
@contact: U{weimin@sumologic.com<mailto:weimin@sumologic.com>}
@since: 2016-04-23
'''

__all__ = ['rest', 'service']

from .rest import RESTConnector
from .service import ServiceConnector

