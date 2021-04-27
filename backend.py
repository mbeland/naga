#!/usr/bin/env python3
# naga.py

# Imports
from fabric import Connection, Config
import logging
import sqlite3
import os


class Host:
    '''
    Host Definition Class
    :param name: hostname from .ssh config
    :param updater: bare function name for updating host
    :param git: Update git repos (Boolean)
    :param appList: list of function names to execute during updates
    :param configuration: Configuration object for Connection class
    '''
    def __init__(self, name, updater, appList, configuration, children):
        self.name = name
        self.updater = updater
        self.appList = appList
        self.configuration = configuration
        self.conn = Connection(name, config=configuration)
        self.children = children


class sqlite_connection(object):
    """sqlite3 db connection"""    

    def __init__(self, connection_string=os.environ.get('CONN', 'hosts.db')):
        self.connection_string = connection_string
        self.connector = None    
        
        
    def __enter__(self):
        self.connector = sqlite3.connect(self.connection_string)
        return self    
    
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_tb is None:
            self.connector.commit()
        else:
            self.connector.rollback()
        self.connector.close()
    

def db_connector(func):
    def with_connection_(cnn, *args, **kwargs):
        conn_str = os.environ.get('CONN', 'hosts.db')
        cnn = sqlite3.connect(conn_str)
        try:
            rv = func(cnn, *args, **kwargs)
        except Exception:
            cnn.rollback()
            logging.error("Database connection error")
            raise
        else:
            cnn.commit()
        finally:
            cnn.close()        
        
        return rv
    return with_connection_


@db_connector
def db_add_app(db, host_id, app):
    '''
    Add update function assignment to host in db
    :param db: DB Connector (use db_connector func)
    :param host_id: DB rowid for host
    :param app: Bare function name to execute
    '''
    apps_sql = '''INSERT INTO apps(host,function) VALUES(?,?)'''
    c = db.cursor()
    c.execute(apps_sql, (host_id, app))
    db.commit()


@db_connector
def db_add_child(db, parent_id, child_id):
    '''
    Add child entry to database host record
    :param db: DB Connector (use db_connector func)
    :param parent_id: host_id record for parent machine
    :param child_id: host_id record for child machine
    :return: updated host.children list for oarent_id
    '''
    update_sql = '''UPDATE hosts SET children = ? WHERE id = ?'''
    c = db.cursor()
    children = db_fetch_children('', parent_id)
    if children[0] == '0':
        c.execute(update_sql, (child_id, parent_id))
    else:
        children.append(str(child_id))
        print(f'DEBUG: children is {children}')
        children = ",".join(children)
        c.execute(update_sql, (children, parent_id))
    db.commit()
    return db_fetch_children('', parent_id)


@db_connector
def db_add_host(db, host):
    '''
    Write Host object info to db
    :param db: DB Connector (use db_connector func)
    :param host: Host instance
    :return: host id
    '''
    host_sql = '''INSERT INTO hosts(name,updater,children) VALUES(?,?,?)'''
    c = db.cursor()
    if host.children == []:
        children = '0'
    else:
        children = host.children
    host_tuple = (host.name, host.updater, children)
    c.execute(host_sql, host_tuple)
    db.commit()
    host_id = c.lastrowid
    for app in host.appList:
        db_add_app('', host_id, app)
    return host_id


def db_create_db():
    '''
    Populate new DB with tables
    :param db_conn: SQLite3 Connection object
    :return:
    '''
    hosts_table_sql = '''
    CREATE TABLE IF NOT EXISTS hosts (
        id integer PRIMARY KEY,
        name text UNIQUE NOT NULL,
        updater text NOT NULL,
        children text
    );
    '''
    apps_table_sql = '''
    CREATE TABLE IF NOT EXISTS apps (
        id integer PRIMARY KEY,
        host integer NOT NULL,
        function text NOT NULL
    );
    '''
    db_create_table('', hosts_table_sql)
    db_create_table('', apps_table_sql)


@db_connector
def db_create_table(db, create_table_sql):
    '''
    Create sqlite3 table
    :param db: DB Connector (use db_connector func)
    :param create_table_sql: a CREATE TABLE statement
    :return:
    '''
    c = db.cursor()
    c.execute(create_table_sql)


@db_connector
def db_delete_app(db, host, app_name):
    '''
    Remove app from db host record and Host object
    :param db: DB Connector (use db_connector func)
    :param host_id: Host object
    :param app_name: App function to remove
    :return: host object
    '''
    sql = '''DELETE FROM apps WHERE host = ? AND function = ?'''
    host_id = db_fetch_hostid('', host.name)
    c = db.cursor()
    c.execute(sql, (host_id, app_name))
    return db_read_host('', host_id, host.configuration)


@db_connector
def db_delete_child(db, parent, child_id):
    '''
    Delete child record from db and host object
    :param db: DB Connector (use db_connector func)
    :param parent: Host object
    :param child_id: host_id of child record
    :return: host object
    '''
    sql = '''UPDATE hosts SET children = ? WHERE id = ?'''
    c = db.cursor()
    parent_id = db_fetch_hostid('', parent.name)
    children = db_fetch_children('', parent_id)
    children.remove(str(child_id))
    c.execute(sql, ','.join(children), parent)
    return db_read_host('', parent_id, parent.configuration)


@db_connector
def db_delete_host(db, host_id):
    '''
    Remove host record from db
    :param db: DB Connector (use db_connector func)
    :param host_id: id of record to delete
    '''
    sql_hosts = '''DELETE FROM hosts WHERE id=?'''
    sql_app = '''DELETE FROM apps WHERE host=?'''
    c = db.cursor()
    c.execute(sql_hosts, (host_id,))
    c.execute(sql_app, (host_id,))


@db_connector
def db_fetch_children(db, host_id):
    '''
    Get children from host db for host_id
    :param db: DB Connector (use db_connector func)
    :param host_id: list of host_ids for child servers
    '''
    select_sql = '''SELECT children FROM hosts WHERE id=?'''
    c = db.cursor()
    c.execute(select_sql, (host_id,))
    return c.fetchone()[0].split(',')


@db_connector
def db_fetch_hostid(db, hostname):
    '''
    Return the host_id for a given hostname from the db
    :param db: DB Connector (use db_connector func)
    :param hostname: hostname for host
    :return: integer host_id or None
    '''
    sql = '''SELECT id FROM hosts WHERE name=?'''
    c = db.cursor()
    c.execute(sql, (hostname,))
    host_id = c.fetchone()
    if host_id:
        return host_id[0]
    else:
        return None


@db_connector
def db_fetch_hostlist(db):
    '''
    Return list of hostnames from db
    :param db: DB Connector (use db_connector func)
    :return: list of hostnames
    '''
    sql = '''SELECT name FROM hosts'''
    nameList = []
    c = db.cursor()
    c.execute(sql)
    names = c.fetchall()
    for name in names:
        nameList.append(name[0])
    return nameList


@db_connector
def db_read_host(db, host_id, config):
    '''
    Read from db, create new host object
    :param db: DB Connector (use db_connector func)
    :param host_id: host_id of host in db
    :param config: Configuration object
    :return: Host object or None
    '''
    sql_hosts = '''SELECT name, updater FROM hosts WHERE id = ?'''
    sql_apps = '''SELECT function FROM apps WHERE host = ?'''
    c = db.cursor()
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
    children = db_fetch_children('', host_id)
    return Host(name, updater, appList, config, children)
