Парсер книг с сайта tululu.org

Как установить
для установки скрипта нужно:
1. Опционально, сделать виртуальное окружение:
```
python -m venv env
source env/bin/activate
```
2. Установить зависмости:
```
python -m pip install -U pip
pip install -r requirements.txt
```

Аргументы

Для запуска потребуется указать ключи
```
python main.py --start_page 1 --end_page 10
```
ключи указывают диапазон с какой по какую книгу скачать

Цель проекта

Код написан в образовательных целях на онлайн-курсе для веб-разработчиков dvmn.org.