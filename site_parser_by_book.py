import logging

import requests
from configargparse import ArgParser

from download_api import check_for_redirect, download_image, download_txt
from tululu_parsing_api import parse_book_page

FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
logger = logging.getLogger(__name__)


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
