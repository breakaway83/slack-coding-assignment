"""
Contains various file utility methods.

@author: Weimin Ma
@contact: U{wma.utd@gmail.com<mailto:wma.utd@gmail.com>}
@since: 2016-10-18
"""
import platform
import os
import stat
import binascii
import re
import shutil
from testingframework.log import Logging
from testingframework.util.basefileutils import BaseFileUtils

_BLOCK_SIZE = 8192


class FileUtils(BaseFileUtils):

    def isfile(self, path):
        '''
        Checks if the given path represents a file.
        @param path: The absolute path to check
        @rtype path: str
        @return: True if the path points to a file.
        @rtype: bool
        '''
        return os.path.isfile(path)

    def isdir(self, path):
        """
        Checks if the giving path represents a directory.
        @param path: The absolute path to check
        @type path: str
        @return: True if the path points to a directory.
        @rtype: bool
        """
        return os.path.isdir(path)


    @staticmethod
    def cygwinizePath(self, path):
        """
        SSH needs path to be in linux format (ALso, It won't accept C: in the path). So this method converts windows path into cygwin's equivalent.
        """
        path = path.replace("\\", "/")   
        if ':' in path:
            list=path.split(":")
            path='/cygdrive/'+list[0]+list[1]
        return path

    def delete_file(self, file):
        '''
        '''
        if self.isfile(file):
            os.remove(file)
        else:
            raise Exception('File {f} not found. Check if the file exists.'.format(f=file))
    
    def get_file_contents(self, path):
        '''
        Get the contents of the file.
        '''
        if self.isfile(path):
            return open(path, 'r').read()
        else:
            raise Exception('File {file} Not Found'.format(file=path))

    def copy_file(self, source, target):
        """
        Copies the file at source to target
        @param source: Source file that needs to be copied.
        @type source: str
        @param target: Target file or directory
        @type target: str
        """
        if self.isfile(source):
            shutil.copy(source, target)
        else:
            raise Exception('Source file {file} not found'.format(file=source))

    def move_file(self, source, target):
        '''
        Moves the source file to the target location <directory or file>
        If the target location is a directory, then source file is moved into directory. Otherwise, target file is overwritten.
        @param source: Source file that needs to be moved
        @param target: Destination directory or file.
        '''
        if self.isfile(source):
            shutil.move(source, target)
        else:
            raise Exception('Source file {f} not present. Check if the file exists.'.format(f=source))

    def copy_directory(self, source, target, ignore=None):
        """
        Copies the directory at source to target by calling copy_file

        This method uses iteration rather than recursion.

        This metod exists to be able to use copy_file which doesn't copy
        metadata except the executable bit.

        If the target directory already exists the source will be merged with the
        target

        @type source: str
        @param source: The source folder

        @type target: str
        @param target: The target folder
        """
        dirs = [(source, target)]

        ignores = [re.compile(name) for name in ignore or []]

        while len(dirs) > 0:
            (source, target) = dirs.pop(0)

            if not os.path.exists(target):
                os.makedirs(target)
            for entry in os.listdir(source):
                source_entry = os.path.join(source, entry)
                target_entry = os.path.join(target, entry)

                skip = False
                for ignore in ignores:
                    if ignore.search(source_entry):
                        skip = True
                        break

                if skip:
                    continue

                if self.isdir(source_entry):
                    dirs.append((source_entry, target_entry))
                else:
                    self.copy_file(source_entry, target_entry)

    
    def move_directory(self, source, target, ignore=None):
        self.copy_directory(source, target, ignore=ignore)
        self.force_remove_directory(source)

    def compare_files(self, file1, file2):
        """
        Compare file1 and file2 by comparing their hashes.

        @type file1: str
        @param file1: The path to the first file

        @type file2: str
        @param file2: The path to the second file

        @rtype: boolean
        @return: True if they have the same contents, False otherwise.
        """
        hash1 = self.get_crc32(file1)
        hash2 = self.get_crc32(file2)
        return hash1 == hash2


    def get_crc32(self, path):
        """
        Calculate the crc32 for the specified file.

        @type path: str
        @param path: The path to the file the check
        @rtype: int
        @return: The crc32 sum for the file
        """
        crc = 0
        with open(path, "rb") as fp:
            block = fp.read(_BLOCK_SIZE)
            while block != '':
                crc = binascii.crc32(block, crc) & 0xffffffff
                block = fp.read(_BLOCK_SIZE)
        return crc


    def force_move_directory(self, source, target):
        '''
        Moves the source directory to the target directory.

        If target does not exist it is created using C{os.makedirs}.

        If the target does exist the source and target directories will be merged.

        Any existing files will be overwritten even if they are read only.

        @param source: The source directory (must be an existing directory)
        @type source: str
        @param target: The target directory (does not have to exist)
        @type target: src
        '''
        self.force_copy_directory(source, target)
        self.force_remove_directory(source)


    def force_copy_directory(self, source, target):
        '''
        Copies the source directory to the target directory.

        If target does not exist it is created using C{os.makedirs}.

        If the target does exist the source and target directories will be merged.

        Any existing files will be overwritten even if they are read only.

        @param source: The source directory (must be an existing directory)
        @type source: str
        @param target: The target directory (does not have to exist)
        @type target: src
        '''
        if not os.path.exists(target):
            os.makedirs(target)
        else:
            self._make_files_writable_if_exists(target)
        for source_entry, target_entry in self._directory_entries(source, target):
            if os.path.isdir(source_entry):
                self.force_copy_directory(source_entry, target_entry)
            else:
                self.force_copy_file(source_entry, target_entry)
        self._copy_file_permissions(source, target)


    def _clone_directory(self, source, target):
        '''
        Clones the source directory to the target directory.
        This clones all the permissions.

        If the target does not exist it will be created.

        @param source: The source directory (must exist)
        @type source: src
        @param target: The target directory (does not have to exist)
        @type target: src
        '''
        if not os.path.exists(target):
            os.makedirs(target)
        self._copy_file_permissions(source, target)


    def _copy_file_permissions(self, source, target):
        '''
        Copies the permissions from the source file/directory to the target
        file/directory.

        Uses C{shutil.copystat}

        @param source: The source directory (must be an existing directory)
        @type source: str
        @param target: The target directory (must be an existing directory)
        @type target: src
        '''
        shutil.copystat(source, target)


    def _directory_entries(self, source, target):
        '''
        Returns a generator that will over all the entries in a directory
        (not . or ..).

        Each iteration yields a tuple containing (source_entry, target_entry).
        The source/target will be appended to the entry.

        @param source: The source directory (must exist).
        @type source: str
        @param target: The target directory
        @type target: str
        @return: A generator that iterates over the entries.
        @rtype: generator
        '''
        for entry in os.listdir(source):
            yield (os.path.join(source, entry), os.path.join(target, entry))


    def force_copy_file(self, source, target):
        '''
        Moves the source file to the target file overwriting any existing file.

        The target file will first be made writable if it exists so that it can
        be overwritten..

        @param source: The path to the source file.
        @type source: str
        @param target: The path to the target file.
        @type target: str
        '''
        self._make_files_writable_if_exists(target)
        shutil.copy2(source, target)


    def force_move_file(self, source, target):
        '''
        Moves the source file to the target file overwriting any existing file.

        The target file will first be made writable if it exists so that it can
        be overwritten..

        @param source: The path to the source file.
        @type source: str
        @param target: The path to the target file.
        @type target: str
        '''
        self._make_files_writable_if_exists(target)
        shutil.move(source, target)


    def _make_files_writable_if_exists(self, *files):
        '''
        Tries to make the specified files writable if possible (failing if not).

        If a file does not exist it will be skipped.

        @param files: The file to make writable.
        '''
        for file_ in files:
            if os.path.exists(file_):
                os.chmod(file_, 0777)

    def force_remove_directory(self, path):
        '''
        Forcefully remove the directory.

        If the directory doesn't exist nothing is done.

        This is equivalent to C{rm -rf}

        @param directory: The directory to remove
        @type directory: str
        '''
        if os.path.exists(path):
            self._recursivly_remove_directory(path)


    def _recursivly_remove_directory(self, directory):
        '''
        Recursively remove a directory.

        @param directory: The directory to remove.
        @type directory: str
        '''
        for entry in os.listdir(directory):
            entry = os.path.join(directory, entry)
            if os.path.isdir(entry):
                self._make_files_writable_if_exists(entry)
                self._recursivly_remove_directory(entry)
            else:
                self.force_remove_file(entry)

        os.rmdir(directory)


    def force_remove_file(self, path):
        '''
        Attempts to remove the specified file.

        It tries to make the file writable before removing it.

        @param file_: The file to remove
        @type file_: str
        '''
        try:
            self._make_files_writable_if_exists(path)
        except Exception:
            pass
        os.remove(path)
