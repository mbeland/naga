#!/usr/bin/env python3
# admin.py

# Imports
from fabric import Connection, Config
from invoke import exceptions
from getpass import getpass
from paramiko import ssh_exception
import admin
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
    return out


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
        out.append(conn.run(''))
    except exceptions.UnexpectedExit as e:
        e = parse_e(e)
        return f'failed: {e}'
    except ssh_exception.NoValidConnectionsError as e:
        return(f'connection failed: {e}')


def apt_update(conn):
    '''
    apt-get update
    :param conn: Host instance connection element
    :return: Formatted string
    '''
    try:
        conn.sudo('apt-get update', hide=True)
    except (exceptions.UnexpectedExit,
            ssh_exception.NoValidConnectionsError) as e:
        return f'failed: {e}'
    return conn.run('apt-get --just-print upgrade | grep ^[0-9]',
                    hide=True).stdout.strip()


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
    return out


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