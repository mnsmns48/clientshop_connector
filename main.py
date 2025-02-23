from engine import DbSessions
from env_config import env
from model import Base, StockTable3
from posgres_func import truncate_table


def main():
    sessions = DbSessions(secret=env)
    Base.metadata.create_all(sessions.local_engine)
    Base.metadata.create_all(sessions.ssh_engine)
    with sessions.local() as local_session:
        truncate_table(session=local_session, table=StockTable3.__table__)
    with sessions.ssh() as ssh_session:
        truncate_table(session=ssh_session, table=StockTable3.__table__)


if __name__ == '__main__':
    main()
