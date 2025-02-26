import time
import signal
from contextlib import contextmanager

from sqlalchemy.orm import Session

from engine import DbSessions
from env_config import env
from firebird_func import firebird_data, get_fdb_activity
from model import StockTable
from posgres_func import truncate_table, upload_data, get_client_activity


@contextmanager
def managed_sessions(sessions):
    local_session = sessions.local()
    ssh_session = sessions.ssh()
    try:
        yield local_session, ssh_session
    finally:
        local_session.close()
        ssh_session.close()


def refresh_table_data(sessions: DbSessions):
    from_firebird: list = firebird_data()
    print('Данные из Firebird получены')
    for session_factory in [sessions.local, sessions.ssh]:
        with session_factory() as session:
            truncate_table(session=session, table=StockTable.__table__)
            upload_data(session=session, table=StockTable, data=from_firebird)
    print('Таблицы наличия обновлены')


def ciclyc_update(time_cycle: int, sessions: DbSessions):
    def signal_handler(sig, frame):
        print('сработал signal')
        raise SystemExit

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    with managed_sessions(sessions) as (local_session, ssh_session):
        while True:
            data_client = get_client_activity(session=local_session)
            fdb_activity = get_fdb_activity()
            difference = len(fdb_activity) - len(data_client)
            print(difference)
            if difference:
                inserted_data = fdb_activity[-difference:]


            print(data_client)
            time.sleep(time_cycle)


def main():
    sessions = DbSessions(secret=env)
    # Base.metadata.create_all(sessions.local_engine)
    # Base.metadata.create_all(sessions.ssh_engine)
    # refresh_table_data(sessions=sessions)
    ciclyc_update(time_cycle=60, sessions=sessions)


if __name__ == '__main__':
    main()
