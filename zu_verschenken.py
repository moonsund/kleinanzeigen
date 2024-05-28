#!/usr/bin/python3

import logging
import os
import re
import time
import random
import requests
from datetime import datetime, timedelta

from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()

URL = os.getenv('URL')
HOST = 'https://www.kleinanzeigen.de'
EXCLUSIONS = os.getenv('EXCLUSIONS').lower().split(', ')
OLD_ADS = []
AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.104 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:84.0) Gecko/20100101 Firefox/84.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.2 Safari/605.1.15',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36',
    'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:84.0) Gecko/20100101 Firefox/84.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.96 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 11_1_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.96 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64; rv:84.0) Gecko/20100101 Firefox/84.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'
    ]

PARAM_NAMES = {'URL', 'HOST'}


class Ad:
    def __init__(self, title, pub_time, link):
        self.title = title
        self.pub_time = pub_time
        self.link = HOST + link

    def __eq__(self, other):
        if isinstance(other, Ad):
            return (self.title == other.title) and (self.pub_time == other.pub_time) and (self.link == other.link)
        return False

    def __hash__(self):
        return hash((self.title, self.pub_time, self.link))


class ResponseError(Exception):
    """Exception raised when response status code is not 200."""
    pass


def check_params():
    logging.info('Parameters verification')
    missing_tokens = [
        name for name in PARAM_NAMES if globals()[name] is None
    ]
    if missing_tokens:
        logging.critical(
            f'One or few params are missing: {missing_tokens}.'
        )
        raise ValueError(
            f'One or few params are missing: {missing_tokens}.'
        )
    logging.info('Parameters have been verified')


def get_response(url):
    """Gets response from the HOST and returns data."""
    logging.info('Get response from the HOST')
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36',
        'Host': 'www.kleinanzeigen.de',
        'Accept': '*/*',
        'page': '1'
    }
    try:
        response = requests.get(url, headers=headers)
    except requests.exceptions.RequestException as error:
        raise ConnectionError(f'Connection error: {error}')
    if response.status_code != 200:
        raise ResponseError(f'Response error: {response.status_code}')
    logging.info('Response received')
    return response


def is_one_hour_old(date_str):
    date_obj = datetime.strptime(date_str, '%Y-%m-%d %H:%M')
    current_time = datetime.now()
    time_difference = current_time - date_obj
    return time_difference >= timedelta(hours=1)


def get_ads(response):
    ads = []
    logging.debug('Starting parsing')
    articles = re.findall('<article(.*?)</article', response.text, re.S)
    if not articles:
        raise KeyError('No articles have been found')

    logging.debug(f'Article count: {len(articles)}')

    for article in articles:
        if 'icon icon-small icon-calendar-open' not in article or 'ref="/pro/' in article:
            continue  # Skip non-ad blocks

        soup = BeautifulSoup(article, 'html.parser')
        ad_title = soup.find('a', attrs={'class': 'ellipsis'}).text.strip()
        ad_pub_time = soup.find('div', attrs={'class': 'aditem-main--top--right'}).text.strip()
        ad_link = soup.find('a', {'class': 'ellipsis'})['href']
        missing_values = [
            value for value in (ad_title, ad_pub_time, ad_link) if value is None
        ]
        if missing_values:
            logging.critical(
                f'One or few ad params is missing: {missing_values}'
            )
            raise ValueError(
                f'One or few ad params is missing: {missing_values}'
            )

        if any(word in ad_title.lower() for word in EXCLUSIONS):
            continue

        if 'Heute,' in ad_pub_time:
            ad_pub_time = ad_pub_time.replace('Heute,', str(datetime.today().date()))
        else:
            ad_pub_time = ad_pub_time.replace('Gestern,', str(datetime.today().date() - timedelta(days=1)))

        if is_one_hour_old(ad_pub_time):
            continue

        ads.append(Ad(title=ad_title, pub_time=ad_pub_time, link=ad_link))
    return ads


def notify(title, message, link, sound):
    """Popup notification in macOS Notification Center"""
    title = '-title {!r}'.format(title)
    message = '-message {!r}'.format(message)
    link = '-open {!r}'.format(link)
    sound = '-sound {!r}'.format(sound)
    os.system('terminal-notifier {}'.format(' '.join([title, message, link, sound])))


def main():
    check_params()
    logging.info('Start scrapping')

    while True:
        try:
            response = get_response(URL)
            ads = get_ads(response)
            if not OLD_ADS:
                OLD_ADS.extend(ads)
                logging.info('OLD_ADS updated')
                continue
            logging.debug(f'OLD_ADS: {len(OLD_ADS)}')
            logging.debug(f'ads: {len(ads)}')
            new_ads = list(set(ads).difference(set(OLD_ADS)))
            logging.debug(f'new_ads: {len(new_ads)}')
            if not new_ads:
                logging.info('No new ads')
                continue
            else:
                for new_ad in new_ads:
                    logging.debug(f'new_ad.title: {new_ad.title}')
                    logging.debug(f'new_ad.time: {new_ad.pub_time}')
                    notify(
                        title=new_ad.title,
                        message=new_ad.pub_time,
                        link=new_ad.link,
                        sound='Sonar')
                    logging.info('Notification has been sent')
                    OLD_ADS.append(new_ad)
        except Exception as error:
            logging.exception(f'{error}')
        finally:
            logging.info('Sleep mode')
            time.sleep(random.randrange(20, 40))


if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s [%(levelname)s] %(message)s',
                        level=logging.DEBUG)
    logger = logging.getLogger(__name__)

    main()
