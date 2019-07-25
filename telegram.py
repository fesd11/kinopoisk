''' Telegram module '''
import json
import requests

class Telegram():
    ''' Telegram class '''
    def __init__(self, key, kinopoisk):
        bot_url = f'https://api.telegram.org/bot{key}'
        req = requests.get(f'{bot_url}/getMe')
        if req.status_code == 200 and req.json()['ok'] and req.json()['result']['is_bot']:
            self.bot_url = bot_url
            self.kinopoisk = kinopoisk
        else:
            import sys
            print('Invalide key')
            sys.exit(4)

    def controler(self, method, params={}):
        req = requests.post(f'{self.bot_url}/{method}', params=params)
        if req.json()['ok'] is False:
            print(req.json())
        return req.json()

    def kinopoisk_message(self, chat_id, film):
        method = 'sendMessage'
        message = f"<b>{film['info']['name']}</b> ({film['info']['sub_name']})\n<i>{film['info']['genre']}</i>\n"
        message += f"Rating Kinopoisk: <b>{film['rating_kp']}</b>\n<a href='https://kinopoisk.ru/film/{film['id']}'>Kinopoisk</a>"
        ratings = []

        for i in range(5, 11):
            callback_data = json.dumps([int(film['id']), i, film['rate_hash']])
            ratings.append({
                'text': i,
                'callback_data': callback_data
            })
        ratings.append({
            'text': '🗑️',
            'callback_data': json.dumps({"id": film['id'], "d": True})
        })

        buttons = {}
        if 'isAvailable' in film['status']:
            buttons['inline_keyboard'] = [[{
                'text': 'Go to watch',
                'url': f'https://kinopoisk.ru/film/{film["id"]}/watch/'
            }], ratings]
        else:
            buttons['inline_keyboard'] = [
                ratings,
            ]

        params = {
            'chat_id': chat_id,
            'text': message,
            'reply_markup': json.dumps(buttons),
            'parse_mode': 'HTML'
        }
        return self.controler(method, params)

    def handle_message(self, data):
        print(data)
        if 'message' in data:
            if data['message']['text'] == 'Get a movie':
                print(data['message']['chat']['id'])
                film = self.kinopoisk.get_film()
                return self.kinopoisk_message(data['message']['chat']['id'], film)
        elif 'callback_query' in data:
            callback = data['callback_query']
            callback['data'] = json.loads(callback['data'])
            if isinstance(callback['data'], list):
                req = self.kinopoisk.set_rating_to_the_film(callback['data'][0], callback['data'][1], callback['data'][2])
            elif isinstance(callback['data'], dict):
                req = self.kinopoisk.delete_film_from_list(callback['data']['id'])

            return self.controler('answerCallbackQuery', {
                'callback_query_id': callback['id'],
                'text': "Success" if req else "Error",
                'show_alert': True
            })
