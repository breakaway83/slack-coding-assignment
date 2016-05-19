import tarfile
import zipfile
import gzip
import os
import logging
import copy
import subprocess

_BLOCK_SIZE = 8192
"""
How many bytes to read per iteration
"""

_LOGGER_NAME = 'archiver'
"""
The name of the logger
"""


def get_archive_types():
    """
    Returns the supported archive types

    @rtype: list
    @return: The valid archive types
    """
    ret = []
    for types in [_SINGLE_FORMATS, _PACKAGE_FORMATS]:
        ret.extend(types.keys())
    return ret


def get_single_file_types():
    """
    Returns the supported single file archive types

    @rtype: list
    @return: The valid archive types
    """
    return copy.copy(_SINGLE_FORMATS.keys())


def get_package_types():
    """
    Returns the supported multi file archive types

    @rtype: list
    @return: The valid archive types
    """
    return copy.copy(_PACKAGE_FORMATS.keys())


def get_extensions(archive_type=None):
    """
    Returns the valid extensions for the specified archive type.

    If type is None all valid extensions are returned

    @type archive_type: str
    @param archive_type: The archive type

    @rtype: list
    @return: The valid extensions
    """
    if archive_type in _PACKAGE_FORMATS:
        return copy.copy(_PACKAGE_FORMATS[archive_type]['extensions'])
    elif archive_type in _SINGLE_FORMATS:
        return copy.copy(_SINGLE_FORMATS[archive_type]['extensions'])
    elif archive_type is None:
        exts = []
        for types in [_SINGLE_FORMATS, _PACKAGE_FORMATS]:
            for value in types.values():
                exts.extend(value['extensions'])
        return exts
    else:
        return None


def get_single_file_extensions():
    """
    Returns the valid extensions for single file archives

    @rtype: list
    @return: The valid extensions
    """
    exts = []
    for value in _SINGLE_FORMATS.values():
        exts.extend(value['extensions'])
    return exts


def get_package_extensions():
    """
    Returns the valid extensions for multi file archives

    @rtype: list
    @return: The valid extensions
    """
    exts = []
    for value in _PACKAGE_FORMATS.values():
        exts.extend(value['extensions'])
    return exts


def create(*sources, **kwargs):
    """
    create(sources, ..., output=None, archive_type=None)

    Creates an archive using the specified input files/directories.

    If output is not set the[0] filename + archive extension is used.
    If output is a directory the[0] filename + archive extension is appended
    to the directory.

    If archive_type is not set it's guessed from the file name,
    if that doesn't work gztar is used.

    When gzipping or bzipping multiple files output needs to be None or a
    directory, not a file.

    If format is zip or a tarball (any compression) a file can be a tuple.
    ('foo', 'bar') means add the file 'foo' with the name 'bar'

    Examples:

    All examples have cwd set to /home

    Creates a zip file named foo.txt.zip

    >>> archiver.create('foo.txt')
    [(['foo.txt'], '/home/foo.txt.zip'])

    Creates a gzipped taball named foo.tgz

    >>> archiver.create('foo.txt', output='foo.tgz')
    [(['foo.txt'], '/home/foo.tgz')]

    Creates a bzipped taball named foo.tbz

    >>> archiver.create('foo.txt', output='foo.tbz')
    [(['foo.txt'], '/home/foo.tbz')]

    Creates a gzipped file named foo.txt.gz

    >>> archiver.create('foo.txt', archive_type='gzip')
    [(['foo.txt'], /home/foo.txt.gz')]

    Creates an archive containing foo.txt and bar.dat

    >>> archiver.create('foo.txt', 'bar.dat', '/tmp/archiver.zip')
    [(['foo.txt', 'bar.dat'], '/tmp/archiver.zip')]

    Gzipps foo.txt and bar.dat

    >>> archiver.create('foo.txt', 'bar.dat', output='/tmp', archive_type='gzip')
    [(['/tmp/foo.txt.gz'], foo.txt), (['bar.dat'], '/tmp/bar.dat.gz')]

    The default extension will always be added if missing

    >>> archiver.create('foo.txt', output='/tmp/foo.some.ext', archive_type='gzip')
    [(['foo.txt'], '/tmp/foo.some.ext.gz')]

    Add files from array

    >>> files = ['foo.txt', 'bar.dat']
    >>> archiver.create(*files)
    [(['foo.txt', 'bar.dat'], '/home/foo.txt.zip')]

    Add a file with an alternative name

    >>> archiver.create(('foo.txt', 'bar.txt'))
    [([('foo.txt', 'bar.txt')], '/home/foo.txt.zip'] #foo.txt.zip will contain only 'bar.txt'

    @param sources: The sources to add. Supplied by positional arguments.
                    When using a single file archive inputs can only contain
                    files, not directories.
                    Each element in sources can either be a str or a tuple,
                    if a tuple the second argument is the added name.

    @type output: str
    @param output: The output file/directory. If output is a directory
                   a filename will be appended. When gzipping or bzipping
                   multiple files output must be a directory.
                   If output is missing a valid extension for the specified
                   archive one will be added.

    @type archive_type: str
    @param archive_type: Which format the archive should have. If left to
                         None it's guessed from the filename.
                         If this fails zip is used.

    @rtype: list(tuple(list(str or tuple), str))
    @return: The following is returned: [(sources, output), ...]
    """
    logger = logging.getLogger(_LOGGER_NAME)

    atype = kwargs.setdefault('archive_type', None)
    output = kwargs.setdefault('output', None)

    del kwargs['archive_type']
    del kwargs['output']

    for key in kwargs.keys():
        err = 'Unknown keyword argument {0}'.format(key)
        logger.error(key)
        raise KeyError(err)

    atype = atype or get_archive_type(output)
    atype = atype or 'zip'

    types = dict(_PACKAGE_FORMATS.items() + _SINGLE_FORMATS.items())
    if atype in types:
        ainfo = types[atype]
    else:
        err = 'Unknown archive type {0}'.format(atype)
        logger.error(err)
        raise ValueError(err)

    if len(sources) == 0:
        err = 'Cannot create archive with no source'
        logger.error(err)
        raise ValueError(err)

    single = atype in _SINGLE_FORMATS

    for source in sources:
        if isinstance(source, tuple):
            source = source[0]

        if not os.path.exists(source):
            err = "Input source {0} doesn't exist".format(source)
            logger.error(err)
            raise Exception(err)

        if single and not os.path.isfile(source):
            err = "Archive type {0} only handles files as input".format(atype)
            logger.error(err)
            raise Exception(err)

    if single and len(sources) > 1 and not os.path.isdir(output or ''):
        err = 'Output must be a directory or None when using multiple files ' \
              'with single file archives'.format(atype)
        logger.error(err)
        raise ValueError(err)

    archives = ainfo['creator'](sources, output, atype)
    logger.info('Created archives {0}'.format(archives))
    return archives


def extract(source, output=None, archive_type=None):
    """
    Extract the specified source to the output.

    Currently it handles tarballs (uncompressed, gzip or bzip2), zip
    bzip2 and gzip

    Examples:

    All of these examples assumes your cwd is /home

    >>> archiver.extract('/tmp/foo.zip')
    ('/tmp/foo.zip', '/home')

    >>> archiver.extract('/tmp/foo.txt.gz')
    ('/home/foo.txt', '/home/foo.txt')

    >>> archiver.extract('/tmp/bar.tgz', output='/opt')
    ('/tmp/bar.tgz', '/opt')

    >>> archiver.extract('/tmp/bar', output='/opt', archive_type='bzip2')
    ('/tmp/bar', '/opt/bar')

    >>> archiver.extract('/tmp/foo.gz', output='/opt/foo.txt')
    ('/tmp/foo.gz', '/opt/foo.txt')


    @type source: str
    @param source: The source file, must be a valid archiver.

    @type output: str
    @param output: The place to extract to. If left unspecified
                   the output will be the current directory for
                   archives that contain files and a file without
                   the extension in the cwd for archives that contain
                   data (gzip, bzip etc). See examples

    @type archive_type: str
    @param archive_type: Which type the archive has, if left unspecified
                           the type is guessed from the source.
                           The type must be one of the types on ARCHIVE_FORMATS

    @rtype: str
    @return: The absolute path to the output directory/file
    """
    logger = logging.getLogger(_LOGGER_NAME)
    types = dict(_PACKAGE_FORMATS.items() + _SINGLE_FORMATS.items())

    atype = archive_type
    if isinstance(source, tuple):
        (source, atype) = source

        if not atype in types:
            err = "Unknown archive type {0}"
            logger.error(err)
            raise ValueError(err)
    else:
        atype = get_archive_type(source)
        if not atype:
            err = "I don't know how to extract {0}"
            err = err.format(os.path.basename(source))
            logger.error(err)
            raise ValueError(err)

    if not os.path.isfile(source):
        err = 'No such file: {0}'.format(source)
        logger.error(err)
        raise Exception(err)

    extracted = types[atype]['extractor'](source, output, atype)

    logger.info('Extracted archive {0}'.format(extracted))
    return extracted


def is_archive(source, check_exists=False):
    """
    Checks if source is an archive by checking its extension.

    @type source: str
    @param source: The file to check

    @rtype: bool
    @return: True if source has a known archive extension
    """
    return get_archive_type(source, check_exists) is not None


def get_archive_type(source, check_exists=False):
    """
    Returns which type or archive the source is.

    @type source: str
    @param source: The file to get the type for

    @rtype: str
    @return: The archive type or None if it's not a known archive
    """
    if source is None:
        return None

    if check_exists and not os.path.isfile(source):
        return None

    for formats in [_PACKAGE_FORMATS, _SINGLE_FORMATS]:
        for (key, value) in formats.items():
            if _has_extension(source, value['extensions']):
                return key

    return None


def _has_extension(path, extensions):
    """
    Returns True if str has any of the extensions
    in the extensions array

    Examples:

    >>> _has_extension('foo.bar', ['foo', 'bar', 'baz'])
    True
    >>> _has_extension('foo.bar', ['foo', 'baz'])
    False

    @type path: str
    @param path: The file name (abs or relative doesn't matter)

    @type extensions: list
    @param extensions: A list of possible extensions (no starting .)

    @rtype: bool
    @return: True if str ends with one the extensions
    """
    for ext in extensions:
        if path.endswith('.' + ext):
            return True
    return False


def _get_compressed_filename(source, output, atype):
    """
    Guesses the name of the output archive using format and source.

    @type source: str
    @param source: The source file

    @type output: str
    @param output: The output output. Can be None

    @type atype: str
    @param atype: The archive format

    @rtype: str
    @return: The path to a file where the archive should be.
    """
    types = dict(_PACKAGE_FORMATS.items() + _SINGLE_FORMATS.items())
    exts = types[atype]['extensions']

    # If output is not set or output is a directory
    if output is None or os.path.isdir(output):
        if isinstance(source, tuple):
            source = source[0]

        filename = os.path.basename(os.path.normpath(source))
        output = os.path.join(output or '', filename)

    if not _has_extension(output, exts):
        output = '{0}.{1}'.format(output, exts[0])

    return os.path.realpath(output)


def _get_uncompressed_filename(source, output, atype):
    """
    Guesses the output from source.

    If the output is a directory the sourcename (without extension)
    is appended.

    @type source: str
    @param source: The source archive

    @type output: str
    @param output: The output file/directory or None

    @rtype: str
    @return: The fixed filename
    """
    filename = os.path.basename(source)

    types = dict(_PACKAGE_FORMATS.items() + _SINGLE_FORMATS.items())
    for ext in types[atype]['extensions']:
        if filename.endswith('.' + ext):
            filename = filename[:-len(ext) - 1]
            break

    if output is None:
        output = filename
    elif os.path.isdir(output):
        output = os.path.join(output, filename)

    return os.path.realpath(output)


def _copy_fd(source, output_path):
    """
    Copies the data from the source file
    to the output_path.

    source is not closed when done.

    @type source: file
    @param source: The source file

    @type output_path: str
    @param output_path: The path to the output file.
                        If it exists it will be overwritten.
    """
    with open(output_path, 'w+b') as output:
        block = source.read(_BLOCK_SIZE)

        while block:
            output.write(block)
            block = source.read(_BLOCK_SIZE)


def _filename_without_extension(path):
    """
    Returns the filename without the extension.

    Examples:

    >>> _filename_without_extension('/foo/bar/baz.zip')
    'baz'

    >>> _filename_without_extension('/foo/bar/baz')
    'baz'

    @type path: str
    @param path: The path to the file

    @rtype: str
    @return: The filename without extension
    """
    return os.path.splitext(os.path.basename(path))[0]


def _compress_files(sources, output, atype, opener, adder):
    """
    Compresses the specified sources to a single archive.

    @type sources: iterable(tuple or str)
    @param sources: The input sources

    @type output: str
    @param output: The output file/directory or None

    @type atype: str
    @param atype: The archive type

    @type opener: function(str, str)
    @param opener: This function should open the specified file with the
                   the specified mode (source, mode)

    @type adder: function(file, str, str)
    @param adder: Should add the 'source' to 'file' with 'name'
                  (file, source, name)

    @rtype: list(tuple(list(str or tuple), str))
    @return: Returns [(list(sources), output)]
    """
    output = _get_compressed_filename(sources[0], output, atype)

    arch = opener(output, 'w')
    for source in sources:
        if isinstance(source, tuple):
            (source, name) = source
        else:
            name = None

        adder(arch, source, name)

    arch.close()
    return [(list(sources), output)]


def _compress_single_files(sources, output, atype, opener):
    """
    Compresses the specified sources to multiple, single file, archives.

    @type sources: iterable(tuple or str)
    @param sources: The input sources

    @type output: str
    @param output: The output file/directory or None

    @type atype: str
    @param atype: The archive type

    @type opener: function(str, str)
    @param opener: This function should open the specified file with the
                   the specified mode (source, mode)

    @rtype: list(tuple(list(str or tuple), str))
    @return: Returns [(list(sources), output)]
    """
    archives = []
    for source in sources:

        if isinstance(source, tuple):
            (source, output) = source
            output = os.path.realpath(output)

        output = _get_compressed_filename(source, output, atype)

        archives.append(([source], output))

        source_file = open(source, 'rb')
        output_file = opener(output, 'w')
        data = source_file.read(_BLOCK_SIZE)
        while data:
            output_file.write(data)
            data = source_file.read(_BLOCK_SIZE)

        output_file.close()
        source_file.close()

    return archives


def _create_gzip(sources, output, atype):
    """
    Creates a gzip archive. NOT TO BE CALLED MANUALLY

    @param sources: The input sources
    @type sources: list
    @param output: The output file or directory
    @type output: str
    @param atype: The archive type
    @type atype: str
    """
    return _compress_single_files(sources, output, atype, gzip.open)


def _create_zip(sources, output, atype):
    """
    Creates a zip archive. NOT TO BE CALLED MANUALLY

    @param sources: The input sources
    @type sources: list
    @param output: The output file or directory
    @type output: str
    @param atype: The archive type
    @type atype: str
    """
    adder = lambda output, source, name: output.write(source, name)
    return _compress_files(sources, output, atype, zipfile.ZipFile, adder)


def _create_tar(sources, output, atype):
    """
    Creates a tar archive. NOT TO BE CALLED MANUALLY

    @param sources: The input sources
    @type sources: list
    @param output: The output file or directory
    @type output: str
    @param atype: The archive type
    @type atype: str
    """

    opener = lambda a, b: tarfile.open(a, '{0}:{1}'.format(b,
                                                           _TAR_MODES[atype]))
    adder = lambda output, source, name: output.add(source, name)
    return _compress_files(sources, output, atype, opener, adder)


def _create_gtar(sources, output, atype):
    """
    Creates a Solaris tar archive. NOT TO BE CALLED MANUALLY

    @param sources: The input sources
    @type sources: list
    @param output: The output file or directory
    @type output: str
    @param atype: The archive type, i.e. 'gtar'
    @type atype: str
    """

    r = _create_tar(sources, output, 'tar')
    compressor = lambda b: subprocess.call(['compress', b])
    compressor(r[0][1])
    return [(r[0][0], "%s%s" % (r[0][1], '.Z'))]


def _extract_zip(source, output, _atype):
    """
    Extracts a Zip archive. NOT TO BE CALLED MANUALLY

    @param source: The source file
    @type source: str
    @param output: The output file or directory
    @type output: str
    @param _atype: The archive type
    @type _atype: str
    """
    output = output or '.'
    with zipfile.ZipFile(source) as zip_file:
        zip_file.extractall(output or '.')
    return (source, output)


def _extract_tar(source, output, atype):
    """
    Extracts a tar archive. NOT TO BE CALLED MANUALLY

    @param source: The source file
    @type source: str
    @param output: The output file or directory
    @type output: str
    @param atype: The archive type
    @type atype: str
    """
    output = output or '.'
    tar = tarfile.open(source, 'r:{0}'.format(_TAR_MODES[atype]))
    tar.extractall(output)
    tar.close()
    return (source, output)


def _extract_gzip(source, output, atype):
    """
    Extracts a gzip archive. NOT TO BE CALLED MANUALLY

    @param source: The source file
    @type source: str
    @param output: The output file or directory
    @type output: str
    @param atype: The archive type
    @type atype: str
    """
    output = _get_uncompressed_filename(source, output, atype)
    with gzip.GzipFile(source, 'r') as source_file:
        _copy_fd(source_file, output)
    return (source, output)


def _extract_gtar(source, output, atype):
    """
    Extracts a Solaris .Z archive. NOT TO BE CALLED MANUALLY

    @param source: The source file
    @type source: str
    @param output: The output file or directory
    @type output: str
    @param atype: The archive type
    @type atype: str
    """
    output = output or '.'
    if os.path.exists('/usr/sfw/bin/gtar'):
        GTAR = '/usr/sfw/bin/gtar'
    elif os.path.exists('/usr/bin/gtar'):
        GTAR = '/usr/bin/gtar'
    else:
        GTAR = 'gtar'
    p = subprocess.Popen([GTAR, '-C', output, '-xzf', source])
    p.communicate()
    return (source, output)

_TAR_MODES = {
    'tar': '',
    'gztar': 'gz',
    'gtar': 'gtar',
}

_PACKAGE_FORMATS = {
    # Zip file
    'zip': {
        'extensions': ['zip'],
        'creator': _create_zip,
        'extractor': _extract_zip,
    },
    # Uncompressed tar
    'tar': {
        'extensions': ['tar'],
        'creator': _create_tar,
        'extractor': _extract_tar,
    },
    # gzipped tar file
    'gztar': {
        'extensions': ['tgz', 'tar.gz', 'spl'],
        'creator': _create_tar,
        'extractor': _extract_tar,
    },
    # solaris tar file
    'gtar': {
        'extensions': ['Z'],
        'creator': _create_gtar,
        'extractor': _extract_gtar,
    }
}
"""
A dictionary of format: [extensions]
This dictionary only contains formats that can be used with multiple files.
"""

_SINGLE_FORMATS = {

    'gzip': {
        'extensions': ['gz', 'gzip'],
        'creator': _create_gzip,
        'extractor': _extract_gzip,
    },

    'gtar': {
        'extensions': ['Z'],
        'creator': _create_gtar,
        'extractor': _extract_gtar,
    }
}
"""
A dictionary of format: [extensions]
This dictionary only contains formats that can be used with a single file.
"""
