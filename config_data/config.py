import os
from dotenv import load_dotenv, find_dotenv
from datetime import date

if not find_dotenv():
    exit('Переменные окружения не загружены т.к отсутствует файл .env')
else:
    load_dotenv()

TOKEN = os.getenv('TOKEN')
RAPID_API_KEY = os.getenv('RAPID_API_KEY')
RAPID_HOST = os.getenv('RAPID_HOST')
DEFAULT_COMMANDS = (
    ('start', "Запустить бота"),
    ('help', "Вывести справку"),
    ('lowprice', 'Вывод самых дешёвых отелей в городе (ТОП дешевых)'),
    ('highprice', 'Вывод самых дорогих отелей в городе (ТОП дорогих)'),
    ('bestdeal', 'Вывод отелей, наиболее подходящих по цене и расположению от центра (ТОП лучших)'),
    ('history', 'Вывод истории поиска отелей'),
)


easy_travel = {
    'city': 'Какой город Вас интересует?',
    'city_id': 'Предлагаю немного уточнить запрос',
    'check_in': 'Выберите год заселения',
    'check_out': 'Выберите год выезда',
    'count_hotels': 'Сколько объектов смотрим?',
    'photo': 'Выберите кол-во фотографий?',
    'min_price': 'Минимальная стоимость 0$\nВведите стоимость:\n',
    'max_price': f'Введите максимальную цену\nцена должна быть больше\n',
    'need_photo': 'Фотографии нужны?',
    'today': date.today(),
    'max_date': 180,
    'performing_search': 'Выполняю поиск.....',
    'no_city': 'Попробуйте другой город или увеличьте разницу между минимальной ценой и максимальной ценой'

}
