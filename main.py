import time

from sqlalchemy import select
from sqlalchemy.exc import ArgumentError
from sqlalchemy.orm import sessionmaker
from sshtunnel import SSHTunnelForwarder
from config import env, create_ssh_tunnel
from engine import Init_Engine
from model import Base


def init_sessions() -> dict['str': sessionmaker]:
    local = Init_Engine(username=env.local_db_username,
                        password=env.local_db_password,
                        host=env.local_db_host,
                        port=env.local_db_port,
                        db_name=env.local_database)
    tunnel = create_ssh_tunnel()
    ssh = Init_Engine(username=env.ssh_db_username,
                      password=env.ssh_db_password,
                      host=env.ssh_db_host,
                      port=tunnel.local_bind_port,
                      db_name=env.ssh_database)
    return {'local': local,
            'ssh': ssh}


def main():
    sessions = init_sessions()
if __name__ == '__main__':
    main()
