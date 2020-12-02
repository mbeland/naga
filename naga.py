#!/usr/bin/env python3
# naga.py

# Imports
from fabric import Connection, Config
from invoke import exceptions
from getpass import getpass
import admin
import argparse
import re
import sqlite3


class Host:
    '''
    Host Definition Class
    :param name: hostname from .ssh config
    :param updater: bare function name for updating host
    :param git: Update git repos (Boolean)
    :param appList: list of function names to execute during updates
    :param configuration: Configuration object for Connection class
    '''
    def __init__(self, name, updater, appList, configuration):
        self.name = name
        self.updater = updater
        self.appList = appList
        self.conn = Connection(name, config=configuration)


def add_host(db_conn, config=None):
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
    host = Host(name, updater, appList, config)
    if re.search('^Y', (input(f'Save {host.name}? [y/N]: ')).capitalize()):
        print(f'{host.name} added as host id {db_add_host(db_conn, host)}')
    return host


def db_add_app(db_conn, host_id, app):
    '''
    Add update function assignment to host in db
    :param db_conn: DB connection object
    :param host_id: DB rowid for host
    :param app: Bare function name to execute
    '''
    apps_sql = '''INSERT INTO apps(host,function) VALUES(?,?)'''
    c = db_conn.cursor()
    c.execute(apps_sql, (host_id, app))
    db_conn.commit()


def db_add_host(db_conn, host):
    '''
    Write Host object info to db
    :param db_conn: DB connection object
    :param host: Host instance
    :return: host id
    '''
    host_sql = '''INSERT INTO hosts(name,updater,git) VALUES(?,?,?)'''
    c = db_conn.cursor()
    host_tuple = (host.name, host.updater, host.git)
    c.execute(host_sql, host_tuple)
    db_conn.commit()
    host_id = c.lastrowid
    for app in host.appList:
        db_add_app(db_conn, host_id, app)
    return host_id


def db_conn(db_file):
    '''
    Connect to Hosts database file
    :param db_file: database file
    :return: Connection object or None
    '''
    conn = None
    try:
        conn = sqlite3.connect(db_file)
    except sqlite3.Connection.Error as e:
        print(e)
    return conn


def db_create_db(db_conn):
    '''
    Populate new DB with tables
    :param db_conn: SQLite3 Connection object
    :return:
    '''
    hosts_table_sql = '''
    CREATE TABLE IF NOT EXISTS hosts (
        id integer PRIMARY KEY,
        name text UNIQUE NOT NULL,
        updater text NOT NULL
    );
    '''
    apps_table_sql = '''
    CREATE TABLE IF NOT EXISTS apps (
        id integer PRIMARY KEY,
        host integer NOT NULL,
        function text NOT NULL
    );
    '''
    db_create_table(db_conn, hosts_table_sql)
    db_create_table(db_conn, apps_table_sql)


def db_create_table(db_conn, create_table_sql):
    '''
    Create sqlite3 table
    :param db_conn: SQLite3 Connection object
    :param create_table_sql: a CREATE TABLE statement
    :return:
    '''
    try:
        c = db_conn.cursor()
        c.execute(create_table_sql)
    except sqlite3.Error as e:
        print(e)


def db_delete_host(db_conn, host_id):
    '''
    Remove host record from db
    :param db_conn: db connection object
    :param host_id: id of record to delete
    '''
    sql_hosts = '''DELETE FROM hosts WHERE id=?'''
    sql_app = '''DELETE FROM apps WHERE id=?'''
    c = db_conn.cursor()
    c.execute(sql_hosts, (host_id,))
    c.execute(sql_app, (host_id,))
    c.commit()


def db_fetch_hostid(db_conn, hostname):
    '''
    Return the host_id for a given hostname from the db
    :param db_conn: db connection object
    :param hostname: hostname for host
    :return: integer host_id or None
    '''
    sql = '''SELECT id FROM hosts WHERE name=?'''
    c = db_conn.cursor()
    c.execute(sql, (hostname,))
    host_id = c.fetchone()
    if host_id:
        return host_id[0]
    else:
        return None


def db_fetch_hostlist(db_conn):
    '''
    Return list of hostnames from db
    :param db_conn: db connection object
    :return: list of hostnames
    '''
    sql = '''SELECT name FROM hosts'''
    nameList = []
    c = db_conn.cursor()
    c.execute(sql)
    names = c.fetchall()
    for name in names:
        nameList.append(name[0])
    return nameList


def db_read_host(db_conn, host_id, config):
    '''
    Read from db, create new host object
    :param db_conn: DB connection object
    :param host_id: host_id of host in db
    :param config: Configuration object
    :return: Host object or None
    '''
    sql_hosts = '''SELECT name, updater FROM hosts WHERE id = ?'''
    sql_apps = '''SELECT function FROM apps WHERE host = ?'''
    c = db_conn.cursor()
    c.execute(sql_hosts, (host_id,))
    row = c.fetchone()
    if row:
        name, updater = row
    else:
        return None
    c.execute(sql_apps, (host_id,))
    rows = c.fetchall()
    appList = []
    for row in rows:
        appList.append(row[0])
    return Host(name, updater, appList, config)


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
        if len(line) > 0:
            print(line)


def run_host(db_conn, host, config=None):
    '''
    Execute updater, host appList updaters, print output
    :param db_conn: db connection object
    :param host: hostname
    :param config: Connection Configuration object
    '''
    host_id = db_fetch_hostid(db_conn, host)
    host = db_read_host(db_conn, host_id, config)
    host_func = getattr(admin, host.updater, admin.version_check)
    print_out(host_func(host))
    for app in host.appList:
        app_func = getattr(admin, app, admin.version_check)
        print_out(app_func(host))


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("host", help="Friendly name of system to target")
    parser.add_argument("-db", "--database", type=str,
                        help="SQLite3 db file to use [default=hosts.db")
    parser.add_argument("-cmd", "--command", nargs=2,
                        help="Function to execute on listed host(s)")
    args = parser.parse_args()
    if args.database is None:
        args.database = 'hosts.db'
    config = get_sudo()
    db = db_conn(args.database)
    if args.host == "all":
        hosts = db_fetch_hostlist(db)
    else:
        hosts = [args.host]
    for host in hosts:
        if args.command:
            host_id = db_fetch_hostid(db, host)
            host = db_read_host(db, host_id, config)
            host_func = getattr(admin, args.command[0],
                                admin.version_check)
            print_out(host_func(host, args.command[1]))
        else:
            run_host(db, host, config)


if __name__ == '__main__':
    import sys
    main(sys.argv)
