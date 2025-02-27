import requests


def notify_via_telegram(bot: str, chat: int, sale_data: list) -> bool:
    text = str()
    for sale in sale_data:
        text += (f"{'Возврат: ' if sale['return_'] else 'Продажа: '} "
                 f"{sale['product']} "
                 f"{sale['quantity']} шт "
                 f"{int(sale['sum_'])} ₽ "
                 f"{'-С-' if sale['noncash'] else ''}\n")
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
