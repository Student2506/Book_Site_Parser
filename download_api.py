from pathlib import Path

from pathvalidate import sanitize_filename
from requests import HTTPError


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
        raise HTTPError()
