"""
Module for getting the test data.
ESNAS is being used at the moment but any FTP storage can be used.

@author: Nicklas Ansman-Giertz
@contact: U{ngiertz@splunk.com<mailto:ngiertz@splunk.com>}
@since: 2011-11-23
"""
import os
import logging
from ftplib import FTP

from helmut.util.fileutils import FileUtils

futils = FileUtils()

_LOGGER = logging.getLogger('filegetter')
"""
The logger we use
"""

FILES = {
    'host': 'esnas.splunk.com',
    'port': 21,
    'user': '',
    'passwd': '',
    'path': '/hellaspace/automated_test_data/{project}/{version}/',
    'filename': '{name}_{version}.tgz',

    'webintelligence': {
        'wi_test': {
            'original': {
                'crc32': 0x63c276b2,
                'db_creation': 1309412591,
            },
            '4.2.3_2011-08-29': {
                'crc32': 0x05a62a96,
                'db_creation': 1314630628,
            },
        },

        'wi_summary_daily': {
            'original': {
                'crc32': 0x58980622,
                'db_creation': 1310575450,
            },
            '4.2.3_2011-08-29': {
                'crc32': 0xc06f0c18,
                'db_creation': 1314630628,
            },
            '4.3_2011-10-11': {
                'crc32': 0x923e69af,
                'db_creation': 1317664814
            }
        },

        'wi_summary_hourly': {
            'original': {
                'crc32': 0xdcdb0cbf,
                'db_creation': 1310575450,
            },
            '4.2.3_2011-08-29': {
                'crc32': 0x0725f13e,
                'db_creation': 1314630628,
            },
            '4.3_2011-10-11': {
                'crc32': 0x39593da7,
                'db_creation': 1317664814
            }
        },

        'wi_summary_fivemin': {
            'original': {
                'crc32': 0x321037a2,
                'db_creation': 1310575450,
            },
            '4.2.3_2011-08-29': {
                'crc32': 0x28e6a33a,
                'db_creation': 1314630628,
            },
            '4.3_2011-10-11': {
                'crc32': 0x8ad75abe,
                'db_creation': 1317664814
            }
        },

        '10m.ldif': {
            'filename': '{name}',
            'unversioned': {
                'crc32': 0xa40b7853,
            }
        }
    },
}
"""
All the files that the FileGetter knows about.

The files are ordered into projects and versions.

The structure is this::
    <project_name>: {
       <file_name> : {
           <version-name>: {
               'crc32': 0xf00,
               ...
           }
       },
       ...
    },
    ...

The data about a file is 'crc32' which should be a crc32
hash of the file but also any extra data in whatever format
you want.

The settings can be overridden on a per project, per file and ber version
basis.

The path will escape {project}, {version} and {name}.
"""


def get_metadata(name, project=None, version=None):
    """
    Returns the data part of the file data.

    Will contain crc32 and any extras (if present)

    @type name: str
    @param name: The name of the file

    @type project: str
    @param project: The project, may be None

    @type version: str
    @param version: The version of the file, may be None

    @rtype: dict
    @return: The data for the file

    @raise Exception: on error
    """
    return _get_file_info(None, name, project, version)['data']


def file_needed(local_file, name=None, project=None, version=None):
    """
    Checks if the specified file needs to be downloaded.

    It does this by comparing crc32 hashes.

    See get_file for more info on the parameters

    @type local_file: str
    @param local_file: The file to check

    @type name: str
    @param name: The name of the file (in FILES)

    @type project: str
    @param project: The name of the project, may be None

    @type version: str
    @param version: The version of the file, may be None

    @rtype: bool
    @return: True if the file needs to be downloaded, False otherwise
    """

    file_info = _get_file_info(local_file, name, project, version)
    local_file = _get_local_file(local_file, file_info)
    return _file_needed(local_file, file_info)


def get_file(local_file, name=None, project=None, version=None, force=False):
    """
    Get the file via ftp.

    Unless force=True the file will only be downloaded if needed.

    @type local_file: str
    @param local_file: Path to where the file should exist locally, this can
                       be either a directory or a file, if it's a directory
                       the filename will be appended to it.
                       {name}, {project} and {version} will be replaced by the
                       actual values. See str.format for more info.

    @type name: str
    @param name: The name of the file to download, the name should come from
                 FILES. If None the file name will be the basename of local_file

    @type project: str
    @param project: The project name, may be None if the file does not belong to
                    a project.

    @type version: str
    @param version: Which version of the file to get, may be None if not
                    applicable.

    @type force: bool
    @param force: If True the file will be downloaded even if it's not needed.

    @rtype: str
    @return: The local file name (the escaped version)
    """

    file_info = _get_file_info(local_file, name, project, version)

    local_file = _get_local_file(local_file, file_info)

    if not force and not _file_needed(local_file, file_info):
        _LOGGER.info('File {0} matches checksum, skipping'.format(local_file))
        return local_file

    _LOGGER.info('Getting version {v} of file {f} from project {p}'.format(
        v=file_info['version'], f=file_info['name'], p=file_info['project']))

    try:
        with open(local_file, 'w+b') as file_pointer:
            ftp = FTP()
            ftp.connect(file_info['host'], file_info['port'])
            ftp.login(file_info['user'], file_info['passwd'])
            ftp.cwd(file_info['path'])
            ftp.retrbinary('RETR ' + file_info['filename'], file_pointer.write)
    except Exception:
        err = "Failed to get file {filename} from ftp://{host}:{port}{path}"
        err = err.format(filename=file_info['filename'], host=file_info['host'],
                         port=file_info['port'], path=file_info['path'])

        _LOGGER.exception(err)
        raise
    finally:
        if ftp:
            ftp.quit()

    _LOGGER.info("File {file} updated".format(file=local_file))

    return local_file


def _get_local_file(local_file, file_info):
    """
    Escapes {name}, {project} and {version} in the
    local file and if local file is a directory {name}
    is appended.

    @type local_file: str
    @param local_file: The user supplied path to the local file

    @type file_info: dict
    @param file_info: The dictionary returned from _get_file_info

    @rtype: str
    @return: The updated local file path
    """
    local_file = local_file.format(name=file_info['name'],
                                   version=file_info['version'],
                                   project=file_info['project'])

    if os.path.isdir(local_file):
        local_file = os.path.join(local_file, file_info['name'])

    return local_file


def _file_needed(local_file, data):
    """
    See file_needed

    @type local_file: str
    @param local_file: The file to check

    @type data: dict
    @param data: A dictionary returned from _get_file_info

    @rtype: bool
    @return: True if the file needs to be downloaded, False otherwise
    """
    if not os.path.exists(local_file):
        msg = "No file exists at {path}, need to update it"
        _LOGGER.info(msg.format(path=local_file))
        return True
    elif (futils.get_crc32(local_file) != data['data']['crc32']):
        msg = "File at {path} doesn't match the crc, need to update it"
        _LOGGER.info(msg.format(path=local_file))
        return True

    return False


def _find_value(key, dictionaries):
    """
    Finds the specified key in the specified list of dictionaries
    by iterating backwards over the list checking each dict.

    @type dictionaries: list of dictionaries
    @param dictionaries: The dictionaries to search in

    @type key: str
    @param key: The key to look for

    @return: The value for that key

    @raise KeyError: if it's not found
    """
    for dictionary in dictionaries:
        if key in dictionary:
            return dictionary[key]

    raise KeyError('Key {key} not found in the dictionaries'.format(key=key))


def _get_file_info(local_file, name, project, version):
    """
    Returns a dictionary with the following info::

        {
            name: The base name of the file
            project: The project name
            version: The version nae
            path: The path to directory where the file is on the server (the {} have been replaced)
            host: The hostname of the FTP server
            port: The port of the server
            user: The user of the server
            passwd: The password of the server
            filename: The name of file on the server (the {} have been replaced)
            data: Additional data such as crc32 and extras.
        }

    @type local_file: str
    @param local_file: The target file, may be None if name is not None

    @type name: str
    @param name: The name of the file in the array, may be None if local_file is
                 not none

    @type project: str
    @param project: The project name, may be None

    @type version: str
    @param version: The version of the file, may be None

    @rtype: dict
    @return: The data for the file (see above)

    @raise Exception: on error
    """
    project = project or 'common'
    name = name or os.path.basename(local_file or '')
    version = version or 'unversioned'

    if name == '':
        raise ValueError('Name cannot be empty')

    dictionary = FILES

    ret = {
        'path': dictionary['path'],
        'host': dictionary['host'],
        'port': dictionary['port'],
        'user': dictionary['user'],
        'passwd': dictionary['passwd'],
        'filename': dictionary['filename'],
    }

    try:
        dictionary = FILES[project]
        for key, value in ret.items():
            ret[key] = dictionary.get(key, value)

    except KeyError:
        raise ValueError('No project named "{0}"'.format(project))

    try:
        dictionary = dictionary[name]
        for key, value in ret.items():
            ret[key] = dictionary.get(key) or value
    except KeyError:
        raise ValueError('No file named "{0}"'.format(name))

    try:
        dictionary = dictionary[version]
        for key, value in ret.items():
            ret[key] = dictionary.get(key) or value
    except KeyError:
        raise ValueError('No version named "{0}"'.format(version))

    ret['name'] = name
    ret['project'] = project
    ret['version'] = version
    ret['data'] = dictionary
    ret['path'] = ret['path'].format(name=name, project=project,
                                     version=version)
    ret['filename'] = ret['filename'].format(name=name, project=project,
                                             version=version)
    return ret
