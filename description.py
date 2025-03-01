from temp_fdb import fdbdata
from env_config import imports


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


def addon_desc():
    result = dict()
    for cat in imports.description_items:
        result.update(get_codes_for_desc(fdbdata, cat))
    print(result)

addon_desc()
