from retry import retry
from sqlalchemy import text, FromClause
from sqlalchemy.orm import Session
from sshtunnel import BaseSSHTunnelForwarderError


@retry(BaseSSHTunnelForwarderError, tries=5000, delay=30)
def truncate_table(session: Session, table: FromClause) -> None:
    stmt = f"truncate table {table}"
    session.execute(text(stmt))
    session.commit()
    print(f"{table} truncated at {session.bind.engine.url.port}")