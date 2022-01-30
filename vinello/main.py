import logging
from collections import namedtuple
import csv
import datetime
import pandas as pd
from typing import List, NamedTuple, Optional, Text

import requests
import bs4

from logger.base_class import ColoredLogger

from page_structure import VinelloPage

logging.setLoggerClass(ColoredLogger)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('VinelloParser')

TOTAL_PAGES = 643


fields = ('wine_name', 'description', 'verification', 'type', 'country', 'region', 'acidity', 'sugar',
                        'sweetness', 'sub_region', 'perfect_for', 'ageing', 'vintage', 'soil', 'aromas', 'texture',
                        'food_pairing', 'alcohol', 'allergens', 'colour', 'variety', 'harvest', 'maturation_duration',
                        'style')
fields_to_parse = ('wine_name', 'description', 'verification', 'type of wine', 'country', 'region',
                        'wine acidity in g/l', 'residual sugar in g/l',
                        'sweetness', 'sub region', 'occasion & theme', 'ageing in', 'vintage', 'soil',
                        'aromas & palate notes', 'mouthfeel/ texture',
                        'food pairing', 'alcohol % abv', 'allergens & misc. ingredients',
                        'wine colour', 'grape variety', 'harvest', 'duration of maturation (in months)',
                        'style')

def drop_extra(string: str) -> str:
    return string.replace('\n', '').replace('\t', '').replace('\xa0', '').replace(':', '').strip(' ')


class VinelloParser:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.138 Safari/537.36',
            'accept-language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
        }
        self.review_page = 'https://www.vinello.eu/wine?p=2&o='
        self.number = 0
        self.pages = []

    @staticmethod
    def _json_to_wine_page(json_data):
        # type: (dict) -> Status
        return VinelloPage(
            wine_name=json_data['wine_name'],
            description=json_data['description'],
            verification=json_data['verification'],
            type=json_data['type of wine'],
            country=json_data['country'],
            region=json_data['region'],
            acidity=json_data['wine acidity in g/l'],
            sugar=json_data['residual sugar in g/l'],
            perfect_for=json_data['occasion & theme'],
            sweetness=json_data['sweetness'],
            sub_region=json_data['sub region'],
            ageing=json_data['ageing in'],
            vintage=json_data['vintage'],
            soil=json_data['soil'],
            aromas=json_data['aromas & palate notes'],
            texture=json_data['mouthfeel/ texture'],
            food_pairing=json_data['food pairing'],
            alcohol=json_data['alcohol % abv'],
            allergens=json_data['allergens & misc. ingredients'],
            colour=json_data['wine colour'],
            variety=json_data['grape variety'],
            harvest=json_data['harvest'],
            maturation_duration=json_data['duration of maturation (in months)'],
            style=json_data['style'],
        )

    def parse_wine_page(self, text: str, **kwargs):
        soup = bs4.BeautifulSoup(text, 'lxml')
        # res = dict({'description': None, 'verification': None})
        res = {}
        for filed in fields_to_parse:
            res[filed] = None

        res['wine_name'] = soup.select('h1')[0].get_text()

        table = soup.select('table')[0]
        list_items = [[drop_extra(items.text) for items in list_item.select("td")]
                      for list_item in table.select("tr")]

        for item in list_items:
            res[f'{item[0].lower()}'] = item[1]

        try:
            # print(' '.join([part.get_text() for part in soup.select('h2 ~ p')[:-1]]))
            res['description'] = drop_extra(soup.find_all("div", {"class": "product--description"})[0].get_text())
            res['verification'] = ' '.join([part.get_text() for part in soup.select('h2 ~ p')[:-1]])
            # print(res['verification'])
            self.pages.append(self._json_to_wine_page(res))
        except:
            logger.error(f'FOR THIS WINE INFO WASN\'T COLLECTED {res}')

    def get_page_number(self, number: int) -> str:
        return f'{self.review_page}{number}&n=16'

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

        # container = soup.find_all('a', href=True)
        containers = soup.find_all("div", {"class": "product--info"})
        # print(soup.find_all('a', class_='product--info'))
        wine_links = []
        for container in containers:
            wine_links.append([link.get('href') for link in container.find_all('a', href=True)][0])
        # print(set([link.get('href') for link in container[0].find_all('a', href=True)]))

        logger.info(f'Links to parse: {wine_links}')

        return wine_links

    def save_to_file(self):
        with open('dataset.csv', 'w') as f:
            w = csv.writer(f)
            # print(self.pages)
            w.writerow(fields)  # field header
            to_save = [[getattr(data, attr_name) for attr_name in fields] for data in self.pages]
            print(to_save)
            w.writerows(to_save)


def main():
    p = VinelloParser()
    # text = p.get_exact_page(url='https://www.vinello.eu/steinraffler-lagrein-j-hofstaetter')
    p.parse_all()
    # p.parse_wine_page(text)


if __name__ == "__main__":
    main()
