from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from loader import bot
from telegram_bot_calendar import DetailedTelegramCalendar
from config_data import easy_travel
from keyboards.reply.menu import button_menu


def city_choose(city_lst: list[tuple[str, str, str]], message: Message,
                region_db: bool = False) -> None:
    """
    Функция генерирует инлайн клавиатуру с найденными городами по запросу пользователя.
    :param city_lst: Список кортежей (Город, Старна и Уникального номера города)
    :param message: Message.
    :param region_db: True or False. True такой город уже искали, список город будет загружен из базы данных.
    """

    keyboard = InlineKeyboardMarkup()
    if not city_lst:
        bot.delete_message(chat_id=message.chat.id, message_id=message.message_id-1)
        bot.send_message(chat_id=message.chat.id, text=easy_travel.get('no_city'), reply_markup=button_menu())

    else:
        for elem in city_lst:
            city_name = f'{elem[0]}, {elem[1]}'
            city_id = elem[-1]
            keyboard.add(InlineKeyboardButton(text=city_name, callback_data=city_id))
        keyboard.add(InlineKeyboardButton(text='🔎Другой город', callback_data='other_city'))
        if region_db:
            keyboard.add(InlineKeyboardButton(text='Обновить локальную базу?', callback_data='update'))
            bot.edit_message_text(chat_id=message.chat.id,
                                  message_id=message.message_id-1,
                                  text='Нашли следующие регионы в локальной базе\nПредлагаю немного уточнить запрос:',
                                  reply_markup=keyboard)

        else:
            bot.edit_message_text(chat_id=message.chat.id,
                                  message_id=message.message_id-1,
                                  text='Предлагаю немного уточнить запрос:',
                                  reply_markup=keyboard)


def yes_no() -> InlineKeyboardMarkup:
    """Функция выводит инлайн клавиатуру 'да' 'нет'."""

    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton(text='Да', callback_data='yes'))
    keyboard.add(InlineKeyboardButton(text='Нет', callback_data='no'))
    return keyboard


def count_object() -> InlineKeyboardMarkup:
    """Функция выводит цифровую инлайн клавиатуру от 0 до 10."""
    keyboard = InlineKeyboardMarkup(row_width=3)
    buttons = []
    for num in range(1, 11):
        button = InlineKeyboardButton(f'{num}', callback_data=num)
        buttons.append(button)
    keyboard.add(*buttons)
    return keyboard


class MyCalendar(DetailedTelegramCalendar):
    """Класс MyCalendar. Родительский класс DetailedTelegramCalendar.
    Добавляет стрелочки и убирает пустые года, месяцы."""
    prev_button = "⬅"
    next_button = "➡"
    empty_month_button = ""
    empty_year_button = ""


RU_STEP = {'y': 'год', 'm': 'месяц', 'd': 'день'}


def get_calendar(is_process=False, callback_data=None, **kwargs):
    """
    Функция выводит инлайн календарь для выбора даты.
    """

    if is_process:
        result, key, step = MyCalendar(calendar_id=kwargs['calendar_id'],
                                       current_date=kwargs.get('current_date'),
                                       min_date=kwargs['min_date'],
                                       max_date=kwargs['max_date'],
                                       locale=kwargs['locale']).process(callback_data.data)

        return result, key, step

    else:
        calendar, step = MyCalendar(calendar_id=kwargs['calendar_id'],
                                    current_date=kwargs.get('current_date'),
                                    min_date=kwargs['min_date'],
                                    max_date=kwargs['max_date'],
                                    locale=kwargs['locale']).build()

        return calendar, step


def hotel_inline(info: list[list[tuple[str, str, float | int, float | int, str, str], list[str]]],
                 cur: int) -> InlineKeyboardMarkup:
    """
    Функция выводит инлайн клавиатура для показа найденных отелей или отелей из истории.
    :param info: Найденные отели и информация об отеле.
    :param cur: Порядковый номер отеля.
    :return: InlineKeyboardMarkup
    """

    site = info[cur][0][4]
    keyboard = InlineKeyboardMarkup(row_width=3)

    buttons = [

        InlineKeyboardButton(text='Ссылка на сайт', url=site),
        InlineKeyboardButton(text='', callback_data='None'),
        InlineKeyboardButton(text='Фото' if info[cur][-1] else '', callback_data='photos'),
        InlineKeyboardButton(text='⬅', callback_data='back'),
        InlineKeyboardButton(text=f'{cur+1}/{len(info)}', callback_data='None'),
        InlineKeyboardButton(text='➡', callback_data='next'),
        InlineKeyboardButton(text='🔎Другой город', callback_data='other_city'),
        InlineKeyboardButton(text='Главное меню', callback_data='menu'),
        InlineKeyboardButton(text='Закрыть❌', callback_data='close')

    ]

    return keyboard.add(*buttons)


def photos(info: list[list[tuple[str, str, float | int, float | int, str, str], list[str]]],
           cur: int, num_hotel: int) -> InlineKeyboardMarkup:
    """
    Функция выводит инлайн клавиатура для показа фотографий.
    :param info: Найденные отели и информация об отеле.
    :param cur: Порядковый номер фотографии.
    :param num_hotel: Порядковый номер отеля.
    :return: InlineKeyboardMarkup
    """

    keyboard = InlineKeyboardMarkup(row_width=3)
    buttons = [InlineKeyboardButton(text='', callback_data='None'),
               InlineKeyboardButton(text='Отель', callback_data='hotel'),
               InlineKeyboardButton(text='', callback_data='None'),
               InlineKeyboardButton(text='⬅', callback_data='back_photo'),
               InlineKeyboardButton(text=f'{cur + 1}/{len(info[num_hotel][1])}', callback_data='None'),
               InlineKeyboardButton(text='➡', callback_data='next_photo')]

    return keyboard.add(*buttons)
