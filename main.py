import logging
from pathlib import Path
from urllib.parse import unquote, urljoin, urlsplit

import requests
from bs4 import BeautifulSoup
from configargparse import ArgParser
from pathvalidate import sanitize_filename

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
    check_for_redirect(response)
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


def parse_book_page(html_content, book_id, url):
    book = {}
    soup = BeautifulSoup(html_content, 'lxml')

    title_tag = soup.find('body').find('div', id='content').find('h1')
    book['title'] = f'{str(book_id)}. {title_tag.text.split("::")[0].rstrip()}'
    book['author'] = title_tag.find('a').text
    logger.debug(book['author'])
    raw_img_url = soup.find(
        'body'
    ).find('div', class_='bookimage').find('img')['src']
    book['full_img_url'] = unquote(urljoin(url, raw_img_url))
    logger.debug(book['full_img_url'])
    book['download_url'] = urljoin(URL_BASE, (DOWNLOAD_PART + str(book_id)))
    book['image_filename'] = Path(urlsplit(book['full_img_url']).path).name
    comments = soup.find(
        'div', id='content'
    ).find_all(
        'span', class_='black'
    )
    book['comments'] = [comment.text for comment in comments]
    logger.debug(book['comments'])
    genres = soup.find('span', class_='d_book').find_all('a')
    book['genres'] = [genre.text for genre in genres]
    logger.debug(book['genres'])
    return book


def main():
    parser = ArgParser()
    parser.add(
        '--start-id', required=True, type=int, help='Begining ID to download'
    )
    parser.add(
        '--end-id', required=True, type=int, help='Ending ID to download'
    )
    options = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG, format=FORMAT)
    with requests.Session() as session:
        for book_id in range(options.start_id, options.end_id):
            url = urljoin(URL_BASE, (DESCRIPTION_PART + str(book_id) + '/'))
            response = session.get(url, allow_redirects=True)
            response.raise_for_status()

            try:
                check_for_redirect(response)
            except requests.HTTPError:
                continue
            book = parse_book_page(response.text, book_id, url)

            try:
                logger.debug(
                    download_txt(session, book['download_url'], book['title'])
                )
            except requests.HTTPError:
                continue

            logger.debug(
                download_image(
                    session, book['full_img_url'], book['image_filename']
                )
            )
            logger.debug(f'book DICT: {book}')


if __name__ == '__main__':
    main()
