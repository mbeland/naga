#!/usr/bin/env python3
# naga.py

# Imports
from fabric import Connection, Config
from invoke import exceptions
from getpass import getpass
from backend import Host, db_add_host, db_fetch_hostid, db_add_child,\
                    db_fetch_hostid, db_read_host, db_connector,\
                    db_fetch_hostlist
import admin
import argparse
import re
import os

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
    child = input("If this is a VM, what system hosts it? [Enter for None]"
                  ).strip.lower()
    host = Host(name, updater, appList, config, [])
    new_id = db_add_host('', host)
    if child != '':
        host_id = db_fetch_hostid('', child)
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


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("host", help="Friendly name of system to target")
    parser.add_argument("-db", "--database", type=str,
                        help="SQLite3 db file to use [default=hosts.db")
    parser.add_argument("-cmd", "--command", nargs=2,
                        help="Function to execute on listed host(s)")
    args = parser.parse_args()
    reboot_list = []
    if (args.database is None):
        args.database = 'hosts.db'
    os.environ['CONN'] = args.database
    config = get_sudo()
    if args.host == "all":
        hosts = db_fetch_hostlist('')
    else:
        hosts = [args.host]
    for host in hosts:
        if args.command:
            host_id = db_fetch_hostid('', host)
            host = db_read_host('', host_id, config)
            host_func = getattr(admin, args.command[0],
                                admin.version_check)
            print_out(host_func(host, args.command[1]))
            flag = False
        else:
            flag = run_host(host, config)
        if flag is True:
            reboot_list.append(f'\t{host}')
    if len(reboot_list) > 0:
        print(f'\n\nThe following hosts need to be rebooted:')
        print_out(reboot_list)
    # Clean up
    del os.environ['CONN']


if __name__ == '__main__':
    import sys
    main(sys.argv)
