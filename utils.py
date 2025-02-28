from contextlib import contextmanager

import requests


@contextmanager
def managed_sessions(sessions):
    local_session = sessions.local()
    ssh_session = sessions.ssh()
    try:
        yield local_session, ssh_session
    finally:
        local_session.close()
        ssh_session.close()


def notify_via_telegram(bot: str, chat: int, sale_data: list, current_qty: dict) -> bool:
    text = str()
    for sale in sale_data:
        text += (f"{'В!!!..' if sale['return_'] else 'П..'}"
                 f"{sale['product']} "
                 f"{sale['quantity']} шт "
                 f"{int(sale['sum_'])} ₽ "
                 f"{'-С-' if sale['noncash'] else ''}")
        if current_qty.get(sale['product_code']):
            text += f":{current_qty.get(sale['product_code'])}\n"
        else:
            text += '\n'
    print(text)
    url = f'https://api.telegram.org/bot{bot}/sendMessage'
    context = {'chat_id': str(chat), 'text': text}
    try:
        response = requests.post(url, data=context)
        if response.status_code == 200:
            return True
        else:
            return False
    except Exception as e:
        return False

