#!/usr/bin/env python3
# sshclient.py

# Import statements
from getpass import getpass
from pathlib import Path
from paramiko import (SSHClient, AutoAddPolicy, RSAKey,
                      AuthenticationException, SSHException,
                      PasswordRequiredException)
from scp import SCPClient, SCPException
from multitool import Snitch
log = Snitch(__name__, level='DEBUG')


class RemoteClient:
    '''Client for connecting to remote host via SSH & SCP'''
    def __init__(self, host, user, key='id_rsa', remote_path='~'):
        self.host = host
        self.user = user
        self.remote_path = remote_path
        self.key_file = str(Path.home()) + '/.ssh/' + key
        self.client = None
        self.scp = None
        self.conn = None

    def _get_ssh_key(self, pword=None):
        '''Fetch locally stored SSH key'''
        try:
            self.ssh_key = RSAKey.from_private_key_file(self.key_file)
            log.debug(f'Found RSA key at {self.key_file}')
        except PasswordRequiredException:
            pword = getpass('Enter SSH key password:')
            self.ssh_key = RSAKey.from_private_key_file(self.key_file,
                                                        password=pword)
            log.debug(f'Found passworded RSA key at {self.key_file}')
        except SSHException as e:
            log.error(e)

    def _connect(self):
        '''Open connection to remote host'''
        if self.conn is None:
            try:
                self._get_ssh_key()
                self.client = SSHClient()
                self.client.load_system_host_keys()
                self.client.set_missing_host_key_policy(AutoAddPolicy())
                self.client.connect(
                    self.host,
                    username=self.user,
                    pkey=self.ssh_key,
                    look_for_keys=True,
                    timeout=5000
                )
                self.scp = SCPClient(self.client.get_transport())
            except (AuthenticationException, SSHException) as e:
                log.error(f'Connection failed: {e}')
                raise e
        return self.client

    def set_loglevel(self, level="ERROR"):
        log.setLevel(level)
        return log.getLevelName()

    def disconnect(self):
        '''Close ssh connection'''
        if self.client:
            self.client.close()
        if self.scp:
            self.scp.close()

    def execute(self, command):
        '''
        Execute command on remote host.

        :param command: Unix command as a single string.
        :type command: str
        '''
        self.conn = self._connect()
        stdin, stdout, stderr = self.client.exec_command(command)
        stdout.channel.recv_exit_status()
        for error in stderr.readlines():
            log.error(f'INPUT: {command} | ERR: {error}')
        return stdout.readlines()

    def upload(self, file, r=False):
        '''
        Upload file to a remote directory.

        :param files: filename as string.
        :type files: str
        '''
        self.conn = self._connect()
        try:
            self.scp.put(file, recursive=r, remote_path=self.remote_path)
        except SCPException as e:
            log.error(f'File transfer error: {e}')
            raise e
        log.info(f'Uploaded {self.remote_path}/{file} on {self.host}')

    def download(self, file, r=False):
        '''
        Download file from remote directory.

        :param files: filename as string
        :type files: str
        '''
        self.conn = self._connect()
        try:
            self.scp.get(file, recursive=r)
        except SCPException as e:
            log.error(f'File transfer error: {e}')
            raise e
        log.info(f'Pulled {self.remote_path}/{file} from {self.host}')
