from engine import DbSessions
from env_config import env
from firebird_func import firebird_data
from model import Base, StockTable3
from posgres_func import truncate_table


def main():
    firebird_data()
    # sessions = DbSessions(secret=env)
    # Base.metadata.create_all(sessions.local_engine)
    # Base.metadata.create_all(sessions.ssh_engine)
    # for session_factory in [sessions.local, sessions.ssh]:
    #     with session_factory() as session:
    #         truncate_table(session=session, table=StockTable3.__table__)


if __name__ == '__main__':
    main()
