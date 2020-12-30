from naga import db_fetch_hostlist, db_fetch_hostid, db_read_host, get_sudo


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


def test_all():
    targets = {}
    config = get_sudo()
    hosts = db_fetch_hostlist('')
    for host in hosts:
        id = db_fetch_hostid('', host)
        host = db_read_host('', id, config)
        targets[host.name] = host
    return targets
