from naga import *
from admin import *


def test():
    targets = {}
    print(f'Defined hosts: {db_fetch_hostlist("")}')
    hosts = input('Load hosts:').split(',')
    config = get_sudo()
    for host in hosts:
        id = db_fetch_hostid('', host)
        host = db_read_host('', id, config)
        targets[host.name] = host
    return targets
