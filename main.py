import sys
import traceback
from datetime import datetime

from core import refresh_table_data, ciclyc_update
from engine import DbSessions
from env_config import env
from model import Base


def main():
    print(f'{datetime.now().strftime("%H:%M:%S")} start')
    sessions = DbSessions(secret=env)
    refreshed = refresh_table_data(sessions=sessions)
    ciclyc_update(time_cycle=60, sessions=sessions, already_refreshed=refreshed['status'])


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        traceback.print_exc()
        sys.exit(1)
