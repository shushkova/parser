import logging
from collections import namedtuple
import csv
import datetime
import pandas as pd
from typing import List, NamedTuple, Optional, Text

import requests
import bs4

from logger.base_class import ColoredLogger

logging.setLoggerClass(ColoredLogger)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('VinoParser')

TOTAL_PAGES = 152

WinePage = NamedTuple('WinePage', [
    ('wine_name', Text),
    ('slogan', Text),
    ('rating', int),
    ('style', Text),
    ('blend', Text),
    ('variety', Text),
    ('vintage', int),
    ('appellation', Text),
    ('abv', float),
    ('price', float),
    ('perfect_for', Text),
    ('recommendation', Text),
    ('description', Text)
])


def drop_extra(string: str) -> str:
    return string.replace('\n', '').replace('\t', '').replace('\xa0', '')


class VineParser:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.138 Safari/537.36',
            'accept-language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
        }
        self.review_page = 'https://vinepair.com/review/category/wine/?fwp_paged='
        self.number = 0
        self.pages = []

    @staticmethod
    def _json_to_wine_page(json_data):
        # type: (dict) -> Status
        return WinePage(
            wine_name=json_data['wine_name'],
            slogan=json_data['slogan'],
            rating=json_data['rating'],
            style=json_data['style'],
            blend=json_data['blend'],
            variety=json_data['variety'],
            vintage=json_data['vintage'],
            appellation=json_data['appellation'],
            abv=json_data['abv'],
            price=json_data['price'],
            perfect_for=json_data['perfect_for'],
            recommendation=json_data['recommendation'],
            description=json_data['description'][0],
        )

    def parse_wine_page(self, text: str, **kwargs):
        soup = bs4.BeautifulSoup(text, 'lxml')
        res = dict({'blend': None, 'variety': None, 'description': None, 'recommendation': None})

        res['wine_name'] = soup.select('h1')[0].get_text()
        res['slogan'] = soup.select('h1 ~ p')[0].get_text()

        table = soup.select('table')[0]
        list_items = [[drop_extra(items.text) for items in list_item.select("td")]
                      for list_item in table.select("tr")]

        for item in list_items:
            res[f'{item[0].lower()}'] = item[1]

        try:
            res['perfect_for'] = [drop_extra(i.get_text()) for i in soup.select('h2 ~ p')[0] if len(i.get_text()) > 2]
            res['recommendation'] = [drop_extra(i.get_text()) for i in soup.select('h2 ~ p')[1] if
                                     len(i.get_text()) > 2]
            res['description'] = [drop_extra(i.get_text()) for i in soup.select('h2 ~ p')[3] if len(i.get_text()) > 2]
            self.pages.append(self._json_to_wine_page(res))

        except:
            logger.error(f'FOR THIS WINE INFO WASN\'T COLLECTED {res}')

    def get_page_number(self, number: int) -> str:
        return f'{self.review_page}{number}'

    def get_new_page(self, **kwargs):
        """
        Переходим на след страницу по кнопке SEE MORE
        :return:
        """
        params = {}  # это параметры get запроса

        # ToDo test params in kwargs
        for v in kwargs.values():
            params.append(v)

        try:
            self.number += 1
            r = self.session.get(self.get_page_number(self.number), params=params)
            logger.info(r)
            return r.text
        except:
            print(self.number)
            return None

    def get_exact_page(self, url: str, **kwargs):
        """
        Берем страницу review
        :param url:
        :param kwargs:
        :return:
        """
        params = {}  # это параметры get запроса

        # ToDo test params in kwargs
        for v in kwargs.values():
            params.append(v)

        r = self.session.get(url, params=params)
        # logger.info(r)
        return r.text

    def parse_all(self):
        while self.number < TOTAL_PAGES:
            logger.info(f'Getting the page {self.review_page}{self.number} ')
            text = self.get_new_page()
            links = self.get_links_per_page(text)
            print(self.number)
            for link in links:
                logger.info(f'{link} parsing')
                page_text = self.get_exact_page(url=link)
                self.parse_wine_page(page_text)

        self.save_to_file()

    @staticmethod
    def get_links_per_page(text):
        """

        :return: list of all wine links per page
        """
        soup = bs4.BeautifulSoup(text, features='lxml')

        container = soup.select('main.main-content')
        wine_links = set([link.get('href') for link in container[0].find_all('a', href=True)])

        logger.info(f'Links to parse: {wine_links}')

        return wine_links

    def save_to_file(self):
        with open('dataset.csv', 'w') as f:
            w = csv.writer(f)
            print(self.pages)
            w.writerow(('wine_name', 'slogan', 'rating', 'style', 'blend', 'variety', 'vintage', 'appellation', 'abv',
                        'price', 'perfect_for', 'recommendation', 'description'))  # field header
            w.writerows([(data.wine_name, data.slogan, data.rating, data.style, data.blend, data.variety, data.vintage,
                          data.appellation, data.abv, data.price, data.perfect_for, data.recommendation,
                          data.description) for data in self.pages])


def main():
    p = VineParser()
    text = p.get_exact_page(url='https://vinepair.com/review/la-parde-de-haut-bailly-haut-bailly-ii/')
    # p.parse_wine_page(text)
    p.parse_all()


if __name__ == "__main__":
    main()
