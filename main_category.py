import json
import logging

import requests
from bs4 import BeautifulSoup
from configargparse import ArgParser
from urllib.parse import unquote, urljoin
from pathlib import PurePosixPath

from main import download_image, download_txt, check_for_redirect
from main import parse_book_page

FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
logger = logging.getLogger(__name__)


def download_category(cat_id, page_qty):
    url = f'http://tululu.org/l{cat_id}/'
    pages_list = [url + str(i) + '/' for i in range(1, page_qty+1)]
    final_book_urls = []
    with requests.Session() as session:
        for page in pages_list:
            response = session.get(page)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'lxml')
            raw_imgs = soup.find(
                'div', id='content'
            ).find_all(
                'div', class_='bookimage'
            )
            book_urls2 = [img.find('a')['href'] for img in raw_imgs]
            full_book_urls2 = [
                (
                    unquote(urljoin(url, book_url)),
                    book_url[2:]
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
    parser.add(
        '--quantity',
        required=False,
        type=int,
        default=1,
        help='Page quantity'
    )
    options = parser.parse_args()
    books = download_category(options.category, options.quantity)
    books_json = []
    with requests.Session() as session:
        for url, book_id in books:
            book_id = book_id.rstrip('/')
            try:
                response = session.get(url, allow_redirects=True)
                response.raise_for_status()
                check_for_redirect(response)
                book = parse_book_page(response.text, book_id, url)
                book['book_path'] = str(PurePosixPath(download_txt(session, book)))
                logger.debug(book['book_path'])
                logger.debug(
                    download_image(
                        session, book['full_img_url'], book['image_filename']
                    )
                )
                book['img_src'] = 'images/' + book.pop('image_filename')
                # book['image_filename'] = 'images/' + book['image_filename']
                book['title'] = book['title']
                for value in ('full_img_url', 'download_url', 'download_params'):
                    del book[value]
                books_json.append(book)
            except requests.HTTPError:
                continue

            logger.debug(f'book DICT: {book}')
        with open('books_catalog.json', 'w', encoding='utf-8') as f:
            json.dump(books_json, f, ensure_ascii=False)


if __name__ == '__main__':
    main()
