#!/usr/bin/env python3
# naga.py

# Imports
from fabric import Connection, Config
from getpass import getpass


class HostConn(Connection):
    '''Extends fabric Connection class to include friendly name'''
    def set_name(self, name):
        self.name = name

    def get_name(self):
        return self.name


def new_host(hostname, configuration):
    '''Create HostConn(fabric.Connection) instance and name it'''
    conn = HostConn(hostname, config=configuration)
    conn.set_name(hostname)
    return conn


def get_sudo():
    '''Ask user for sudo password, return as fabric config object'''
    return Config(overrides={'sudo': {'password':
                             getpass("What's your sudo password? ")}})


def file_flag_check(conn, directory, flag):
    '''Check for file-based flags like .nopull'''
    if conn.run(f'ls -al {directory} | grep {flag}',
                hide=True,
                warn=True).stdout.splitlines():
        return True
    else:
        return False


def print_out(list):
    '''Output list of strings to stdout'''
    for line in list:
        print(line)


def get_subdirs(conn, directory):
    '''Get all first-level sub-directories of specified directory'''
    result = conn.run(f'find {directory} -maxdepth 1 -type d', hide=True)
    dirs = result.stdout.splitlines()
    if len(dirs) < 2:
        return False
    else:
        return dirs[1:]


def version_check(conn):
    '''Grab result from ~/bin/distro'''
    return conn.run('distro', hide=True).stdout.strip()


def git_repo(conn, directory):
    '''Git status and update - report if not clean'''
    if file_flag_check(conn, directory, ".noPull"):
        return f'{conn.name} repo {directory}: noPull, aborting update'
    status = conn.run(f'cd {directory} && git status',
                      hide=True).stdout.splitlines()
    if "working tree clean" not in status[-1]:
        return f'{conn.name} repo {directory}: not clean, aborting update'
    else:
        update = conn.run(f'cd {directory} && git pull',
                          hide=True).stdout.splitlines()
        if "Already " in update[-1]:
            return f'{conn.name} repo {directory}: already up to date'
        else:
            if file_flag_check(conn, directory, "postpull.sh"):
                conn.run(f'cd {directory} && ./postpull.sh', hide=True)
            return f'{conn.name} repo {directory}: {update[-1]}'


def repo_list(conn, directory="~/repos/"):
    '''Generate list of git repositories in standard structure'''
    repos = ["~/", "~/.ssh/", "~/bin/"]
    dirs = get_subdirs(conn, directory)
    if dirs:
        repos.extend(dirs)
    return repos


def git_all(conn):
    '''run git_repo() against all repos on host'''
    git_results = []
    for repo in repo_list(conn):
        git_results.append(git_repo(conn, repo))
    return git_results


def apt_update(conn):
    '''apt-get update'''
    conn.sudo('apt-get update', hide=True)
    return conn.run('apt-get --just-print upgrade | grep ^[0-9]')


def apt_upgrade(conn):
    '''apt-get -y upgrade'''
    conn.sudo('apt-get -y upgrade')


def main_function(host, command):
    config = get_sudo()
    conn = new_host(host, config)
    apt_upgrade(conn)


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
