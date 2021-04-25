#!/usr/bin/env python3
# naga.py

# Imports
from fabric import Connection, Config
from invoke import exceptions
from cmd import Cmd
from getpass import getpass
from backend import Host, db_add_host, db_fetch_hostid, db_add_child,\
                    db_fetch_hostid, db_read_host, db_connector,\
                    db_fetch_hostlist
import admin
import argparse
import re
import os

class NagaPrompt(Cmd):
    intro = 'Welcome to the Naga shell. Type help or ? to list commands.\n'
    prompt = 'naga> '
    reboot_list = []
    hosts = {}

    def do_exit(self, inp):
        '''Exit to system shell.'''
        if len(self.reboot_list) > 0:
            print(f'\n\nThe following hosts need to be rebooted:')
            print_out(self.reboot_list)
        print('Bye.')
        return True

    def do_list(self, inp):
        '''List configured hosts in database'''
        if len(self.hosts) == 0:
            config, hosts = setup()
            targets = {}
            for host in hosts:
                id = db_fetch_hostid('', host)
                host = db_read_host('', id, config)
                targets[host.name] = host
            self.hosts = targets
            self.do_list(inp)
        else:
            print("Configured hosts:")
            for host in self.hosts:
                print(host)


def add_host(config=None):
    '''
    Create Host object, write it to db
    :param config: Connection Config object if provided
    :return: Host object
    '''
    name = input("Enter the hostname (from ~/.ssh/config): ")
    if config is None:
        config = get_sudo()
    updater = input("Enter updater function to use [default=apt_all]: ")
    if updater == '':
        updater = 'apt_all'
    appList = []
    flag = True
    while flag:
        appList.append(input("Additional update function? "))
        if appList[-1] == '':
            appList.remove('')
            flag = False
    child = input("If this is a VM, what system hosts it? [Enter for None]:")
    host = Host(name, updater, appList, config, [])
    new_id = db_add_host('', host)
    if str(child) != '':
        host_id = db_fetch_hostid('', str(child).strip.lower())
        db_add_child('', host_id, new_id)
    print(f'{host.name} added as host id {new_id}')
    return host


def get_sudo():
    '''
    Create Config object with sudo password
    :return: Fabric/Config object
    '''
    return Config(overrides={'sudo': {'password':
                             getpass("What's your sudo password? ")}})


def print_out(list):
    '''
    Output list of strings to stdout
    :param list: List of formatted strings
    :return: Output function, does not return
    '''
    for line in list:
        print(line)


def run_host(host, config=None):
    '''
    Execute updater, host appList updaters, print output
    :param db_conn: db connection object
    :param host: hostname
    :param config: Connection Configuration object
    '''
    host_id = db_fetch_hostid('', host)
    host = db_read_host('', host_id, config)
    host_func = getattr(admin, host.updater, admin.version_check)
    host_out, flag = host_func(host)
    print_out(host_out)
    for app in host.appList:
        app_func = getattr(admin, app, admin.version_check)
        print_out(app_func(host))
    return flag


def setup():
    config = get_sudo()
    hosts = db_fetch_hostlist('')
    return config, hosts


def main(argv):
    parser = argparse.ArgumentParser(description='Automated / interactive maintenance program.')
    parser.add_argument("host", type=str, default="all",
                        help="Hostname or \'all\'; \'shell\' for interactive mode")
    parser.add_argument("-db", "--database", type=str, default="hosts.db",
                        help="SQLite3 db file to use")
    args = parser.parse_args()
    os.environ['CONN'] = args.database
    if args.host == "shell":
        NagaPrompt().cmdloop()
    elif args.host == "all":
        reboot_list = []
        config, hosts = setup()
        for host in hosts:
            flag = run_host(host, config)
            if flag is True:
                reboot_list.append(f'\t{host}')
        if len(reboot_list) > 0:
            print(f'\n\nThe following hosts need to be rebooted:')
            print_out(reboot_list)
    else:
        config = get_sudo()
        flag = run_host(args.host, config)
        if flag is True:
            print(f'\n\nHost {args.host} needs to be rebooted.')
    # Clean up
    del os.environ['CONN']


if __name__ == '__main__':
    import sys
    main(sys.argv)
