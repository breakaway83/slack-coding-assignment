'''
Module used for downloading collector builds.

@author: Weimin Ma
@contact: U{weimin@sumologic.com<mailto:weimin@sumologic.com>}
@since: 2016-05-23
'''

from .collector_package import COLLECTOR
from .collector_nightly import NightlyPackage
from .collector_release import ReleasedPackage

__all__ = ['collector_package', 'collector_nightly', 'collector_release']
