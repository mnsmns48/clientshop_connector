from dataclasses import dataclass
from environs import Env


@dataclass
class Environs:
    ssh_host: str
    ssh_port: int
    ssh_username: str
    ssh_password: str
    ssh_db_host: str
    ssh_db_port: int
    ssh_database: str
    ssh_db_username: str
    ssh_db_password: str
    fdb_dsn: str
    fdb_user: str
    fdb_password: str
    local_db_host: str
    local_db_port: int
    local_database: str
    local_db_username: str
    local_db_password: str
    tg_bot: str
    chat_id: int


def load_environs(path: str):
    env_data = Env()
    env_data.read_env()
    return Environs(
        ssh_host=env_data.str("SSH_HOST"),
        ssh_port=env_data.int("SSH_PORT"),
        ssh_username=env_data.str("SSH_USERNAME"),
        ssh_password=env_data.str("SSH_PASSWORD"),
        ssh_db_host=env_data.str("SSH_DB_HOST"),
        ssh_db_port=env_data.int("SSH_DB_PORT"),
        ssh_database=env_data.str("SSH_DATABASE"),
        ssh_db_username=env_data.str("SSH_DB_USERNAME"),
        ssh_db_password=env_data.str("SSH_DB_PASSWORD"),
        fdb_dsn=env_data.str("FDB_DSN"),
        fdb_user=env_data.str("FDB_USER"),
        fdb_password=env_data.str("FDB_PASSWORD"),
        local_db_host=env_data.str("LOCAL_DB_HOST"),
        local_db_port=env_data.int("LOCAL_DB_PORT"),
        local_database=env_data.str("LOCAL_DATABASE"),
        local_db_username=env_data.str("LOCAL_DB_USERNAME"),
        local_db_password=env_data.str("LOCAL_DB_PASSWORD"),
        tg_bot=env_data.str("TG_BOT"),
        chat_id=env_data.int("CHAT_ID"),

    )


env = load_environs('..env')
