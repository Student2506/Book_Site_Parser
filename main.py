import logging
from pathlib import Path
from urllib.parse import unquote, urljoin, urlsplit

import requests
from bs4 import BeautifulSoup
from configargparse import ArgParser
from pathvalidate import sanitize_filename

FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
logger = logging.getLogger(__name__)


def download_image(session, book, folder='images/'):
    url = book['full_img_url']
    filename = book['image_filename']
    book['img_src'] = Path(folder) / sanitize_filename(filename)
    response = session.get(url)
    response.raise_for_status()
    check_for_redirect(response)
    Path(folder).mkdir(parents=True, exist_ok=True)
    with open(str(book['img_src']), 'w+b') as f:
        f.write(response.content)
    book['img_src'] = book['img_src'].as_posix()
    return book['img_src']


def download_txt(session, book, folder='books/'):
    """Функция для скачивания текстовых файлов.

    Args:
        url (str): Ссылка на текст, который хочется скачать.
        filename (str): Имя файла, с которым сохранять.
        folder (str): Папка, куда сохранять.

    Returns:
        str: Путь до файла, куда сохранён текст.
    """
    filename = book['title']
    url = book['download_url']
    params = book['download_params']
    response = session.get(url=url, params=params)
    response.raise_for_status()
    check_for_redirect(response)
    Path(folder).mkdir(parents=True, exist_ok=True)
    parent = Path(folder)
    filepath = parent / sanitize_filename(f'{filename}.txt')
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(response.text)
    book['book_path'] = filepath.as_posix()
    return book['book_path']


def check_for_redirect(response):
    if response.history:
        raise requests.HTTPError()


def parse_book_page(html_content, book_id, url):
    soup = BeautifulSoup(html_content, 'lxml')
    title = soup.select_one('div#content > h1').text.split("::")[0].rstrip()
    author = soup.select_one('div#content > h1 > a').text
    comments = soup.select('div#content span.black')
    raw_img_url = soup.select_one('div.bookimage > a > img')['src']
    full_img_url = unquote(urljoin(url, raw_img_url))
    genres = soup.select('span.d_book a')
    book = {
        'title': title,
        'author': author,
        'full_img_url': unquote(urljoin(url, raw_img_url)),
        'download_url': 'http://tululu.org/txt.php',
        'download_params': {'id': book_id},
        'image_filename': Path(urlsplit(full_img_url).path).name,
        'comments': [comment.text for comment in comments],
        'genres': [genre.text for genre in genres],
    }
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
            try:
                url = f'http://tululu.org/b{book_id}/'
                response = session.get(url, allow_redirects=True)
                response.raise_for_status()
                check_for_redirect(response)
                book = parse_book_page(response.text, book_id, url)
                logger.debug(
                    download_txt(session, book)
                )
                logger.debug(
                    download_image(
                        session, book
                    )
                )
            except requests.HTTPError:
                continue
            logger.debug(f'book DICT: {book}')


if __name__ == '__main__':
    main()
