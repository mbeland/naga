from naga import *
from admin import *


def test():
    targets = {}
    db = db_conn('hosts.db')
    print(f'Defined hosts: {db_fetch_hostlist(db)}')
    hosts = input('Load hosts:').split(',')
    config = get_sudo()
    for host in hosts:
        id = db_fetch_hostid(db, host)
        host = db_read_host(db, id, config)
        targets[host.name] = host
    return targets
