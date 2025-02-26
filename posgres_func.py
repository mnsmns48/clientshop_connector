from datetime import datetime
from typing import Type, Any, Sequence, Literal

from retry import retry
from sqlalchemy import text, FromClause, func, select, Row, delete, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session, DeclarativeBase
from sshtunnel import BaseSSHTunnelForwarderError

from model import StockTable, Activity, Base


@retry(BaseSSHTunnelForwarderError, tries=5000, delay=30)
def truncate_table(session: Session, table: FromClause) -> None:
    stmt = f"truncate table {table}"
    session.execute(text(stmt))
    session.commit()


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
def update_data(session: Session, table: Type[StockTable], data: list) -> bool:
    temp_data = dict()
    for line in data:
        temp_data.update({line['product_code']: int(line['quantity'])})
    response = session.execute(select(table).filter(table.code.in_(temp_data.keys()))).scalars().all()
    for line in response:
        current_amount = line.quantity
        if current_amount == 0:
            session.execute(delete(table).where(table.code == line.code))
            session.commit()
            print(f"Удаляю проданную позицию из наличия: {line.code} {line.name}")
        else:
            session.execute(update(table).where(table.code == line.code).values(quantity=current_amount))
            session.commit()
            print(f"Меняю количество товара на сайте:\n"
                  f"{line.name}\nБыло {current_amount + temp_data[line.code]} шт. -> стало {current_amount} шт.\n")
