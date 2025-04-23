import signal
import time
from datetime import datetime

from tenacity import stop_after_attempt, retry, wait_fixed

from crud_posgres_func import truncate_stocktable, upload_data, get_client_activity, update_data
from description import addon_desc_from_dtube
from engine import DbSessions
from env_config import env
from firebird_func import firebird_data, get_fdb_activity
from model import StockTable, Activity
from utils import notify_via_telegram


@retry(stop=stop_after_attempt(500), wait=wait_fixed(60))
def refresh_table_data() -> dict:
    from_firebird_only: list = firebird_data()
    print(f'{datetime.now().strftime("%H:%M:%S")} Данные из ClientShop получены')
    from_firebird_with_desc: dict = addon_desc_from_dtube(firebird_data=from_firebird_only)
    table_data = from_firebird_with_desc.get('data') \
        if from_firebird_with_desc['status'] is True else from_firebird_only
    sessions = DbSessions(secret=env)
    with sessions.get_local_session() as local_ses, sessions.get_ssh_session() as ssh_ses:
        try:
            truncate_stocktable(session=local_ses)
            upload_data(session=local_ses, table=StockTable, data=table_data)
            truncate_stocktable(session=ssh_ses)
            upload_data(session=ssh_ses, table=StockTable, data=table_data)
        except Exception as e:
            print(f"Ошибка при обновлении данных при первичном обновлении: {e}")
            raise
    print(f'{datetime.now().strftime("%H:%M:%S")} Таблицы наличия обновлены')
    return {'from_firebird': table_data, 'status': True}


@retry(stop=stop_after_attempt(500), wait=wait_fixed(60))
def ciclyc_update(time_cycle: int, already_refreshed: bool):
    print(f'{datetime.now().strftime("%H:%M:%S")} Ожидаю продажи')

    def signal_handler(sig, frame):
        raise SystemExit

    signal.signal(signal.SIGINT, signal_handler)
    try:
        sessions = DbSessions(secret=env)
        with sessions.get_local_session() as local_ses, sessions.get_ssh_session() as ssh_ses:
            while True:
                data_client = get_client_activity(session=local_ses)
                fdb_activity = get_fdb_activity()
                difference = len(fdb_activity) - len(data_client)
                if difference:
                    inserted_data = fdb_activity[-difference:]
                    upload_data(session=ssh_ses, table=Activity, data=inserted_data)
                    upload_data(session=local_ses, table=Activity, data=inserted_data)
                    if not already_refreshed:
                        update_data(session=ssh_ses, table=StockTable, data=inserted_data)
                        current_qty: dict = update_data(session=local_ses, table=StockTable, data=inserted_data)
                        notify_via_telegram(bot=env.tg_bot, chat=env.chat_id, sale_data=inserted_data,
                                            current_qty=current_qty)
                already_refreshed = False
                time.sleep(time_cycle)
    except Exception as e:
        print(f"Ошибка в цикле обновления при цикле: {e}")
        raise
