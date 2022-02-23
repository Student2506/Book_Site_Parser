import random
from pathlib import Path

import requests

# url = 'http://tululu.org/txt.php?id=32168'

url = 'http://tululu.org/txt.php?id='

Path('books').mkdir(exist_ok=True)

parent = Path('books')

for _ in range(10):
    book_id = random.randint(10000, 50000)
    response = requests.get(url + str(book_id))
    response.raise_for_status()

    filename = parent / f'{str(book_id)}.txt'
    with open(filename, 'w+b') as f:
        f.write(response.content)
