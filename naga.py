#!/usr/bin/env python3
# naga.py

# Import statements
from multitool import RemoteSSH, Snitch, create_formatter, print_table
import os
snitch = Snitch('NAGA', log_file='/tmp/naga.log')


def read_stout(lines_list):
    for line in lines_list:
        print(line, end='')


def get_subdirs(target, dir_name):
    result = target.execute(f'find {dir_name} -maxdepth 1 -type d')
    return(result[1:])


def check_status(output, dict_flags):
    status_flags = dict_flags
    for key in status_flags:
        if any(key in s for s in output):
            return status_flags[key]
    snitch.debug('Unhandled output in check_status: ', output)
    return('Unhandled output - check log')


def repo_status(target, repo_dir):
    command_string = f'cd {repo_dir} && git status'
    return(check_status(target.execute(command_string)))


def update_repo(target, repo_dir):
    command_string = f'cd {repo_dir} && git pull'
    flagCheck = target.execute(f'cd {repo_dir} && ls -a')
    flags = {
            "Already": "no change",
            "Updating": "updated"
    }
    if any('.noPull' in s for s in flagCheck):
        snitch.info(f'{repo_dir} has .noPull - skipping')
        return([f'{repo_dir}: skipped'])
    if any('.postpull.sh' in s for s in flagCheck):
        command_string = command_string + ' && ./.postpull.sh'
        check_status(target.execute(command_string), flags)


def main_function(hostname, command):
    target = RemoteSSH(hostname, 'matt')
    read_stout(target.execute(command))
    read_stout(get_subdirs(target, '~/repos/'))
    read_stout(update_repo(target, '~/.ssh/'))
    target.disconnect()
    return


def main(argv):
    ''' Parse command line arguments etc.'''
    if len(argv) < 3:  # size for req and opt args
        raise SystemExit(f'Usage: {argv[0]} ' '<host> <command>')
    hostname = argv[1]
    command = argv[2]
    main_function(hostname, command)


if __name__ == '__main__':
    import sys
    main(sys.argv)
