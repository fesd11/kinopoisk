''' Main app '''
import os
import sys
import json
from flask import Flask, jsonify, request
from telegram import Telegram

from kinopoisk import Kinopoisk
# TODO: past here your cookies just one string
COOKIES_1 = ''
# TODO: past here your cookies just one string (for rating)
COOKIES_2 = ''
# TODO: past here csrf token
CSRF_TOKEN = ''
kinopoisk = Kinopoisk(COOKIES_1, COOKIES_2, CSRF_TOKEN)

app = Flask(__name__)
app.config['TELEGRAM_KEY'] = os.environ.get('TELEGRAM_KEY')

if app.config['TELEGRAM_KEY'] is None:
    print('You should set your telegram api key to TELEGRAM_KEY variable')
    sys.exit(4)
else:
    telegram = Telegram(app.config['TELEGRAM_KEY'], kinopoisk)

@app.route('/')
def index():
    ''' Index page for test '''
    try:
        rating = float(request.args.get('rating'))
    except TypeError:
        rating = None

    film = kinopoisk.get_film(rating)

    return jsonify({'film': film})

@app.route(f"/{app.config['TELEGRAM_KEY']}", methods=['POST'])
def telegram_bot_handler():
    ''' Handle request '''
    if request.method == 'POST':
        data = json.loads(request.data)
        result = telegram.handle_message(data)
        return jsonify(result)
    return None

if __name__ == '__main__':
    app.run()
