'''
@author: Weimin Ma
@contact: U{weimin@sumologic.com<mailto:weimin@sumologic.com>}
@since: 2011-11-23
'''
from testingframework.exceptions import UnsupportedConnectorError


def create_wrapper_from_connector_mapping(base_class, connector, mappings):
    wrapper = get_wrapper_class_from_connector_mapping(connector, mappings)
    return super(base_class, base_class).__new__(wrapper, connector)


def get_wrapper_class_from_connector_mapping(connector, mappings):
    cls = connector.__class__
    if cls not in mappings:
        raise UnsupportedConnectorError
    return mappings[cls]
