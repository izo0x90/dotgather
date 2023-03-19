#!/usr/bin/env python3
# TODO:
# - Implement Chose installation dir on build
#  - Implement GOHOME ✓
#  - add .dotgatherhome creation to build cmd
#  - Help for setting up env. variable
# - Implement disperse undo
# - Implement disperse diff-only
# - Implement --force directory path 

import argparse
import errno
import os
import socket
import subprocess
import shutil

GIT_DIFF_CMD = 'git diff --shortstat'
TERM_WIDTH, _ = os.get_terminal_size()
CMD_NAME = 'dg'
DATA_DIR = 'data'
TEMP_BACK_DIR = 'temp_backup'
UNDO_DIR = 'undo'
GATHER_LIST_NAME = 'dotfilelist'
IS_DOTGATHER_DIR_DOTFILE_NAME = '.dotgatherhome'
DOTGATHER_DIR_ENV_VAR_NAME = 'DOTGATHERHOME'
DESCRIPTION = 'Collects a list of dot file (or other config) in a git repo.\nOrganized by hostname.'


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

def git_diff(source_file_path, target_file_path):
    git_output = subprocess.run(['git', 'diff', '--shortstat', target_file_path, source_file_path], 
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
            os.chdir(os.path.expanduser(os.getenv(DOTGATHER_DIR_ENV_VAR_NAME)) or '')
        except FileNotFoundError:
            pass
        
        if not os.path.exists(IS_DOTGATHER_DIR_DOTFILE_NAME):
            raise GatherException(f'Not in dotgather home dir... manually change to it. ' + \
                    'Or set {DOTGATHER_DIR_ENV_VAR_NAME} env. variable.')

# Command funcs.
def process_arguments():
    parser = argparse.ArgumentParser(description=DESCRIPTION)

    if parser.prog != CMD_NAME:
        parser.add_argument('--build',
                            help='Copy source to runnable script to "release" updated version.',
                            action='store_const',
                            const=build,
                            dest='command')
    
    parser.add_argument('--setup',
                        help='Setup a dotgather directory for a specific machine.',
                        action='store_const',
                        const=setup,
                        dest='command')

    parser.add_argument('--disperse',
                        help='Place dotfile in active dirs. Will make undo backup.',
                        action='store_const',
                        const=disperse_dotfiles,
                        dest='command')

    parser.add_argument('--gather',
                        help='Collect dot files for this host.',
                        action='store_const',
                        const=gather_dotfiles,
                        dest='command')

    parser.add_argument('--undo',
                        help='Undo last disperse for specific host',
                        action='store_const',
                        const=undo_disperse,
                        dest='command')

    parser.add_argument('--clean',
                        help='Clear undo back up for last disperse on a specific host',
                        action='store_const',
                        const=clean_undo,
                        dest='command')

    args = parser.parse_args()
    return args, parser.prog

def build(_):
    shutil.copy(__file__, os.path.join('..', CMD_NAME))
    print('🍾🙌👯‍♀️')

def setup(directory):
    if os.path.exists(directory):
        raise GatherException('Directory already exists! 🤷‍♀️')

    os.mkdir(directory)
    file = os.path.join(directory, GATHER_LIST_NAME)
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
                    else: 
                        raise GatherException(f'Something went terribly wrong! Go outside and take a walk. '+ \
                                'Previous gather backed up in {data_temp_dir_path}. 🗑️🔥')
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
    for root, dirs, files in os.walk(data_dir_path, topdown=False):
        for file in files:
            print('\n')
            [_, relative_path] = root.split(f'{data_dir_path}/', 1)

            undo_root = os.path.join(undo_dir_path, relative_path)

            actual_root = root.replace(data_dir_path, '', 1)

            undo_file_path = os.path.join(undo_root, file)

            target_file_path = os.path.expanduser(os.path.join(actual_root, file))
            source_file_path = os.path.join(root, file)
            
            target_exists = os.path.exists(target_file_path)

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
                        raise GatherException('A different undo state has been already saved. ' + \
                            'Use --clean 🧹 to clear existing undo if no longer relevant.🍏/🍎')
                    else:
                        print('Skipping undo, it already exists! 🍏/🍏')
                        continue

                new_dir, _ = split_path_dir_file(undo_file_path)
                mkdir_or_existing(new_dir)
                shutil.copy(target_file_path, undo_file_path)
                print_aligned('Undo >>>> ', undo_file_path, [('Target >> ', target_file_path)])
                # print_center('Created undo for 💾')

            # Copy repo dotfile to target location
            # shutil.copy(source_file_path, target_file_path)
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
    # TODO: Revert files from an undo dir
    pass

def main():
    PROCESS_SUCCSESS = 0 
    PROCESS_ERRORED = 1
    args,_ = process_arguments()

    explicit_dir = None
    hostname = socket.gethostname()
    dir = explicit_dir or hostname

    if not dir:
        print('No directory given or host name found, not sure what to do! 😕')
        return PROCESS_ERRORED

    try:
        if not args.command:
            raise GatherException('What should I do? Try --help. 🤔')

        go_home()
        args.command(dir)
    except GatherException as e:
        print(f'\n\n{str(e)}\n')
        return PROCESS_ERRORED

    return PROCESS_SUCCSESS

if __name__ == '__main__':
    raise SystemExit(main())

