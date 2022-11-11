#!/usr/bin/env python3
import argparse
import errno
import os
import socket
import shutil

TERM_WIDTH, _ = os.get_terminal_size()
CMD_NAME = 'dg'
DATA_DIR = 'data'
TEMP_BACK_DIR = 'temp_backup'
HOME_DIR = 'home'
GATHER_LIST_NAME = 'dotfilelist'
DESCRIPTION = 'Collects a list of dot file (or other config) in a git repo.\nOrganized by hostname.'


class GatherException(Exception):
    pass

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
                dotfile_path = input('Enter file path for collection or CTRL-D to exit ')
                dotfile_paths.append(f'{dotfile_path}\n')
        except EOFError:
            dotfile_paths_file.writelines(dotfile_paths)
            print('\nSaving gather list file! 🙌')

def gather_dotfiles(directory):
    file = os.path.join(directory, GATHER_LIST_NAME)
    data_dir_path = os.path.join(directory, DATA_DIR)
    data_temp_dir_path = os.path.join(directory, TEMP_BACK_DIR)
    home_dir_path = os.path.join(data_dir_path, HOME_DIR)
    try:
        os.rename(data_dir_path, data_temp_dir_path)
    except FileNotFoundError:
        pass

    try:
        with open(file, 'r') as dotfile_paths:
            for file_path in dotfile_paths:
                file_path = file_path.strip()
                dest_path = file_path.replace('~', home_dir_path)
                file_path = os.path.expanduser(file_path)
                print(f' [Copying {dest_path = }] '.center(TERM_WIDTH, '-'))
                print(f' [To {file_path = }] '.center(TERM_WIDTH, '-'))
                print('\n')

                try:
                    shutil.copytree(file_path, dest_path)
                except OSError as e:
                    if e.errno in (errno.ENOTDIR, errno.EINVAL):
                        new_dir, _ = dest_path.rsplit('/', 1)
                        try:
                            os.makedirs(new_dir)
                        except FileExistsError:
                            pass

                        shutil.copy(file_path, dest_path)
                    else: 
                        raise GatherException('Something went terribly wrong! Go outside and take a walk. 🗑️🔥')
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
    # TODO: Reverse gather process back up existing files, clean with explicit clean call
    #       Add undo dirs to .gitignore
    pass

def clean_undo(directory):
    # TODO: Clear undo dir for a specifc host dir
    pass

def undo_disperse(directory):
    # TODO: Revert files from an undo dir
    pass

def main():
    args,_ = process_arguments()

    explicit_dir = None
    hostname = socket.gethostname()
    dir = explicit_dir or hostname

    if not dir:
        print('No directory given or host name found, not sure what to do! 😕')
        return 1

    try:
        if not args.command:
            raise GatherException('What should I do? Try --help. 🤔')

        args.command(dir)
        return 0
    except GatherException as e:
        print(str(e))
        return 1

    return 0

if __name__ == '__main__':
    raise SystemExit(main())
