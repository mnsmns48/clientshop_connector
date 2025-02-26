import time
import signal

from sqlalchemy.orm import Session

from engine import DbSessions
from env_config import env
from firebird_func import firebird_data, get_fdb_activity
from model import StockTable
from posgres_func import truncate_table, upload_data, get_client_activity






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
    signal.signal(signal.SIGINT, signal_handler)
    with sessions.local() as local_session, sessions.ssh() as ssh_session:
        while True:

            data_client = get_client_activity(session=local_session)
            fdb_activity = get_fdb_activity()
            difference = len(fdb_activity) - len(data_client)
            print(difference)
            if difference:
                inserted_data = fdb_activity[-difference:]
            time.sleep(time_cycle)

# (opened_sessions=[local_session, ssh_session])


def main():
    sessions = DbSessions(secret=env)
    # Base.metadata.create_all(sessions.local_engine)
    # Base.metadata.create_all(sessions.ssh_engine)
    # refresh_table_data(sessions=sessions)
    ciclyc_update(time_cycle=60, sessions=sessions)


if __name__ == '__main__':
    main()

