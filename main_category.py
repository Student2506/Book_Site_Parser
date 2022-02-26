import json
import logging
from shutil import move
from pathlib import Path
from urllib.parse import unquote, urljoin

import requests
from bs4 import BeautifulSoup
from configargparse import ArgParser, FileType

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
    parser.add('--dest_folder', type=str, default='', help='Specify folder')
    parser.add(
        '--skip_imgs',
        action='store_false',
        default=True,
        help='Pass on images download'
    )
    parser.add(
        '--skip_txt',
        action='store_false',
        default=True,
        help='Pass on texts download'
    )
    parser.add(
        '--json_path',
        type=FileType('w', encoding='utf-8'),
        default='books_catalog.json',
        help='End Page'
    )

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
                txts = Path(options.dest_folder) / 'books'
                if options.skip_txt:
                    if options.dest_folder:
                        download_txt(session, book, txts)
                        book['book_path'] = book['book_path'].replace(
                            options.dest_folder, ''
                        )
                    else:
                        download_txt(session, book)
                imgs = Path(options.dest_folder) / 'images'
                if options.skip_imgs:
                    if options.dest_folder:
                        download_image(session, book, imgs)
                        book['img_src'] = book['img_src'].replace(
                            options.dest_folder, ''
                        )
                    else:
                        download_image(session, book)
                for value in (
                    'full_img_url', 'download_url', 'download_params',
                    'image_filename'
                ):
                    del book[value]
                books_json.append(book)
            except requests.HTTPError:
                continue

            logger.debug(f'book DICT: {book}')

        json.dump(books_json, options.json_path, ensure_ascii=False)
        if options.dest_folder:
            current_name = options.json_path.name
            options.json_path.close()
            new_name = Path(options.dest_folder) / current_name
            move(current_name, new_name)


if __name__ == '__main__':
    main()
