import requests
import time
import threading
from datetime import datetime
import json

BOT_TOKEN = '8740804498:AAH7KBEAhdv1VAZZwGagd1Y9HyC4cWbVboc'
USERS_FILE = 'users.json'

USERS = set()
LAST_UPDATE = 0

def load_users():
    global USERS
    try:
        with open(USERS_FILE, 'r') as f:
            USERS = set(json.load(f))
    except:
        USERS = {608423521}
    print(f'👥 Подписчиков: {len(USERS)}')

def save_users():
    with open(USERS_FILE, 'w') as f:
        json.dump(list(USERS), f)

def fmt(v):
    return f'{float(v):.2f}' if v and str(v).replace('.','').replace('-','').isdigit() else '—'

def get_ticker_data(secid, is_index=False):
    if is_index:
        url = f'https://iss.moex.com/iss/engines/stock/markets/index/boards/SNDX/securities/{secid}.json?iss.meta=off'
    else:
        url = f'https://iss.moex.com/iss/engines/stock/markets/shares/boards/TQBR/securities/{secid}.json?iss.meta=off'
    
    try:
        resp = requests.get(url, timeout=10).json()
        data = resp['marketdata']['data'][0]
        columns = resp['marketdata']['columns']
        
        prev_idx = columns.index('PREVPRICE') if 'PREVPRICE' in columns else 2
        open_idx = columns.index('OPEN') if 'OPEN' in columns else 3
        close_idx = columns.index('CLOSE') if 'CLOSE' in columns else 4
        pct_idx = columns.index('WAPTOPREVWAPRICEPRCNT') if 'WAPTOPREVWAPRICEPRCNT' in columns else 9
        low_idx = columns.index('LOW') if 'LOW' in columns else 5
        high_idx = columns.index('HIGH') if 'HIGH' in columns else 6
        
        return (data[prev_idx], data[open_idx], data[close_idx], data[pct_idx], data[low_idx], data[high_idx])
    except:
        return None, None, None, None, None, None

def register_user(chat_id):
    if chat_id not in USERS:
        USERS.add(chat_id)
        save_users()
        print(f'✅ Новый: {chat_id}')

def send_to_all(message):
    sent = 0
    for chat_id in list(USERS):
        try:
            requests.post(f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage',
                         data={'chat_id': chat_id, 'text': message}, timeout=10).raise_for_status()
            sent += 1
        except:
            USERS.discard(chat_id)
    save_users()
    print(f'📤 Отправлено {sent}/{len(USERS)}')

def check_updates():
    global LAST_UPDATE
    while True:
        try:
            url = f'https://api.telegram.org/bot{BOT_TOKEN}/getUpdates?offset={LAST_UPDATE}'
            resp = requests.get(url, timeout=10).json()
            for update in resp.get('result', []):
                register_user(update['message']['chat']['id'])
                LAST_UPDATE = update['update_id'] + 1
        except:
            pass
        time.sleep(60)  # Реже

def hourly_report():
    print('🔄 НАЧИНАЮ ОТЧЁТ...')
    time_now = datetime.now().strftime('%H:%M')
    
    imoex = get_ticker_data('IMOEX', True)
    sber = get_ticker_data('SBER')
    lkoh = get_ticker_data('LKOH')
    gmkn = get_ticker_data('GMKN')
    
    print(f'✅ Данные получены IMOEX: {fmt(imoex[2])}')
    
    message = f'''🕐 {time_now}

📊 IMOEX
Вчера: {fmt(imoex[0])}
Сегодня: {fmt(imoex[1])} → {fmt(imoex[2])}
📈 {fmt(imoex[3])}%
📏 Low: {fmt(imoex[4])} High: {fmt(imoex[5])}

📊 SBER
Вчера: {fmt(sber[0])}
Сегодня: {fmt(sber[1])} → {fmt(sber[2])}
📈 {fmt(sber[3])}%
📏 Low: {fmt(sber[4])} High: {fmt(sber[5])}

📊 LKOH
Вчера: {fmt(lkoh[0])}
Сегодня: {fmt(lkoh[1])} → {fmt(lkoh[2])}
📈 {fmt(lkoh[3])}%
📏 Low: {fmt(lkoh[4])} High: {fmt(lkoh[5])}

📊 GMKN
Вчера: {fmt(gmkn[0])}
Сегодня: {fmt(gmkn[1])} → {fmt(gmkn[2])}
📈 {fmt(gmkn[3])}%
📏 Low: {fmt(gmkn[4])} High: {fmt(gmkn[5])}'''

    print('📤 ОТПРАВЛЯЮ...')
    send_to_all(message)
    print('✅ ОТЧЁТ ГОТОВ!')

if __name__ == '__main__':
    load_users()
    print('🚀 МОНИТОРИНГ ЗАПУЩЕН')
    
    # Авторегистрация в фоне
    threading.Thread(target=check_updates, daemon=True).start()
    
    # ПЕРВЫЙ ОТЧЁТ СРАЗУ!
    hourly_report()
    
    # Дальше каждый час
    while True:
        print('💤 Сплю 1 час...')
        time.sleep(3600)
        hourly_report()
