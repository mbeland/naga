#!/usr/bin/env python3
# admin.py

# Imports
from fabric import Connection, Config
from invoke import exceptions
from getpass import getpass
from paramiko import ssh_exception
from backend import Host, db_read_host
from pathlib import Path
import argparse
import re


def apt_all(host):
    '''
    Structured / formatted collection of system update for apt-get
    :param host: Host object
    :return: List of formatted strings
    '''
    out = [f'{host.name}: System update:']
    out.append(f'{host.name}: {apt_update(host.conn)}')
    out.append(f'{host.name}: {apt_upgrade(host.conn)}')
    out.append(f'{host.name} autoremove: {apt_autoremove(host.conn)}')
    check, flag = apt_checkrestart(host)
    out.extend(check)
    return out, flag


def apt_autoremove(conn):
    '''
    apt-get -y autoremove
    :param conn: Host instance connection element
    :return: list of formatted strings
    '''
    out = []
    try:
        out.append(conn.sudo('apt-get -y autoremove',
                   hide=True).stdout.splitlines()[-1])
    except exceptions.UnexpectedExit as e:
        e = parse_e(e)
        return f'failed: {e}'
    except ssh_exception.NoValidConnectionsError as e:
        return(f'connection failed: {e}')


def apt_checkrestart(host):
    '''
    Test to determine host needs for service restarts or reboot
    :param host: Host object
    :return: list of formatted strings
    '''
    flag = False
    filename = '/usr/sbin/checkrestart'
    out = []
    reboot_file = '/var/run/reboot-required'
    try:
        if not file_test(host.conn, filename):
            apt_install(host, 'debian-goodies')
        output = host.conn.sudo('checkrestart', hide=True).stdout.splitlines()
        out.append(f'{host.name}: {output[0]}')
        if file_test(host.conn, reboot_file):
            out.append('*** System restart required ***')
            flag = True
    except exceptions.UnexpectedExit as e:
        e = parse_e(e)
        out.append(f'failed: {e}')
    except ssh_exception.NoValidConnectionsError as e:
        out.append(f'connection failed: {e}')
    return out, flag


def apt_install(host, package):
    '''
    Install specified package and dependencies with apt-get
    :param host: Host object
    :param package: package to install
    :return: list of formatted strings
    '''
    out = [f'{host.name}: {package} install:']
    command = 'DEBIAN_FRONTEND=noninteractive apt-get -y install ' + package
    try:
        output = host.conn.sudo(command, hide=True).stdout.splitlines()
        for line in output:
            if re.search('^[0-9]', line) or re.search('^Fetched', line):
                out.append(line)
    except exceptions.UnexpectedExit as e:
        e = parse_e(e)
        out.append(f'failed: {e}')
    except ssh_exception.NoValidConnectionsError as e:
        out.append(f'connection failed: {e}')
    return out


def apt_remove(host, package):
    '''
    Remove specified package and dependencies with apt-get
    :param host: Host object
    :param package: package to install
    :return: list of formatted strings
    '''
    out = [f'{host.name}: {package} removal:']
    command = 'DEBIAN_FRONTEND=noninteractive apt-get -y remove ' + package
    try:
        output = host.conn.sudo(command, hide=True).stdout.splitlines()
        for line in output:
            if re.search('^[0-9]', line) or re.search('^Removing', line):
                out.append(line)
        apt_autoremove(host.conn)
        out.extend(apt_checkrestart(host.conn))
    except exceptions.UnexpectedExit as e:
        e = parse_e(e)
        out.append(f'failed: {e}')
    except ssh_exception.NoValidConnectionsError as e:
        out.append(f'connection failed: {e}')
    return out


def apt_update(conn):
    '''
    apt-get update
    :param conn: Host instance connection element
    :return: Formatted string
    '''
    try:
        conn.sudo('apt-get update', hide=True)
        outlines = conn.run('apt-get --just-print upgrade',
                            hide=True).stdout.splitlines()
        for line in outlines:
            if re.search('^[0-9]', line):
                out = line.strip()
    except (exceptions.UnexpectedExit,
            ssh_exception.NoValidConnectionsError) as e:
        return f'failed: {e}'
    return out


def apt_upgrade(conn):
    '''
    apt-get -y upgrade
    :param conn: Host instance connection element
    :return: Formatted string
    '''
    try:
        conn.sudo('DEBIAN_FRONTEND=noninteractive apt-get -y upgrade',
                  hide=True)
        return "system updated"
    except exceptions.UnexpectedExit as e:
        e = parse_e(e)
        return(f'upgrade failed: {e}')
    except ssh_exception.NoValidConnectionsError as e:
        return(f'connection failed: {e}')


def brew_all(host):
    '''
    Structured / formatted collection of update tasks for Homebrew
    :param host: Host object
    :return: List of formatted strings
    '''
    out = [f'{host.name}: System update:']
    try:
        brew_count = brew_update(host.conn)
        out.append(f'{host.name}: {brew_count}')
        if re.search('^0', brew_count):
            out.append(f'{host.name}: No packages to upgrade, skipping')
        else:
            out.append(f'{host.name}: {brew_upgrade(host.conn)}')
    except ssh_exception.NoValidConnectionsError as e:
        out.append(f'connection failed: {e}')
    return out, False


def brew_update(conn):
    '''
    Homebrew update / outdated count
    :param conn: Host instance connection element
    :return: Formatted string
    '''
    try:
        conn.run('/usr/local/bin/brew update', hide=True)
        brew_com = '/usr/local/bin/brew outdated | wc -l | awk {\'print $1\'}'
        brewstat = conn.run(brew_com, hide=True).stdout.strip()
        return f'{brewstat} packages to update'
    except exceptions.UnexpectedExit as e:
        return f'brew update failed: {e}'
    except ssh_exception.NoValidConnectionsError as e:
        return(f'connection failed: {e}')


def brew_upgrade(conn):
    '''
    Homebrew upgrade and cleanup
    :param conn: Host instance connection element
    :return: Formatted string
    '''
    brew_com2 = '/usr/local/bin/brew upgrade'
    brew_com3 = '/usr/local/bin/brew cleanup'
    try:
        conn.run(brew_com2, hide=True)
        conn.run(brew_com3, hide=True)
        return f'brew upgrade complete'
    except exceptions.UnexpectedExit as e:
        return f'brew upgrade failed: {e}'
    except ssh_exception.NoValidConnectionsError as e:
        return(f'connection failed: {e}')


def file_test(conn, filename):
    '''
    Test for existence of the file on remote host
    :param conn: Host connection object
    :param filename: path of file to test as string
    :return: Boolean value
    '''
    command = f'if test -f "{filename}"; then echo "True"; fi'
    return bool(conn.run(command, hide=True).stdout.strip())


def file_flag_check(conn, directory, flag):
    '''
    Check for file-based flags like .nopull
    :param conn: Host connection object
    :param directory: remote directory to check for flags (str)
    :param flag: string to search for in filenames
    :return: True/False
    '''
    if conn.run(f'ls -al {directory} | grep {flag}',
                hide=True,
                warn=True).stdout.splitlines():
        return True
    else:
        return False


def get_subdirs(conn, directory):
    '''
    Get all first-level sub-directories of specified directory
    :param conn: Host connection object
    :param directory: remote parent directory as path string
    :return: list of directory names as strings (removes . and ..)
    '''
    result = conn.run(f'find {directory} -maxdepth 1 -type d', hide=True)
    dirs = result.stdout.splitlines()
    if len(dirs) < 2:
        return False
    else:
        return dirs[1:]


def git_all(host):
    '''
    run git_repo() against all repos on host
    :param host: Host object
    :return: List of formatted strings
    '''
    git_results = []
    try:
        for repo in repo_list(host.conn):
            git_results.append(git_repo(host, repo))
    except exceptions.UnexpectedExit as e:
        e = parse_e(e)
        git_results.append(f'{host.name} repo {repo}: {e}')
    except ssh_exception.NoValidConnectionsError as e:
        return([f'connection failed: {e}'])
    return git_results


def git_repo(host, directory):
    '''
    Git status and update - report if not clean
    :param host: Host connection object
    :param directory: Path to remote repository as string
    :return: formatted string
    '''
    if file_flag_check(host.conn, directory, ".noPull"):
        return f'{host.name} repo {directory}: noPull, aborting update'
    status = host.conn.run(f'cd {directory} && git status',
                           hide=True).stdout.splitlines()
    if "working tree clean" not in status[-1]:
        return f'{host.name} repo {directory}: not clean, aborting update'
    else:
        update = host.conn.run(f'cd {directory} && git pull',
                               hide=True).stdout.splitlines()
        if "Already " in update[-1]:
            return f'{host.name} repo {directory}: already up to date'
        else:
            if file_flag_check(host.conn, directory, ".postpull.sh"):
                host.conn.run(f'cd {directory} && ./.postpull.sh', hide=True)
            output = ''
            for line in update:
                if re.search('^ [0-9]+? file', line):
                    output = line
            return f'{host.name} repo {directory}: {output}'


def parse_e(e):
    '''
    Parse the UnexpectedError output from invoke.run/sudo, extract stderr
    :param e: UnexpectedError output strings
    :return: Just the stderr string
    '''
    return str(e).split("Stderr:\n\n")[1].split("\n")[0]


def pihole_up(host):
    '''
    Update pihole installation
    :param host: Host object
    '''
    out = [f'{host.name}: Update Pi-Hole']
    try:
        update = host.conn.sudo('pihole -up', hide=True).stdout.splitlines()
        out.append(f'{host.name}: pihole{update[-1]}')
    except exceptions.UnexpectedExit as e:
        out.append(f'{host.name}: pihole update failed: {e}')
    except ssh_exception.NoValidConnectionsError as e:
        out.append(f'connection failed: {e}')
    return out


def reboot(host, time='+1', halt=False):
    '''
    Reboots specified host
    :param host: Host object
    :param time: Time in HH:MM format or integer minutes
    :param halt: Power off instead of reboot
    :return: List of formatted strings
    '''
    out = []
    if halt is True:
        flag = '-h'
    else:
        flag = '-r'
    try:
        if host.children[0] != '0':
            for child in host.children:
                child_host = db_read_host('', child, host.configuration)
                out.append(reboot(child_host, time, halt=True))
            if re.search(r'^\+', time):
                time = '+' + str(int(time[1:]) + 1)
            else:
                h, m = time.split(':')
                time = h + ':' + str(int(m) + 1)
        out1 = f'{host.name} '
        out2 = host.conn.sudo(f'/sbin/shutdown {flag} {time}',
                              hide=True).stderr.strip().split(',')[0]
        out.append(out1 + out2)
    except exceptions.UnexpectedExit as e:
        out.append(f'{host.name}: command failure: {e}')
    except ssh_exception.NoValidConnectionsError as e:
        out.append(f'{host.name}: connection failed: {e}')
    return out


def repo_list(conn, directory="~/repos/"):
    '''
    Generate list of git repositories in standard structure
    :param conn: Host connection object
    :param directory: Parent directory of repositories (Default: ~/repos/)
    :return: list of repository path strings inc. ~, ~/.ssh, and ~/bin/
    '''
    repos = ["~/", "~/.ssh/", "~/bin/"]
    dirs = get_subdirs(conn, directory)
    if dirs:
        repos.extend(dirs)
    return repos


def script(host, filename, sudo=False, dest=None, execute=True):
    '''
    Push specified file to hosts and exeecute
    :param host: Host object
    :param filename: local file to deploy
    :param sudo: Execute with sudo, defaults to False
    :param dest: Destination path, defaults to /tmp/
    :param execute: Execute deployed file, defaults to True
    :return: List of formatted strings
    '''
    out = []
    out.append(f'Deploying to {host.name}...')
    try:
        p = Path(filename).expanduser()
        filename = str(p).split('/')[-1]
        if not p.is_file():
            out.append(f'{p} is not a valid filename')
            return out
        if dest is not None:
            d = Path(f'{dest}/{filename}')
        else:
            d = Path(f'/tmp/{filename}')
            out.append(host.conn.put(p, str(d), preserve_mode=True))
        if execute is True:
            if sudo is True:
                outlines = host.conn.sudo(str(d), hide=True).stdout.split('\n')
            else:
                outlines = host.conn.run(str(d), hide=True).stdout.split('\n')
            for line in outlines:
                if len(line) < 1:
                    next
                out.append(f'{host.name}: {line}')
        else:
            out.append(f'{host.name}: Transfer complete.')
    except Exception as e:
        out.append(f'{host.name}: Transfer failed: {e}')
    return out
        

def version_check(host):
    '''
    Grab result from ~/bin/distro
    :param host: Host object
    :return: Formatted string
    '''
    try:
        return host.conn.run('distro', hide=True).stdout.strip()
    except exceptions.UnexpectedExit as e:
        return (f'UnexpectedExit: {e}')
    except ssh_exception.NoValidConnectionsError as e:
        return(f'connection failed: {e}')
