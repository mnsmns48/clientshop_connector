from datetime import datetime
from typing import Type, Any, Sequence, Literal

from retry import retry
from sqlalchemy import text, func, select, Row, delete, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from sshtunnel import BaseSSHTunnelForwarderError

from model import StockTable, Activity, Base


@retry(BaseSSHTunnelForwarderError, tries=5000, delay=30)
def truncate_stocktable(session: Session) -> None:
    stmt = """TRUNCATE TABLE public.stocktable"""
    try:
        session.execute(text(stmt))
        session.commit()
    except SQLAlchemyError as e:
        session.rollback()
        raise e


@retry(BaseSSHTunnelForwarderError, tries=5000, delay=30)
def upload_data(session: Session, table: Literal[StockTable: Base | Activity: Base], data: list):
    session.execute(insert(table).on_conflict_do_nothing(), data)
    session.commit()


@retry(BaseSSHTunnelForwarderError, tries=5000, delay=30)
def get_client_activity(session: Session) -> Sequence[Row[Any]]:
    today = datetime.today().date()
    stmt = select(Activity).filter(func.DATE(Activity.time_) == today)
    result = session.execute(stmt).fetchall()
    return result


@retry(BaseSSHTunnelForwarderError, tries=5000, delay=30)
def update_data(session: Session, table: Type[StockTable], data: list) -> dict:
    result = dict()
    data_qty = dict()
    for line in data:
        data_qty.update({line['product_code']: int(line['quantity'])})
    response = session.execute(select(table).filter(table.code.in_(data_qty.keys()))).scalars().all()
    for line in response:
        current_amount = line.quantity - data_qty[line.code]
        if current_amount == 0:
            session.execute(delete(table).where(table.code == line.code))
            session.commit()
            print(f"Удаляю проданную позицию из наличия: {line.code} {line.name}")
            if response:
                result[line.code] = 0
        else:
            session.execute(update(table).where(table.code == line.code).values(quantity=current_amount))
            session.commit()
            print(f"Меняю количество товара на сайте:\n"
                  f"{line.name}\nБыло {current_amount + data_qty[line.code]} шт. -> стало {current_amount} шт.\n")
            if response:
                result[line.code] = current_amount
    return result
