# This file is NOT licensed under the GPLv3, which is the license for the rest
# of YouCompleteMe.
#
# Here's the license text for this file:
#
# This is free and unencumbered software released into the public domain.
#
# Anyone is free to copy, modify, publish, use, compile, sell, or
# distribute this software, either in source code form or as a compiled
# binary, for any purpose, commercial or non-commercial, and by any
# means.
#
# In jurisdictions that recognize copyright laws, the author or authors
# of this software dedicate any and all copyright interest in the
# software to the public domain. We make this dedication for the benefit
# of the public at large and to the detriment of our heirs and
# successors. We intend this dedication to be an overt act of
# relinquishment in perpetuity of all present and future rights to this
# software under copyright law.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS BE LIABLE FOR ANY CLAIM, DAMAGES OR
# OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
# ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.
#
# For more information, please refer to <http://unlicense.org/>

'''
YouCompleteMe configuration file template to be used in 'YCM-Generator'.
'''

# Needed because ur"" syntax is no longer supported
from __future__ import unicode_literals

import glob
import os
import re
import subprocess
import ycm_core


# ========================== Configuration Options ============================
# Refer to the docstring of 'GuessBuildDirectory' function for further detail.
# This is an experimental feature.
GUESS_BUILD_DIRECTORY = False
# Refer to the docstring of 'GuessIncludeDirectory' function for further detail.
GUESS_INCLUDE_PATH = True
# ========================== Configuration Options ============================

# =========================== Constant Definitions ============================
# NOTE:
#
# 1. The string comparison in this configuration file is performed in a case
#    in-sensitive manner; for example, there is no difference between file
#    extensions of the following: '.cc' '.CC' '.Cc' 'cC'
#
# 2. One of the naming conventions for C++ header and source files involve the
#    use of uppercase '.H' and '.C' - this case is handled as if they are named
#    as '.h', and '.c', respectively.
SOURCE_EXTENSIONS = ('.cpp', '.cxx', '.cc', '.c', '.m', '.mm')
HEADER_EXTENSIONS = ('.h', '.hxx', '.hpp', '.hh')
# =========================== Constant Definitions ============================

flags = [
    # INSERT FLAGS HERE
]


def LoadSystemIncludes():
    '''
    Return a list of system include paths prefixed by '-isystem'.
    '''
    query = (
        r'(?:\#include \<...\> search starts here\:)'
        r'(?P<list>.*?)(?:End of search list)'
    )
    regex = re.compile(query, re.DOTALL)
    process = subprocess.Popen(['clang', '-v', '-E', '-x', 'c++', '-'],
                               stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
    process_out, process_err = process.communicate('')
    output = (process_out + process_err).decode('utf8')

    includes = []
    for p in re.search(regex, output).group('list').split('\n'):
        p = p.strip()
        if len(p) > 0 and p.find('(framework directory)') < 0:
            includes.append('-isystem')
            includes.append(p)
    return includes


def DirectoryOfThisScript():
    '''
    Return the absolute path of the parent directory containing this
    script.
    '''
    return os.path.dirname(os.path.abspath(__file__))


def GuessBuildDirectory():
    '''
    Guess the build directory using the following heuristics:

    1. Returns the current directory of this script plus 'build'
       subdirectory in absolute path if this subdirectory exists.

    2. Otherwise, probes whether there exists any directory
       containing 'compile_commands.json' file two levels above the current
       directory; returns this single directory only if there is one candidate.

    Raise 'OSError' if the two above fail.
    '''
    result = os.path.join(DirectoryOfThisScript(), 'build')

    if os.path.exists(result):
        return result

    result = glob.glob(os.path.join(DirectoryOfThisScript(),
                                    '..', '..', '*', 'compile_commands.json'))

    if not result:
        raise OSError('Build directory cannot be guessed.')

    if 1 != len(result):
        raise OSError('Build directory cannot be guessed.')

    return os.path.split(result[0])[0]


def GuessIncludeDirectory():
    '''
    Return a list of absolute include paths; the list would be empty if the
    attempt fails.

    NOTE:
    1. It first probes whether there are any paths in the result of
    'GuessSourceDirectory' containing files with extensions specified in
    'HEADER_EXTENSIONS', qualified paths would become part of the result.

    2. It then checks the existence of either 'include' or 'inclues' in the
       current directory; it will add them to the result if the directory exists
       regardless of whether the directory contain valid file extensions
       specified in 'HEADER_EXTENSIONS'.
    '''
    result = list()
    source_dir = None
    include_dir_set = set()
    external_include_dir_set = set()

    try:
        source_dir = os.path.join(DirectoryOfThisScript(),
                                  GuessSourceDirectory())
        include_dir_set = TraverseByDepth(source_dir,
                                          frozenset(HEADER_EXTENSIONS))
    except OSError:
        pass

    # The 'include' or 'includes' subdirectory can be left as empty, but still
    # be considered as valid include path; unlike the include paths that reside
    # inside source directory.
    for external in ('include', 'includes'):
        external_include_path = os.path.join(DirectoryOfThisScript(), external)
        if os.path.exists(external_include_path):
            external_include_dir_set = TraverseByDepth(external_include_path,
                                                       None)
            break

    if include_dir_set:
        for include_dir in include_dir_set:
            result.append('-I' + include_dir)

    if external_include_dir_set:
        for include_dir in external_include_dir_set:
            result.append('-I' + include_dir)

    return result


def GuessSourceDirectory():
    '''
    Return either 'src', 'source', 'lib', or the name of the parent directory if
    any one of them exists in the current directory; the first found result is
    returned.
    Otherwise 'OSError' is raised should all of the above fail.
    '''
    guess_candidates = (
        'src',
        'source',
        'lib',
        os.path.basename(DirectoryOfThisScript())
    )

    for candidate in guess_candidates:
        result = os.path.join(DirectoryOfThisScript(), candidate)

        if os.path.exists(result):
            return result
    raise OSError('Source directory cannot be guessed.')


def TraverseByDepth(root, include_extensions):
    '''
    Return a set of child directories of the 'root' containing file
    extensions specified in 'include_extensions'.

    NOTE:
        1. The 'root' directory itself is excluded from the result set.
        2. No subdirectories would be excluded if 'include_extensions' is left
           to 'None'.
        3. Each entry in 'include_extensions' must begin with string '.'.
        4. Each entry in 'include_extensions' is treated in a case-insensitive
           manner.
    '''
    is_root = True
    result = set()

    if include_extensions:
        new_extensions = { entry.lower() for entry in include_extensions }
        include_extensions = new_extensions

    # Perform a depth first top down traverse of the given directory tree.
    for root_dir, subdirs, file_list in os.walk(root):
        if not is_root:
            # print("Relative Root: ", root_dir)
            # print(subdirs)
            if include_extensions:
                get_ext = os.path.splitext
                subdir_extensions = {
                    get_ext(f)[-1].lower() for f in file_list if get_ext(f)[-1]
                }
                if subdir_extensions & include_extensions:
                    result.add(root_dir)
            else:
                result.add(root_dir)
        else:
            is_root = False

    return result


# Set this to the absolute path to the folder (NOT the file!) containing the
# compile_commands.json file to use that instead of 'flags'. See here for
# more details: http://clang.llvm.org/docs/JSONCompilationDatabase.html
#
# You can get CMake to generate this file for you by adding:
#   set( CMAKE_EXPORT_COMPILE_COMMANDS 1 )
# to your CMakeLists.txt file.
#
# Most projects will NOT need to set this to anything; you can just change the
# 'flags' list of compilation flags. Notice that YCM itself uses that approach.
compilation_database_folder = ''

if GUESS_INCLUDE_PATH:
    flags.extend(GuessIncludeDirectory())

if GUESS_BUILD_DIRECTORY:
    try:
        compilation_database_folder = GuessBuildDirectory()
    except OSError:
        compilation_database_folder = ''

if os.path.exists(compilation_database_folder):
    database = ycm_core.CompilationDatabase(compilation_database_folder)
else:
    database = None

system_includes = LoadSystemIncludes()
flags = flags + system_includes


def MakeRelativePathsInFlagsAbsolute(flags, working_directory):
    '''
    Iterate through 'flags' and replace the relative paths prefixed by
    '-isystem', '-I', '-iquote', '--sysroot=' with absolute paths
    start with 'working_directory'.
    '''
    if not working_directory:
        return list(flags)
    new_flags = []
    make_next_absolute = False
    path_flags = ['-isystem', '-I', '-iquote', '--sysroot=']
    for flag in flags:
        new_flag = flag

        if make_next_absolute:
            make_next_absolute = False
            if not flag.startswith('/'):
                new_flag = os.path.join(working_directory, flag)

        for path_flag in path_flags:
            if flag == path_flag:
                make_next_absolute = True
                break

            if flag.startswith(path_flag):
                path = flag[len(path_flag):]
                new_flag = path_flag + os.path.join(working_directory, path)
                break

        if new_flag:
            new_flags.append(new_flag)
    return new_flags


def IsHeaderFile(filename):
    '''
    Check whether 'filename' is considered as a header file.
    '''
    extension = os.path.splitext(filename)[1].lower()
    return extension in HEADER_EXTENSIONS


def GetCompilationInfoForFile(filename):
    '''
    Helper function to look up compilation info of 'filename' in the 'database'.
    '''
    # The compilation_commands.json file generated by CMake does not have
    # entries for header files. So we do our best by asking the db for flags for
    # a corresponding source file, if any. If one exists, the flags for that
    # file should be good enough.
    if not database:
        return None

    if IsHeaderFile(filename):
        basename = os.path.splitext(filename)[0]
        for extension in SOURCE_EXTENSIONS:
            replacement_file = basename + extension
            if os.path.exists(replacement_file):
                compilation_info = \
                    database.GetCompilationInfoForFile(replacement_file)
                if compilation_info.compiler_flags_:
                    return compilation_info
        return None
    return database.GetCompilationInfoForFile(filename)


def FlagsForFile(filename, **kwargs):
    '''
    Callback function to be invoked by YouCompleteMe in order to get the
    information necessary to compile 'filename'.

    It returns a dictionary with a single element 'flags'. This element is a
    list of compiler flags to pass to libclang for the file 'filename'.
    '''
    if database:
        # Bear in mind that compilation_info.compiler_flags_ does NOT return a
        # python list, but a "list-like" StringVec object
        compilation_info = GetCompilationInfoForFile(filename)
        if not compilation_info:
            return None

        final_flags = MakeRelativePathsInFlagsAbsolute(
            compilation_info.compiler_flags_,
            compilation_info.compiler_working_dir_) + system_includes

    else:
        relative_to = DirectoryOfThisScript()
        final_flags = MakeRelativePathsInFlagsAbsolute(flags, relative_to)

    return {
        'flags': final_flags,
        'do_cache': True
    }
