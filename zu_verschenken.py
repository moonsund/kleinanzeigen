#!/usr/bin/python3

import os
import re
import time
import logging
import random
import requests
from datetime import datetime, timedelta

from bs4 import BeautifulSoup


URL = 'https://www.kleinanzeigen.de/s-zu-verschenken/friedrichshain-kreuzberg/c192l26918'
HOST = 'https://www.kleinanzeigen.de'
EXCLUSIONS = ('matratze', 'waschmaschine', 'kühlschrank', 'mattress')


class ResponseError(Exception):
    """Exception raised when response status code is not 200."""
    pass


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


def parse_response(response, timestamp):
    logging.debug('Starting parsing')
    articles = re.findall('<article(.*?)</article', response.text, re.S)
    if not articles:
        raise KeyError('No articles have been found')

    logging.debug(f'Article count: {len(articles)}')

    for article in articles:
        if 'icon icon-small icon-calendar-open' not in article or 'ref="/pro/' in article:
            continue  # Skip non-ad blocks

        soup = BeautifulSoup(article, 'html.parser')
        ad_time = soup.find('div', attrs={'class': 'aditem-main--top--right'}).text.strip()
        ad_title = soup.find('a', attrs={'class': 'ellipsis'}).text.strip()
        ad_link = soup.find('a', {'class': 'ellipsis'})['href']
        missing_info = [
            param for param in (ad_time, ad_title, ad_link) if param is None
        ]
        if missing_info:
            logging.critical(
                f'One or few ad params is missing: {missing_info}'
            )
            raise ValueError(
                f'One or few ad params is missing: {missing_info}'
            )
        else:
            logging.debug(f'Last ad: "{ad_title}", {ad_time}')
            break

    if 'Heute,' in ad_time:
        add_time = ad_time.replace('Heute,', str(datetime.today().date()))
    else:
        add_time = ad_time.replace('Gestern,', str(datetime.today().date() - timedelta(days=1)))
    add_time = datetime.strptime(add_time, "%Y-%m-%d %H:%M")
    time_delta = add_time.timestamp() - timestamp.timestamp()

    if any(word in ad_title.lower() for word in EXCLUSIONS):
        return False

    if time_delta <= 0:
        logging.info('No new ads')
        return False
    logging.info('New ad has been published')
    return add_time.strftime("%Y-%m-%d %H:%M:%S"), ad_title, ad_link


def notify(title, message, link, sound):
    """Popup notification in macOS Notification Center"""
    title = '-title {!r}'.format(title)
    message = '-message {!r}'.format(message)
    link = '-open {!r}'.format(link)
    sound = '-sound {!r}'.format(sound)
    os.system('terminal-notifier {}'.format(' '.join([message, title, link, sound])))


def main():
    logging.info('Start')
    timestamp = datetime.now()

    while True:
        try:
            response = get_response(URL)
            new_adds = parse_response(response, timestamp)
            if not new_adds:
                continue
            timestamp = datetime.now()
            add_time, add_title, add_link = new_adds
            notify(
                title=add_title,
                message=add_time,
                link=HOST+add_link,
                sound='Sonar')
            logging.info('Notification has been sent')
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
