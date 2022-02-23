import logging
import random
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from pathvalidate import sanitize_filename
from urllib.parse import urljoin, urlsplit, unquote


# url = 'http://tululu.org/txt.php?id=32168'
FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
logger = logging.getLogger(__name__)

URL_BASE = 'http://tululu.org/'
DOWNLOAD_PART = 'txt.php?id='
DESCRIPTION_PART = 'b'


def download_image(session, url, filename, folder='images/'):
    response = session.get(url)
    response.raise_for_status()

    try:
        check_for_redirect(response)
    except requests.HTTPError:
        return

    Path(folder).mkdir(parents=True, exist_ok=True)
    parent = Path(folder)
    filepath = parent / sanitize_filename(filename)

    with open(filepath, 'w+b') as f:
        f.write(response.content)
    return filepath


def download_txt(session, url, filename, folder='books/'):
    """Функция для скачивания текстовых файлов.

    Args:
        url (str): Ссылка на текст, который хочется скачать.
        filename (str): Имя файла, с которым сохранять.
        folder (str): Папка, куда сохранять.

    Returns:
        str: Путь до файла, куда сохранён текст.
    """
    response = session.get(url)
    response.raise_for_status()

    try:
        check_for_redirect(response)
    except requests.HTTPError:
        return

    Path(folder).mkdir(parents=True, exist_ok=True)
    parent = Path(folder)
    filepath = parent / sanitize_filename(filename+'.txt')

    with open(filepath, 'w+b') as f:
        f.write(response.content)
    return filepath


def check_for_redirect(response):
    logger.debug(response)
    if len(response.history):
        raise requests.HTTPError()


def main():
    logging.basicConfig(level=logging.DEBUG, format=FORMAT)
    with requests.Session() as session:
        for book_id in range(1, 10):
            # book_id = random.randint(10000, 50000)
            url = urljoin(URL_BASE, (DESCRIPTION_PART + str(book_id) + '/'))
            response = session.get(url, allow_redirects=True)
            response.raise_for_status()

            try:
                check_for_redirect(response)
            except requests.HTTPError:
                continue

            soup = BeautifulSoup(response.text, 'lxml')
            title_tag = soup.find('body').find('div', id='content').find('h1')
            title = f'{str(book_id)}. {title_tag.text.split("::")[0].rstrip()}'
            author_tag = title_tag.find('a').text
            logger.debug(author_tag)
            raw_img_url = soup.find(
                'body'
            ).find('div', class_='bookimage').find('img')['src']
            full_img_url = unquote(urljoin(url, raw_img_url))
            logger.debug(full_img_url)
            download_url = urljoin(URL_BASE, (DOWNLOAD_PART + str(book_id)))
            logger.debug(download_txt(session, download_url, title))
            image_filename = Path(urlsplit(full_img_url).path).name
            logger.debug(download_image(session, full_img_url, image_filename))
            comments = soup.find(
                'div', id='content'
            ).find_all(
                'span', class_='black'
            )
            comments = [comment.text for comment in comments]
            logger.debug(comments)
            genres = soup.find('span', class_='d_book').find_all('a')
            genres = [genre.text for genre in genres]
            logger.debug(genres)


if __name__ == '__main__':
    main()
