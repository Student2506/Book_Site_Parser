import json
import logging
from pathlib import Path
from shutil import move

import requests
from configargparse import ArgParser, FileType

from download_api import check_for_redirect, download_image, download_txt
from tululu_parsing_api import parse_book_page, parse_category_page

FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
logger = logging.getLogger(__name__)


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
        type=FileType('w', encoding='utf-8'),
        default='books_catalog.json',
        help='File name to use for catalog'
    )

    options = parser.parse_args()
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
                book = parse_book_page(response.text, book_id, url)
                txts = Path(options.dest_folder) / 'books'
                if not options.skip_txt:
                    if options.dest_folder:
                        download_txt(session, book, txts)
                        book['book_path'] = book['book_path'].replace(
                            options.dest_folder, ''
                        )
                    else:
                        download_txt(session, book)
                imgs = Path(options.dest_folder) / 'images'
                if not options.skip_imgs:
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
