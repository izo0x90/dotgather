#!/usr/bin/env python3

# TODO:
# - Implement --force directory path ✓
# - Implement chose installation dir on install ✓
#   - Implement GOHOME ✓
#   - Add .dotgatherhome creation to build cmd ✓
#   - Add --force-path and default dir to install help ✓
#   - Create .dotgatherhome on install ✓
#   - Implement install default dir ✓
#       - Dump cmd to add to .rc file to add env. variable ✓
#   - Help for setting up env. variable ✓
# - Finish setup ✓
#   - Implement git init on setup ✓
# - Implement disperse undo ✓
#   - Undo mechanism ✓
#   - Convert disperse to use walk_source_path_generate_alt_and_target ✓
#   - More granular control when individual target vs gathered diverged ✓
#   - Clean up ✓
# - Add version ✓
# - Fully test and re-enable disperse ✓
# - Add README.MD with usage instructions ✓
# - Add check in undo if exiting same as undo ✓
# - Maybe more granular disperse as option? Next ver. maybe
# - Implement disperse diff-only? Next ver. maybe

import argparse
import errno
import os
import pathlib
import shutil
import socket
import stat
import subprocess
import typing


class GIT_COMMANDS:
    MAIN = 'git'
    DIFF = 'diff'
    INIT = 'init'
    REV_PARSE = 'rev-parse'
    SHORSTAT_FLAG = '--shortstat'
    INSIDE_WORK_TREE_FLAG = '--is-inside-work-tree'
    INSIDE_WORK_TREE_RESPONSE = 'true'


VERSION = '1.0.0'
TERM_WIDTH, _ = os.get_terminal_size()
CMD_NAME = 'dg'
DATA_DIR = 'data'
TEMP_BACK_DIR = 'temp_backup'
UNDO_DIR = 'undo'
GATHER_LIST_NAME = 'dotfilelist'
IS_DOTGATHER_DIR_DOTFILE_NAME = '.dotgatherhome'
DOTGATHER_DIR_ENV_VAR_NAME = 'DOTGATHERHOME'
DESCRIPTION = f'ver. {VERSION} Collects a list of dot files (or other configs) in a git repo. Organized by hostname.'
PROCESS_SUCCSESS = 0
PROCESS_ERRORED = 1


class GatherException(Exception):
    pass


# Util. funcs.
def mkdir_or_existing(directory_path):
    try:
        os.makedirs(directory_path)
    except FileExistsError:
        pass


def split_path_dir_file(path):
    dir_path, file_name = path.rsplit('/', 1)
    return dir_path, file_name


def walk_source_path_generate_alt_and_target(source_base_path, alt_base_path):
    class ActionablePaths(typing.NamedTuple):
        source_file_path: pathlib.Path
        target_file_path: pathlib.Path
        alt_file_path: pathlib.Path
        target_exists: bool

    for root, dirs, files in os.walk(source_base_path, topdown=False):
        for file in files:
            [_, relative_path] = root.split(f'{source_base_path}/', 1)

            alt_root = os.path.join(alt_base_path, relative_path)

            actual_root = root.replace(source_base_path, '', 1)

            alt_file_path = os.path.join(alt_root, file)

            target_file_path = os.path.expanduser(os.path.join(actual_root, file))
            source_file_path = os.path.join(root, file)

            target_exists = os.path.exists(target_file_path)

            yield ActionablePaths(source_file_path=source_file_path,
                                  target_file_path=target_file_path,
                                  alt_file_path=alt_file_path,
                                  target_exists=target_exists)


def git_init():
    subprocess.run([GIT_COMMANDS.MAIN,
                    GIT_COMMANDS.INIT])


def git_is_inited():
    git_output = subprocess.run([
                                 GIT_COMMANDS.MAIN,
                                 GIT_COMMANDS.REV_PARSE,
                                 GIT_COMMANDS.INSIDE_WORK_TREE_FLAG
                                ],
                                capture_output=True)

    return GIT_COMMANDS.INSIDE_WORK_TREE_RESPONSE == git_output.stdout.strip().decode()


def git_diff(source_file_path, target_file_path):
    git_output = subprocess.run([GIT_COMMANDS.MAIN,
                                 GIT_COMMANDS.DIFF,
                                 GIT_COMMANDS.SHORSTAT_FLAG,
                                 target_file_path,
                                 source_file_path],
                                capture_output=True)

    return bool(git_output.stdout)


def print_center(text, padding_character='-'):
    print(f'[ {text} ]'.center(TERM_WIDTH, padding_character))


def print_aligned(longest_text_prefix, longest_text, other_text_items: list[tuple], padding_character='_'):
    print_center(f'{longest_text_prefix}{longest_text}')
    length_longest_text = len(longest_text)
    for line_prefix, text_item in other_text_items:
        padding = length_longest_text - len(text_item)
        print_center(f'{line_prefix}{padding_character * + padding}{text_item}')


def go_home():
    try:
        os.chdir(os.path.expanduser((os.getenv(DOTGATHER_DIR_ENV_VAR_NAME)) or pathlib.Path()))
    except FileNotFoundError:
        pass

    if not os.path.exists(IS_DOTGATHER_DIR_DOTFILE_NAME):
        raise GatherException(f'Not in dotgather home dir... manually change to it. ' +
                                'Or set {DOTGATHER_DIR_ENV_VAR_NAME} env. variable.')


# Command funcs.
def process_arguments():
    parser = argparse.ArgumentParser(description=DESCRIPTION)

    parser.add_argument('--setup',
                        help='Setup a dotgather directory for a specific machine. Host name will be used.' +
                        '\nCreate list of configs gather should target!',
                        action='store_const',
                        const=setup,
                        dest='command')

    parser.add_argument('--gather',
                        help='Collect dot files for this host.',
                        action='store_const',
                        const=gather_dotfiles,
                        dest='command')

    parser.add_argument('--disperse',
                        help='Place collected dotfile for current host in active dirs. Will make undo backup.',
                        action='store_const',
                        const=disperse_dotfiles,
                        dest='command')

    parser.add_argument('--undo-disperse',
                        help='Undo last disperse for current host',
                        action='store_const',
                        const=undo_disperse,
                        dest='command')

    parser.add_argument('--clean',
                        help='Clear undo back up for last disperse on a specific host',
                        action='store_const',
                        const=clean_undo,
                        dest='command')

    parser.add_argument('--version',
                        help='Show dotgather version',
                        action='store_const',
                        const=lambda _: print(VERSION),
                        dest='command')

    parser.add_argument('--force-path', type=pathlib.Path, help='Force an explicit path for a commnad to operate on ' +
                        'Maybe don\'t do this unless you really know what this script does ¯\\_(ツ)_/¯ !')

    args = parser.parse_args()

    return args, parser.prog


def setup(directory):
    if os.path.exists(directory):
        raise GatherException('Directory already exists! 🤷‍♀️')

    if not git_is_inited():
        git_init()
        print('Git tracking initialized ...')

    os.mkdir(directory)
    file = os.path.join(directory, GATHER_LIST_NAME)
    print('Create target list of config files that should be gathered:')
    with open(file, 'w') as dotfile_paths_file:
        try:
            dotfile_paths = list()
            while True:
                dotfile_path = input('Enter file path for collection, CTRL-D to save & exit ')
                dotfile_paths.append(f'{dotfile_path}\n')
        except EOFError:
            dotfile_paths_file.writelines(dotfile_paths)
            print('\nSaving gather list file! 🙌')


def gather_dotfiles(directory):
    print('Any existing undo will be removed as part of gathering new dotfile crop.')
    clean_undo(directory)

    file = os.path.join(directory, GATHER_LIST_NAME)
    data_dir_path = os.path.join(directory, DATA_DIR)
    data_temp_dir_path = os.path.join(directory, TEMP_BACK_DIR)

    try:
        os.rename(data_dir_path, data_temp_dir_path)
    except FileNotFoundError:
        pass

    try:
        with open(file, 'r') as dotfile_paths:
            for file_path in dotfile_paths:
                file_path = file_path.strip()
                file_path = os.path.expanduser(file_path)
                dest_path = f'{data_dir_path}{file_path}'

                print_aligned('Target >> ', dest_path, [('Source >> ', file_path)])
                print('\n')

                try:
                    shutil.copytree(file_path, dest_path)
                except OSError as e:
                    if e.errno in (errno.ENOTDIR, errno.EINVAL):
                        new_dir, _ = split_path_dir_file(dest_path)
                        mkdir_or_existing(new_dir)

                        shutil.copy(file_path, dest_path)
                    elif e.errno == errno.ENOENT:
                        raise GatherException(f'No such file {file_path}.' +
                                        f'Previous gather backed up in {data_temp_dir_path}. 🗑️🔥')
                    else:
                        raise GatherException('Something went terribly wrong! Go outside and take a walk. ' +
                                f'Previous gather backed up in {data_temp_dir_path}. 🗑️🔥')

    except FileNotFoundError:
        raise GatherException('Directory for this host has not been setup. Try --setup. ⚙️')

    # ######## Great success! We can remove temp backup
    try:
        shutil.rmtree(data_temp_dir_path)
    except FileNotFoundError:
        pass
    print('Great success!🧙🏿‍♂️')
    print('Like wild mushrooms 🍄 in a damp forest your dotfiles (and other configs) have been gathared! ✨')


def disperse_dotfiles(directory):
    data_dir_path = os.path.join(directory, DATA_DIR)
    undo_dir_path = os.path.join(directory, UNDO_DIR)

    files_dispersed = 0
    for paths in walk_source_path_generate_alt_and_target(data_dir_path, undo_dir_path):
        print('\n')

        undo_file_path = paths.alt_file_path
        source_file_path = paths.source_file_path
        target_file_path = paths.target_file_path
        target_exists = paths.target_exists

        print_aligned(f'Source >> ', source_file_path, [('Target >> ', target_file_path)])

        if not git_diff(source_file_path, target_file_path):
            print('These two files are the same, skipping dispersal. ♻️')
            continue

        # Check if a file already exist in target location and backup for undo
        if target_exists:
            print_center('Target exists, backing up for undo ...')

            undo_exists = os.path.exists(undo_file_path)
            if undo_exists:
                if git_diff(undo_file_path, target_file_path):
                    raise GatherException('A different undo state has been already saved. ' +
                        'Use --clean 🧹 to clear existing undo if no longer relevant.🍏/🍎')
                else:
                    print('Skipping undo, it already exists! 🍏/🍏')
                    continue

            new_dir, _ = split_path_dir_file(undo_file_path)
            mkdir_or_existing(new_dir)
            shutil.copy(target_file_path, undo_file_path)
            print_aligned('Undo >>>> ', undo_file_path, [('Target >> ', target_file_path)])
            print_center('Created undo for 💾')

        # Copy repo dotfile to target location
        shutil.copy(source_file_path, target_file_path)
        files_dispersed += 1
        print('File dispersed. 🌱')

    print('\nTada!!🧙🏿‍♂️')
    print(f'Successfuly seeded {files_dispersed} files! 🚜 ✨')


def clean_undo(directory):
    undo_dir_path = os.path.join(directory, UNDO_DIR)
    undo_exists = os.path.exists(undo_dir_path)

    if not undo_exists:
        print('No undo data found!')
        return

    confirm_delete_files = input(f'Type "YES" to confirm you want to remove undo for {undo_dir_path} ')

    if confirm_delete_files != 'YES':
        raise GatherException('Aborted removing exiting undo! 🖐️')

    shutil.rmtree(undo_dir_path)
    print('Undo files removed. 🧹')


def undo_disperse(directory):
    data_dir_path = os.path.join(directory, DATA_DIR)
    undo_dir_path = os.path.join(directory, UNDO_DIR)

    files_skipped = []
    files_identical = []
    files_to_copy = []

    for paths in walk_source_path_generate_alt_and_target(undo_dir_path, data_dir_path):
        data_file_path = paths.alt_file_path
        source_file_path = paths.source_file_path
        target_file_path = paths.target_file_path
        target_exists = paths.target_exists

        # If target exists is it identical to undo version, no undo needed
        if target_exists and not git_diff(source_file_path, target_file_path):
            files_identical.append((source_file_path, target_file_path))

        # If target exists make sure it is same as gathered version
        elif target_exists and git_diff(data_file_path, target_file_path):
            files_skipped.append((data_file_path, target_file_path))
        else:
            files_to_copy.append((source_file_path, target_file_path))

    if files_skipped:
        print_center(f'\nThe following {len(files_skipped)} files have diverged:')
        for data_file_path, target_file_path in files_skipped:
            print_aligned('Source (gathered  file) >> ', data_file_path,
                        [('Target (dispersed file) >> ', target_file_path)])  # noqa

        confirm_recover_files = input(f'Type "YES" to confirm you want to still recover {len(files_to_copy)} files  ')
        if confirm_recover_files != 'YES':
            raise GatherException('Undo files and dispersed files have diverged. ' +
                            'Unfortunetly you will have to fix this manually. 🛠️')
        print('\n') # Next section separator

    if files_identical:
        print_center(f'The following {len(files_identical)} files are identical no undo needed:')

        for undo_file_path, target_file_path in files_identical:
            print('\n')
            print_aligned('Source (undo      file) >> ', undo_file_path,
                        [('Target (dispersed file) >> ', target_file_path)])  # noqa

        print('\n') # Next section separator

    if files_to_copy:
        print_center('Reverting dispersed files from undo:')
        for source_file_path, target_file_path in files_to_copy:
            print('\n')
            shutil.copy(source_file_path, target_file_path)
            print_aligned('Source file) >> ', source_file_path, [('Target file) >> ', target_file_path)])

    print(f'Successfuly reverted {len(files_to_copy)} files. ' +
          (f'Undo skipped on {len(files_skipped)} diverged files! ' if files_skipped else '') +
          (f'Undo not needed on {len(files_identical)} identical files.' if files_identical else ''))


def main():
    args, _ = process_arguments()

    explicit_dir = args.force_path
    hostname = socket.gethostname()
    dir = explicit_dir or hostname

    if not dir:
        print('No directory given or host name found, not sure what to do! 😕')
        return PROCESS_ERRORED

    try:
        if not args.command:
            raise GatherException('What should I do? Try --help. 🤔')

        if explicit_dir and input(f'You sure you want to force this "{explicit_dir}" ' +
                                  'path. Bad things might happen? "Y" or "N" >') != 'Y':
            return PROCESS_ERRORED

        go_home()

        args.command(dir)
    except GatherException as e:
        print(f'\n\n{str(e)}\n')
        return PROCESS_ERRORED

    return PROCESS_SUCCSESS


if __file__[-len(CMD_NAME):] != CMD_NAME:
    def install():
        parser = argparse.ArgumentParser(description=f'{DESCRIPTION} Install the script to a select directory to use!')

        parser.add_argument('--install_path',
                            type=pathlib.Path,
                            required=True,
                            help='Select a path to install gather script and store dotfiles in.')

        parser.add_argument('--upgrade',
                            help='Upgrade existing installation to new version.',
                            action="store_true")

        args = parser.parse_args()

        directory = args.install_path
        install_path = os.path.join(directory, CMD_NAME)
        is_home_dir_file_path = os.path.join(directory, IS_DOTGATHER_DIR_DOTFILE_NAME)
        full_install = not args.upgrade

        if not os.path.exists(directory):
            print(f'Directory "{directory}" not found, creating now!')
            os.mkdir(directory)

        if os.path.exists(install_path) and full_install:
            print(f'File with the same name "{install_path}" already exists, please delete first! 🖐️')
            print(f'Use --install --upgrade to replace existing copy of dotgather with this one.')
            return PROCESS_ERRORED

        shutil.copy(__file__, install_path)
        os.chmod(install_path, stat.S_IRWXU)

        if full_install:
            open(is_home_dir_file_path, 'w').close()

            print('To run dotgather from anywhere:')
            print(f'Add `{install_path}` to you system path')
            print(f'Along with `export {DOTGATHER_DIR_ENV_VAR_NAME}="{directory}"` to you .rc file.')

        else:
            print('Upgrade complete!')

        print('🍾🙌👯‍♀️')

        return PROCESS_SUCCSESS

    if __name__ == '__main__':
        raise SystemExit(install())


if __name__ == '__main__':
    raise SystemExit(main())
