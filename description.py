import time
from datetime import datetime, timezone, timedelta
import jwt
import requests
from tenacity import retry, stop_after_attempt, wait_fixed
from urllib3 import HTTPSConnectionPool

from env_config import imports, env


def create_dtube_token() -> str:
    now = datetime.now(timezone.utc)
    payload = {"service": "clientshop_connector",
               "iss": "clientshop_connector",
               "sub": f"clientshop_connector->digitaltube",
               "iat": now,
               "exp": now + timedelta(minutes=5)}

    return jwt.encode(payload, env.dtube_token, algorithm="HS256")


def get_codes_for_desc(data, category_name):
    result, category_code = list(), None
    for item in data:
        if item['name'] == category_name:
            category_code = item['code']
            break
    if not category_code:
        return result

    def find_codes(parent_code):
        for product_item in data:
            if product_item['parent'] == parent_code:
                if product_item['ispath'] is False:
                    result.append(product_item['name'])
                find_codes(product_item['code'])

    find_codes(category_code)
    return result


@retry(stop=stop_after_attempt(3), wait=wait_fixed(3))
def fetch_description_items(descriptioned: list) -> dict | None:
    try:
        token = create_dtube_token()
        headers = {"Authorization": f"Bearer {token}",
                   "Content-Type": "application/json"}

        result = requests.post(f"{env.descs_server}/get_many/",
                               timeout=15,
                               json={"items": descriptioned},
                               headers=headers)
        result.raise_for_status()
        return result.json()

    except HTTPSConnectionPool as e:
        print(e)
        raise


def addon_desc_from_dtube(firebird_data: list) -> dict:
    try:
        response = requests.get(env.descs_server, timeout=15)
        response.raise_for_status()
        time.sleep(1)
        print(f'{datetime.now().strftime("%H:%M:%S")} Сервер с описанием товаров доступен')
        descriptioned = []
        for cat in imports.description_items:
            descriptioned += get_codes_for_desc(firebird_data, cat)
        try:
            data = fetch_description_items(descriptioned)
            print(f'{datetime.now().strftime("%H:%M:%S")} Описания получены')
            difference = list(set(descriptioned) - set(data.keys()))
            if difference:
                print(f'{datetime.now().strftime("%H:%M:%S")} Описание не добавлено для', difference)
            else:
                print(f'{datetime.now().strftime("%H:%M:%S")} Все описания успешно добавлены')
            for line in firebird_data:
                if line['name'] in data.keys():
                    line['info'] = data.get(line['name'])
            return {'status': True, 'data': firebird_data}
        except requests.exceptions.RequestException as e:
            print(f'{datetime.now().strftime("%H:%M:%S")} Неудачное получение описания. Ошибка: {e}')
    except requests.exceptions.RequestException as e:
        print(f'{datetime.now().strftime("%H:%M:%S")} Сервер с описанием не отвечает. Ошибка: {e}')
    return {'status': False}
