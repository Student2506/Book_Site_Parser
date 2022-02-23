import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlsplit, unquote
from pathlib import Path

url = 'http://tululu.org/b9/'

response = requests.get(url)
response.raise_for_status()

soup = BeautifulSoup(response.text, 'lxml')
genres = soup.find('span', class_='d_book').find_all('a')
genres = [genre.text for genre in genres]
print(genres)
# texts = soup.find('div', id='content').find_all('span', class_='black')
# for text in texts:
#     print(text.text)
# title_tag = soup.find('main').find('header').find('h1')
# title_text = title_tag.text
# print(title_text)
# print(soup.find('img', class_='attachment-post-image')['src'])
# p_elems = soup.find('div', class_='entry-content').find_all(['p', 'h3'])
# for elem in p_elems:
# #     print(elem.text)
# raw_img_url = soup.find('body').find('div', class_='bookimage').find('img')['src']
# full_img_url = unquote(urljoin(url, raw_img_url))
# path = Path(urlsplit(full_img_url).path)
# print(path.name)
