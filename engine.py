import fdb
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sshtunnel import SSHTunnelForwarder

from env_config import Environs, env


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
        self.local_engine_line = (f'postgresql+psycopg2://'
                                  f'{secret.local_db_username}:'
                                  f'{secret.local_db_password}@'
                                  f'{secret.local_db_host}:'
                                  f'{secret.local_db_port}/'
                                  f'{secret.local_database}')
        self.local_engine = create_engine(self.local_engine_line)
        self.local = sessionmaker(bind=self.local_engine)
        tunnel = create_ssh_tunnel()
        self.ssh_engine_line = (f'postgresql+psycopg2://'
                                f'{secret.ssh_db_username}:'
                                f'{secret.ssh_db_password}@'
                                f'{secret.ssh_db_host}:'
                                f'{tunnel.local_bind_port}/'
                                f'{secret.ssh_database}')
        self.ssh_engine = create_engine(self.ssh_engine_line)
        self.ssh = sessionmaker(self.ssh_engine)

fdb_connection = fdb.connect(dsn=env.fdb_dsn, user=env.fdb_user, password=env.fdb_password)