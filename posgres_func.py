from datetime import datetime
from typing import Type, Any, Sequence

from retry import retry
from sqlalchemy import text, FromClause, func, select, Row
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session
from sshtunnel import BaseSSHTunnelForwarderError

from model import StockTable, Activity


@retry(BaseSSHTunnelForwarderError, tries=5000, delay=30)
def truncate_table(session: Session, table: FromClause) -> None:
    stmt = f"truncate table {table}"
    session.execute(text(stmt))
    session.commit()


@retry(BaseSSHTunnelForwarderError, tries=5000, delay=30)
def upload_data(session: Session, table: Type[StockTable], data: list) -> bool:
    session.execute(insert(table).on_conflict_do_nothing(), data)
    session.commit()


def get_client_activity(session: Session) -> Sequence[Row[Any]]:
    today = datetime.today().date()
    stmt = select(Activity).filter(func.DATE(Activity.time_) == today)
    result = session.execute(stmt).fetchall()
    return result
