import json
import time
from datetime import datetime

import requests

from env_config import imports, env


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


def addon_desc_from_dtube(firebird_data: list) -> dict:
    response = requests.get(env.descs_server, timeout=10)
    if response.status_code == 200:
        time.sleep(1)
        print(f'{datetime.now().strftime("%H:%M:%S")} Сервер с описанием товаров доступен')
        descriptioned = list()
        for cat in imports.description_items:
            descriptioned += get_codes_for_desc(firebird_data, cat)
        result = requests.post(f'{env.descs_server}/get_many/', timeout=10, json={"items": descriptioned})
        if result.status_code == 200:
            print(f'{datetime.now().strftime("%H:%M:%S")} Описания получены')
            data = json.loads(result.text)
            difference = list(set(descriptioned) - set(data.keys()))
            if difference:
                print(f'{datetime.now().strftime("%H:%M:%S")} Описание не добавлено для', difference)
            else:
                print(f'{datetime.now().strftime("%H:%M:%S")} Все описания успешно добавлены')
            for line in firebird_data:
                if line['name'] in data.keys():
                    line['info']= data.get(line['name'])
            return {'status': True, 'data': firebird_data}
        else:
            print(f'{datetime.now().strftime("%H:%M:%S")} Неудачное получение описания. Ошибка', result.status_code)
    print(f'{datetime.now().strftime("%H:%M:%S")} Error! Сервер с описанием не отвечает', response.status_code)
    return {'status': False}