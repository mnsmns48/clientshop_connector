from contextlib import contextmanager

import fdb
from tenacity import retry, stop_after_attempt, wait_exponential
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sshtunnel import SSHTunnelForwarder

from env_config import Environs, env


@retry(stop=stop_after_attempt(500), wait=wait_exponential(multiplier=60, min=60, max=60))
def create_ssh_tunnel() -> SSHTunnelForwarder:
    tunnel = SSHTunnelForwarder(
        ssh_address_or_host=(env.ssh_host, env.ssh_port),
        ssh_username=env.ssh_username,
        ssh_password=env.ssh_password,
        remote_bind_address=(env.ssh_db_host, env.ssh_db_port))
    tunnel.start()
    return tunnel


class DbSessions:
    def __init__(self, secret: Environs):
        self.secret = secret
        self.local_engine_line = (f'postgresql+psycopg2://'
                                  f'{secret.local_db_username}:'
                                  f'{secret.local_db_password}@'
                                  f'{secret.local_db_host}:'
                                  f'{secret.local_db_port}/'
                                  f'{secret.local_database}')
        self.local_engine = create_engine(self.local_engine_line)
        self.local_session_maker = sessionmaker(bind=self.local_engine)

    def get_ssh_session(self):
        tunnel = create_ssh_tunnel()
        ssh_engine_line = (f'postgresql+psycopg2://'
                           f'{self.secret.ssh_db_username}:'
                           f'{self.secret.ssh_db_password}@'
                           f'localhost:{tunnel.local_bind_port}/'
                           f'{self.secret.ssh_database}')
        ssh_engine = create_engine(ssh_engine_line)
        ssh_session_maker = sessionmaker(bind=ssh_engine)
        session = ssh_session_maker()
        return session

    def get_local_session(self):
        return self.local_session_maker()



fdb_connection = fdb.connect(dsn=env.fdb_dsn, user=env.fdb_user, password=env.fdb_password)
