from pathlib import Path
from urllib.parse import unquote, urljoin, urlsplit

from bs4 import BeautifulSoup


def parse_book_page(html_content, url):
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
        'image_filename': Path(urlsplit(full_img_url).path).name,
        'comments': [comment.text for comment in comments],
        'genres': [genre.text for genre in genres],
    }
    return book


def parse_category_page(session, cat_id, start_page, end_page):
    url = f'http://tululu.org/l{cat_id}/'
    end_page = get_last_page_value(session, url, end_page)
    pages_list = [
        f'{url}{page}/' for page in range(start_page, end_page+1)
    ]
    final_book_urls = []
    for page in pages_list:
        response = session.get(page)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'lxml')
        img_urls = soup.select('div#content div.bookimage > a')
        book_urls = [a['href'] for a in img_urls]
        book_full_urls = [
            (
                unquote(urljoin(url, book_url)),
                book_url[2:-1]
            ) for book_url in book_urls
        ]
        final_book_urls += book_full_urls

    return final_book_urls


def get_last_page_value(session, url, end_page):
    response = session.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'lxml')
    last_page = soup.select_one('div#content a.npage:last-child').text
    if end_page is None or end_page > int(last_page):
        end_page = int(last_page)
    return end_page
