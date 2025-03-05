import signal
import time

from crud_posgres_func import truncate_stocktable, upload_data, get_client_activity, update_data
from description import addon_desc_from_dtube
from engine import DbSessions
from env_config import env
from firebird_func import firebird_data, get_fdb_activity
from model import StockTable, Activity
from utils import managed_sessions, notify_via_telegram


def refresh_table_data(sessions: DbSessions) -> dict:
    from_firebird_only: list = firebird_data()
    print('Данные из ClientShop получены')
    from_firebird_with_desc: dict = addon_desc_from_dtube(firebird_data=from_firebird_only)
    table_data = from_firebird_with_desc.get('data') if from_firebird_with_desc['status'] is True else from_firebird_only
    for session_factory in [sessions.local, sessions.ssh]:
        with session_factory() as session:
            truncate_stocktable(session=session)
            upload_data(session=session, table=StockTable, data=table_data)
    print('Таблицы наличия обновлены')
    return {'from_firebird': table_data, 'status': True}


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
                if already_refreshed is False:
                    update_data(session=ssh_session, table=StockTable, data=inserted_data)
                    current_qty: dict = update_data(session=local_session, table=StockTable, data=inserted_data)
                    notify_via_telegram(bot=env.tg_bot, chat=env.chat_id, sale_data=inserted_data, current_qty=current_qty)
            already_refreshed = False
            time.sleep(time_cycle)