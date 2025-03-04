import signal
import time

from crud_posgres_func import truncate_stocktable, upload_data, get_client_activity, update_data
from engine import DbSessions
from env_config import env
from firebird_func import firebird_data, get_fdb_activity
from model import StockTable, Activity
from utils import managed_sessions, notify_via_telegram


def refresh_table_data(sessions: DbSessions) -> dict:
    from_firebird: list = firebird_data()
    print('Данные из Firebird получены')
    for session_factory in [sessions.local, sessions.ssh]:
        with session_factory() as session:
            truncate_stocktable(session=session)
            upload_data(session=session, table=StockTable, data=from_firebird)
    print('Таблицы наличия обновлены')
    return {'from_firebird': from_firebird, 'status': True}


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
                if already_refreshed is True:
                    update_data(session=ssh_session, table=StockTable, data=inserted_data)
                    current_qty: dict = update_data(session=local_session, table=StockTable, data=inserted_data)
                    notify_via_telegram(bot=env.tg_bot, chat=env.chat_id, sale_data=inserted_data, current_qty=current_qty)
            already_refreshed = False
            time.sleep(time_cycle)