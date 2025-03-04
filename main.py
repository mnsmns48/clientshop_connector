import sys
import traceback

from core import refresh_table_data, ciclyc_update
from engine import DbSessions
from env_config import env
from model import Base


def main():
    print('start')
    sessions = DbSessions(secret=env)
    Base.metadata.create_all(sessions.local_engine)
    Base.metadata.create_all(sessions.ssh_engine)
    refreshed = refresh_table_data(sessions=sessions)
    # addon_desc_from_dtube(sessions=sessions, data=refreshed['from_firebird'])
    ciclyc_update(time_cycle=60, sessions=sessions, already_refreshed=refreshed['status'])


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        traceback.print_exc()
        sys.exit(1)
