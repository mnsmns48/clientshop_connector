import sys
import traceback
from datetime import datetime

from core import refresh_table_data, ciclyc_update



def main():
    print(f'{datetime.now().strftime("%H:%M:%S")} start')
    refreshed = refresh_table_data()
    ciclyc_update(time_cycle=60, already_refreshed=refreshed['status'])


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        traceback.print_exc()
        sys.exit(1)
