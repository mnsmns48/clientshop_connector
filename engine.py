from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


class Init_Engine:
    def __init__(self,
                 username: str,
                 password: str,
                 host: str,
                 port: str,
                 db_name: str):
        self.engine_line = f'postgresql+psycopg2://' \
                      f'{username}:{password}@{host}:{port}/{db_name}'
        self.session = sessionmaker(
            bind=create_engine(self.engine_line)
        )