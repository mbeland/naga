#!/usr/bin/env python3
# naga.py

# Imports
from fabric import Connection, Config
from invoke import exceptions
from cmd import Cmd
from getpass import getpass
from backend import Host, db_add_app, db_add_host, db_fetch_hostid, db_add_child,\
                    db_fetch_hostid, db_read_host, db_connector,\
                    db_fetch_hostlist, db_fetch_children, db_delete_host,\
                    db_fetch_parent_id, db_fetch_hostname, db_delete_child,\
                    db_delete_app, db_fetch_apps
import admin
import argparse
import math
import os
import re

class NagaPrompt(Cmd):
    intro = 'Welcome to the Naga shell. Type help or ? to list commands.\n'
    prompt = 'naga> '
    reboot_list = []
    hosts = {}
    config = None


    def do_add_app(self, inp):
        '''Add app to specified host in db and reload host'''
        id = pick_host(inp, 'Host for new app? ')
        app = str(input("New app function? ")).lower()
        db_add_app('', id, app)
        self.do_load(db_fetch_hostname('', id))


    def do_delete(self, inp):
        '''Delete host entry from database'''
        id = pick_host(inp, "Delete which host: ")
        if str(db_fetch_children('', id)[0]) != "0":
            print("WARNING: selected host contains defined children")
        print(f'Deleting host {inp}: Continue?')
        ans = input("Type \'yes\' to confirm deletion: ")
        if ans.strip() == "yes":
            parent = db_fetch_parent_id('', id)
            if parent:
                db_delete_child('', parent, id)
            db_delete_host('', id)
            print("Deleted. Defined hosts:")
            print_out(print_cols(db_fetch_hostlist('')))
        else:
            print("Deletion aborted.")


    def do_delete_app(self, inp):
        '''Remove app from specified host in db and reload host'''
        id = pick_host(inp, 'Host to modify? ')
        apps = db_fetch_apps('', id)
        hostname = db_fetch_hostname('', id)
        print(f'Configured apps on {hostname}:')
        print_out(print_cols(apps))
        app = str(input(f'App to remove? ')).lower()
        db_delete_app('', id, app)
        print('Done.')
        self.do_load(hostname)


    def do_exit(self, inp):
        '''Exit to system shell. Shorthand: x q'''
        if len(self.reboot_list) > 0:
            print(f'\n\nThe following hosts need to be rebooted:')
            print_out(self.reboot_list)
        print('Bye.')
        return True


    def do_fetch_parent(self, inp):
        '''Fetch id of host parent from database'''
        id = pick_host(inp, "Find parent of: ")
        parent = db_fetch_parent_id('', id)
        if parent is None:
            print(f'{inp} is not a child host')
        else:
            parent = db_fetch_hostname('', parent)
            print(f'{inp} is a child of {parent}')


    def do_list(self, inp):
        '''List configured hosts in database'''
        print(f'Defined hosts:')
        print_out(print_cols(db_fetch_hostlist('')))


    def do_load(self, inp):
        '''Load specified hosts from database - \'all\' for all'''
        if self.config is None:
            self.config = get_sudo()
        if inp == 'all':
            hosts = db_fetch_hostlist('')
        else:
            hosts = str(inp).split(',')
        for host in hosts:
            id = pick_host(host, f'{host} not found - load which host? ')
            host = db_read_host('', id, self.config)
            self.hosts[host.name] = host
        print("Loaded hosts:")
        print_out(print_cols((list(self.hosts.keys()))))


    def do_new(self, inp):
        '''Create new host entry for the database'''
        if self.config is None:
            self.config = get_sudo()
        host = add_host(self.config)
        self.hosts[host.name] = host
        print("Loaded hosts:")
        print_out(print_cols((list(self.hosts.keys()))))


    def do_reboot(self, inp):
        '''Reboot specified hosts'''
        id = pick_host(inp, "Reboot which host? ")
        hostname = db_fetch_hostname('', id)
        host = self.do_load(hostname)
        flag = str(input(f'Shutdown {hostname}? (Y/N) [default=N]: ')).lower()
        if flag == "y":
            flag = True
        else:
            flag = False
        time = input("Time to reboot? (+INT minutes delay or HH:MM) [Default: +1]: ")
        if time == "":
            time = '+1'
        print_out(admin.reboot(self.hosts[hostname], time=time, halt=flag))


    def default(self, inp):
        if inp == 'x' or inp == 'q':
            return self.do_exit(inp)

        print("Default: {}".format(inp))


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
        host_id = db_fetch_hostid('', str(child).lower())
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


def pick_host(inp, query):
    '''
    Select host from db list
    :param inp: string of hostname
    :param query: prompt for input string if no match
    :return: Host_id of matching hostname
    '''
    if str(inp).lower() not in db_fetch_hostlist(''):
        print("Defined hosts:")
        print_out(print_cols(db_fetch_hostlist('')))
        inp = input(query)
    return db_fetch_hostid('', str(inp).lower())


def print_cols(list):
    '''
    Create a list of four 20-character column stringsfrom input strings
    :param list: List of string objects
    :return: List of formatted strings
    '''
    out = []
    while len(list) > 0:
        outstring = ''
        if len(list) <= 4:
            for i in range(0,len(list)):
                outstring = outstring + str(list.pop(0)).rjust(20," ")
            out.append(outstring)
        else:
            for j in range(0,4):
                outstring = outstring + str(list.pop(0)).rjust(20," ")
            out.append(outstring)
    return out


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
