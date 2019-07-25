''' Kinopoisk module '''
import random
import datetime
import requests
from bs4 import BeautifulSoup

class Kinopoisk:
    ''' Kinopoisk class '''
    def __init__(self, cookie_1, cookie_2, csrf_token):
        self.headers = {
            'Connection': 'keep-alive',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
            'X-Requested-With': 'XMLHttpRequest',
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.86 Safari/537.36',
            'Content-Type': 'application/json',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7,bg;q=0.6,la;q=0.5',
        }
        raw_cook = cookie_1
        raw_cook = raw_cook.split('; ')
        self.cookies = {i.split('=')[0]: i.split('=')[1] for i in raw_cook}

        raw_cook = cookie_2
        raw_cook = raw_cook.split('; ')
        self.cookies_for_status = {i.split('=')[0]: i.split('=')[1] for i in raw_cook}

        self.csrf_token = csrf_token

        self.film_list = None
        self.time_cache = None


    def get_film_status_online_show(self, fid):
        """ Check film status """
        headers = {
            **self.headers,
            'Host': 'ott-widget.yandex.ru',
            'Upgrade-Insecure-Requests': '1'
        }
        req = requests.get(
            f'https://ott-widget.yandex.ru/v1/ott/api/kp-film-access?kpId={fid}',
            cookies=self.cookies_for_status,
            headers=headers
        )
        try:
            req = req.json()
            return req
        except ValueError as error:
            print(error)
            return False

    def delete_film_from_list(self, fid):
        ''' Delete film from list '''
        rnd = random.randint(0, 1000000)
        req = requests.get(
            f'https://www.kinopoisk.ru/handler_mustsee_ajax.php?mode=del_film&id_film={fid}&rnd={rnd}&from_folder=3575&token={self.csrf_token}',
            headers=self.headers,
            cookies=self.cookies
        )
        if req.status_code == 200:
            self.time_cache = None
            return True
        return False

    def set_rating_to_the_film(self, fid, rating, khash):
        ''' Set gating to given film '''
        req = requests.get(
            f'https://www.kinopoisk.ru/handler_vote.php?token={self.csrf_token}&vote={rating}&id_film={fid}&c={khash}',
            headers=self.headers,
            cookies=self.cookies
        )
        if req.status_code == 200:
            self.time_cache = None
            return True
        print('Error', req.status_code)
        return False

    def get_list_of_films(self, force=False):
        ''' Get new list '''
        if self.time_cache is not None and force is False:
            now = datetime.datetime.now()
            diff = now - self.time_cache
            if diff.days < 1:
                return self.film_list

        self.film_list = []
        self.time_cache = datetime.datetime.now()
        req = requests.get(
            'https://www.kinopoisk.ru/mykp/movies/list/type/3575/sort/default/vector/desc/vt/all/perpage/200/',
            headers=self.headers,
            cookies=self.cookies
        )
        if req.status_code == 200:
            soup = BeautifulSoup(req.text, 'lxml')
            for item in soup.find_all('li', class_='item'):
                fid = item['data-id']
                info = item.find('div', class_='info')
                info_spans = info.find_all('span')
                info = {
                    'name': info.find('a', class_='name').string,
                    'sub_name': info_spans[0].string,
                    'genre': info_spans[2].string
                }

                script = item.find('script').string.split("'")
                if len(script) < 2:
                    continue
                rate_hash = script[-2]

                kp_rating = item.find('div', class_='kpRating')
                if kp_rating is not None:
                    for string in kp_rating.stripped_strings:
                        kp_rating = string
                        break

                imdb_rating = item.find('div', class_='imdb')
                if imdb_rating is not None:
                    for string in imdb_rating.stripped_strings:
                        imdb_rating = string.split()[-1]
                        break

                film = {
                    'id': fid,
                    'rating_kp': kp_rating,
                    'rating_imdb': imdb_rating,
                    'info': info,
                    'rate_hash': rate_hash
                }
                self.film_list.append(film)
            return self.film_list
        return False

    def get_film(self, rating=None):
        ''' Get random film from list '''
        film_list = self.get_list_of_films()
        if film_list is False:
            return film_list

        random_film = None
        while True:
            random_film = random.choice(self.film_list)
            if rating is not None:
                if float(random_film['rating_kp']) > rating:
                    break
                else:
                    film_list.remove(random_film)
            else:
                break

        random_film['status'] = self.get_film_status_online_show(random_film['id'])
        return random_film
