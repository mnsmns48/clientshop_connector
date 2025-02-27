import sys
import time
import signal
import traceback
from contextlib import contextmanager

from engine import DbSessions
from env_config import env
from firebird_func import firebird_data, get_fdb_activity
from model import StockTable, Activity, Base
from posgres_func import truncate_table, upload_data, get_client_activity, update_data
from utils import notify_via_telegram


@contextmanager
def managed_sessions(sessions):
    local_session = sessions.local()
    ssh_session = sessions.ssh()
    try:
        yield local_session, ssh_session
    finally:
        local_session.close()
        ssh_session.close()


def refresh_table_data(sessions: DbSessions) -> bool:
    from_firebird: list = firebird_data()
    print('Данные из Firebird получены')
    for session_factory in [sessions.local, sessions.ssh]:
        with session_factory() as session:
            truncate_table(session=session, table=StockTable.__table__)
            upload_data(session=session, table=StockTable, data=from_firebird)
    print('Таблицы наличия обновлены')
    result = bool()
    return result


def ciclyc_update(time_cycle: int, sessions: DbSessions, already_refreshed: bool):
    print('Ожидаю продажи')

    def signal_handler(sig, frame):
        raise SystemExit

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    with managed_sessions(sessions) as (local_session, ssh_session):
        while True:
            data_client = get_client_activity(session=ssh_session)
            fdb_activity = get_fdb_activity()
            difference = len(fdb_activity) - len(data_client)
            if difference:
                inserted_data = fdb_activity[-difference:]
                upload_data(session=ssh_session, table=Activity, data=inserted_data)
                upload_data(session=local_session, table=Activity, data=inserted_data)
                if not already_refreshed:
                    update_data(session=ssh_session, table=StockTable, data=inserted_data)
                    current_qty: dict = update_data(session=local_session, table=StockTable, data=inserted_data)
                    notify_via_telegram(bot=env.tg_bot,
                                        chat=env.chat_id,
                                        sale_data=inserted_data,
                                        current_qty = current_qty)
            already_refreshed = False
            time.sleep(time_cycle)


def main():
    print('start')
    sessions = DbSessions(secret=env)
    Base.metadata.create_all(sessions.local_engine)
    Base.metadata.create_all(sessions.ssh_engine)
    refreshed = refresh_table_data(sessions=sessions)

    ciclyc_update(time_cycle=60, sessions=sessions, already_refreshed=refreshed)


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        traceback.print_exc()
        sys.exit(1)
