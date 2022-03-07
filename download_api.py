from pathlib import Path

from pathvalidate import sanitize_filename
from requests import HTTPError


def download_image(session, full_img_url, image_filename, folder='images/'):
    url = full_img_url
    filename = image_filename
    img_src = Path(folder) / sanitize_filename(filename)
    response = session.get(url)
    response.raise_for_status()
    check_for_redirect(response)
    Path(folder).mkdir(parents=True, exist_ok=True)
    with open(str(img_src), 'w+b') as f:
        f.write(response.content)
    img_src = img_src.as_posix()
    return img_src


def download_txt(
    session, title, download_url, download_params, folder='books/'
):
    """Функция для скачивания текстовых файлов.

    Args:
        url (str): Ссылка на текст, который хочется скачать.
        filename (str): Имя файла, с которым сохранять.
        folder (str): Папка, куда сохранять.

    Returns:
        str: Путь до файла, куда сохранён текст.
    """
    response = session.get(url=download_url, params=download_params)
    response.raise_for_status()
    check_for_redirect(response)
    Path(folder).mkdir(parents=True, exist_ok=True)
    parent = Path(folder)
    filepath = parent / sanitize_filename(f'{title}.txt')
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(response.text)
    book_path = filepath.as_posix()
    return book_path


def check_for_redirect(response):
    if response.history:
        raise HTTPError()
