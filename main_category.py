import json
import logging
from urllib.parse import unquote, urljoin

import requests
from bs4 import BeautifulSoup
from configargparse import ArgParser

from main import check_for_redirect, download_image, download_txt   # noqa
from main import parse_book_page                                    # noqa
                                                                    # noqa
FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
logger = logging.getLogger(__name__)


def download_category(cat_id, start_page, end_page):
    url = f'http://tululu.org/l{cat_id}/'
    with requests.Session() as session:
        response = session.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'lxml')
        last_page = soup.select_one('div#content a.npage:last-child').text
        if end_page is None or end_page > int(last_page):
            end_page = int(last_page)

    pages_list = [url + str(i) + '/' for i in range(start_page, end_page+1)]
    final_book_urls = []
    with requests.Session() as session:
        for page in pages_list:
            response = session.get(page)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'lxml')
            img_urls = soup.select('div#content div.bookimage > a')
            book_urls2 = [a['href'] for a in img_urls]
            full_book_urls2 = [
                (
                    unquote(urljoin(url, book_url)),
                    book_url[2:-1]
                ) for book_url in book_urls2
            ]
            final_book_urls += full_book_urls2

    return final_book_urls


def main():
    logging.basicConfig(level=logging.DEBUG, format=FORMAT)
    parser = ArgParser()
    parser.add(
        '--category', required=True, type=int, help='category id to download'
    )
    parser.add('--begin_page', type=int, default=1, help='Start page')
    parser.add('--end_page', type=int, help='End Page')
    options = parser.parse_args()
    books = download_category(
        options.category, options.begin_page, options.end_page
    )
    books_json = []
    with requests.Session() as session:
        for url, book_id in books:
            try:
                response = session.get(url, allow_redirects=True)
                response.raise_for_status()
                check_for_redirect(response)
                book = parse_book_page(response.text, book_id, url)
                logger.debug(
                    (download_txt(session, book))
                )
                logger.debug(book['book_path'])
                logger.debug(
                    download_image(session, book)
                )
                for value in (
                    'full_img_url', 'download_url', 'download_params',
                    'image_filename'
                ):
                    del book[value]
                books_json.append(book)
            except requests.HTTPError:
                continue

            logger.debug(f'book DICT: {book}')
        with open('books_catalog.json', 'w', encoding='utf-8') as f:
            json.dump(books_json, f, ensure_ascii=False)


if __name__ == '__main__':
    main()
