from crud_posgres_func import with_description_products
from engine import DbSessions
from env_config import imports
from utils import managed_sessions


def get_codes_for_desc(data, category_name):
    result, category_code = dict(), None
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
                    result.update(
                        {product_item['code']: product_item['name']}
                    )
                find_codes(product_item['code'])
    find_codes(category_code)
    return result


def addon_desc_from_dtube(sessions: DbSessions, data: list):
    descriptioned = dict()
    for cat in imports.description_items:
        descriptioned.update(get_codes_for_desc(data, cat))
    with managed_sessions(sessions) as (local_session, ssh_session):
        not_desc_array = with_description_products(session=local_session, for_description=descriptioned)
    for key in not_desc_array:
        if key in descriptioned:
            del descriptioned[key]
    print(descriptioned)