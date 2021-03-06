import json
import logging
from pathlib import Path

import requests
from configargparse import ArgParser

from download_api import check_for_redirect, download_image, download_txt
from tululu_parsing_api import parse_book_page, parse_category_page

FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
logger = logging.getLogger(__name__)


def read_arguments():
    parser = ArgParser()
    parser.add(
        '--category', required=True, type=int, help='category id to download'
    )
    parser.add('--begin_page', type=int, default=1, help='Start page')
    parser.add('--end_page', type=int, help='End Page')
    parser.add('--dest_folder', type=str, default='.', help='Specify folder')
    parser.add(
        '--skip_imgs',
        action='store_true',
        default=False,
        help='Pass on images download'
    )
    parser.add(
        '--skip_txt',
        action='store_true',
        default=False,
        help='Pass on texts download'
    )
    parser.add(
        '--json_path',
        type=str,
        default='books_catalog.json',
        help='Filename to use for catalog'
    )

    return parser.parse_args()


def main():
    logging.basicConfig(level=logging.DEBUG, format=FORMAT)
    options = read_arguments()
    with requests.Session() as session:
        books = parse_category_page(
            session, options.category, options.begin_page, options.end_page
        )
        books_json = []
        for url, book_id in books:
            try:
                response = session.get(url, allow_redirects=True)
                response.raise_for_status()
                check_for_redirect(response)
                book = parse_book_page(response.text, url)
                txts = Path(options.dest_folder) / 'books'
                if not options.skip_txt:
                    book['book_path'] = download_txt(
                        session,
                        book['title'],
                        'http://tululu.org/txt.php',
                        {'id': book_id},
                        txts
                    )
                imgs = Path(options.dest_folder) / 'images'
                if not options.skip_imgs:
                    book['img_src'] = download_image(
                        session,
                        book['full_img_url'],
                        book['image_filename'],
                        imgs
                    )
                for value in (
                    'full_img_url', 'image_filename'
                ):
                    del book[value]
                books_json.append(book)
            except requests.HTTPError:
                continue

            logger.debug(f'book DICT: {book}')

        json_filepath = Path(options.dest_folder) / options.json_path
        with open(json_filepath, 'w', encoding='utf-8') as file_handle:
            json.dump(books_json, file_handle, ensure_ascii=False)


if __name__ == '__main__':
    main()
