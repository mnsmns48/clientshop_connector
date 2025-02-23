from engine import DbSessions
from env_config import env


def main():
    sessions = DbSessions(secret=env)


if __name__ == '__main__':
    main()
