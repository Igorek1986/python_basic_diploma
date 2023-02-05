import datetime
from datetime import timedelta
from loader import bot
from states.contact_information import InfoHotel
from telebot.types import Message, CallbackQuery
from telebot.apihelper import ApiTelegramException
from rapid_api import get_region_names, get_address_photo
from keyboards.inline.inline_keyboard import city_choose, get_calendar, MyCalendar, RU_STEP, yes_no, count_object
from config_data import easy_travel
from database import db
from keyboards.inline.price_inline_keyboard import KeyboardNumber
import os
from handlers.custom_heandlers.result import get_hotel_info, send_info_hotel
from time import sleep
from collections.abc import Callable


@bot.message_handler(func=lambda message: message.text in ['ТОП дешевых', 'ТОП лучших', 'ТОП дорогих', '/lowprice',
                                                           '/highprice', '/bestdeal'])
def user_info_hotel(message: Message) -> None:

    """
    Функция запроса города. Для поиска отеля.
    :param message: команда полученная от пользователя.
    """
    if message.text in ['/lowprice', 'ТОП дешевых']:
        command = '/lowprice'
    elif message.text in ['/highprice', 'ТОП дорогих']:
        command = '/highprice'
    else:
        command = '/bestdeal'

    bot.set_state(chat_id=message.chat.id, user_id=message.from_user.id, state=InfoHotel.city)

    try:
        bot.delete_message(chat_id=message.chat.id, message_id=message.message_id-1)
    except ApiTelegramException:
        pass
    bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
    bot.send_message(chat_id=message.chat.id, text=easy_travel.get('city'))

    with bot.retrieve_data(user_id=message.from_user.id, chat_id=message.chat.id) as data:

        data['command'] = command
        data['date_command'] = datetime.datetime.today().strftime("%Y-%m-%d-%H.%M.%S")
        data['history'] = False

    if not os.path.exists('database/hotel.db'):
        db.create_table()


@bot.message_handler(func=lambda message: message.text == 'История \U0001F4D7' or message.text == '/history')
def history(message: Message) -> None:

    """
    Функция запроса истории поиска отелей пользователем.
    :param message: команда полученная от пользователя.
    """
    if message.text == 'История \U0001F4D7':
        bot.delete_message(chat_id=message.chat.id, message_id=message.message_id - 1)

    bot.set_state(chat_id=message.chat.id, user_id=message.from_user.id, state=InfoHotel.hotel)
    user_id = str(message.from_user.id)
    bot.delete_message(chat_id=message.chat.id, message_id=message.id)
    hotel_id_count_foto = db.get_history(user_id)
    if hotel_id_count_foto:
        hotels = [info_hotel for id_count_foto in hotel_id_count_foto
                  for info_hotel in db.result_hotels(id_count_foto[0], id_count_foto[1],
                                                     history_id=id_count_foto[2], history=True)]

        with bot.retrieve_data(user_id=message.from_user.id, chat_id=message.chat.id) as data:
            data["hotels"] = hotels
            data['number'] = -1
            data['number_photo'] = 0
            data['history'] = True

        answer = yes_no()
        bot.send_message(chat_id=message.chat.id,
                         text=f'История поиска отелей\nНайдено отелей: {len(data.get("hotels"))}\n'
                              f'Показать подробности об отелях?', reply_markup=answer)
    else:
        bot.send_message(chat_id=message.chat.id, text='История не найдена')


@bot.callback_query_handler(state=InfoHotel.hotel, func=lambda call: call.data == "yes")
def view_history(call: CallbackQuery) -> None:

    """
    Функция выводит последние найденные отели. Максим 10 последних.
    :param call: yes.
    """
    with bot.retrieve_data(user_id=call.from_user.id, chat_id=call.message.chat.id) as data:
        data['msg_id'] = call.message.message_id
    send_info_hotel(call, back=False)


@bot.message_handler(state=InfoHotel.city)
def clarify_city(message: Message) -> None:

    """
    Функция поиска города.
    Проверка аналогичных запросов, если такой город уже искали, будут показаны данные из локальной базы.
    Выводит список городов, для уточнения нужного города.
    :param message: Город введенный пользователем.
    """

    with bot.retrieve_data(user_id=message.from_user.id, chat_id=message.chat.id) as data:
        data['msg'] = message
        data['city'] = message.text

    try:
        bot.delete_message(chat_id=message.chat.id, message_id=data.get('msg').message_id)
    except ApiTelegramException:
        pass
    bot.edit_message_text(chat_id=message.chat.id, message_id=message.message_id-1,
                          text=easy_travel.get('performing_search'))
    sleep(1)
    need_update = db.check_update(message.text.lower())

    if need_update:
        city = get_region_names(message)
        db.write_search_city(message.text)
        db.need_update(num_bool='0', text=message.text.lower())
        city_choose(city, message)
        db.write_country(city)
        db.write_region_names(message.text.lower(), city)

    else:
        city = db.select_region(message.text.lower())
        city_choose(city, message, region_db=True)

    bot.set_state(user_id=message.from_user.id, state=InfoHotel.city_id, chat_id=message.chat.id)


@bot.callback_query_handler(state=InfoHotel.city_id, func=None)
def get_city_id(call: CallbackQuery) -> None:

    """
    Функция получения уникального ключа города или необходимость обновить список с помощью инлайн клавиатуры.
    Отправляет инлайн клавиатуру для выбора даты заезда.
    :param call: id города или update.
    """

    with bot.retrieve_data(user_id=call.from_user.id, chat_id=call.message.chat.id) as data:
        msg = data.get('msg')
        data['city_id'] = call.data

    if call.data == 'update':
        db.need_update(num_bool='1', text=msg.text.lower())
        clarify_city(msg)

    else:

        bot.set_state(user_id=call.from_user.id, state=InfoHotel.check_in, chat_id=call.message.chat.id)
        calendar, step = get_calendar(calendar_id=1,
                                      current_date=easy_travel.get('today'),
                                      min_date=easy_travel.get('today'),
                                      max_date=easy_travel.get('today') + timedelta(days=easy_travel.get('max_date')),
                                      locale='ru')
        bot.edit_message_text(chat_id=call.from_user.id,
                              message_id=call.message.message_id,
                              text=easy_travel.get('check_in'),
                              reply_markup=calendar)


@bot.callback_query_handler(func=MyCalendar.func(calendar_id=1))
def get_check_in(call: CallbackQuery) -> None:

    """
    Функция получения даты заезда. Минимальная дата ограничена текущим днем.
    После выводиться инлайн клавиатура для выбора даты выезда.
    :param call: календарь.
    """

    result, key, step = get_calendar(calendar_id=1,
                                     current_date=easy_travel.get('today'),
                                     min_date=easy_travel.get('today'),
                                     max_date=easy_travel.get('today') + timedelta(days=easy_travel.get('max_date')),
                                     locale='ru',
                                     is_process=True,
                                     callback_data=call)
    if not result and key:
        bot.edit_message_text(f'Выберите {RU_STEP[step]} заселения',
                              chat_id=call.from_user.id,
                              message_id=call.message.message_id,
                              reply_markup=key)
    elif result:

        with bot.retrieve_data(user_id=call.from_user.id, chat_id=call.message.chat.id) as data:
            data['check_in'] = result
        bot.edit_message_text(text=f"Дата заезда: {result}",
                              chat_id=call.message.chat.id,
                              message_id=call.message.message_id)

        calendar, step = get_calendar(calendar_id=2,
                                      current_date=result + timedelta(days=1),
                                      min_date=result + timedelta(days=1),
                                      max_date=result + timedelta(days=easy_travel.get('max_date')),
                                      locale='ru')
        sleep(1.5)
        bot.edit_message_text(chat_id=call.from_user.id,
                              message_id=call.message.message_id,
                              text=easy_travel.get('check_out'),
                              reply_markup=calendar)

        bot.set_state(user_id=call.from_user.id, state=InfoHotel.check_out, chat_id=call.message.chat.id)


@bot.callback_query_handler(func=MyCalendar.func(calendar_id=2))
def get_check_out(call: CallbackQuery) -> None:

    """
    Функция получения даты выезда. Минимальная дата ограничена 180 дней от текущей даты.
    Максимальную дату можно поправить в конфигурации.
    Выводится инлайн клавиатура с кол-вом отелей.
    :param call: календарь.
    """

    with bot.retrieve_data(user_id=call.from_user.id, chat_id=call.message.chat.id) as data:
        min_day = data.get('check_in') + timedelta(days=1)
        max_day = data.get('check_in') + timedelta(days=180)
    result, key, step = get_calendar(calendar_id=2,
                                     current_date=min_day,
                                     min_date=min_day,
                                     max_date=max_day,
                                     locale='ru',
                                     is_process=True,
                                     callback_data=call)
    if not result and key:
        bot.edit_message_text(text=f'Выберите {RU_STEP[step]} выезда',
                              chat_id=call.from_user.id,
                              message_id=call.message.message_id,
                              reply_markup=key)
    elif result:

        with bot.retrieve_data(user_id=call.from_user.id, chat_id=call.message.chat.id) as data:
            data['check_out'] = result
        bot.edit_message_text(text=f"Дата выезда: {result}",
                              chat_id=call.message.chat.id,
                              message_id=call.message.message_id)

        bot.set_state(user_id=call.from_user.id, state=InfoHotel.count_hotels, chat_id=call.message.chat.id)
        count = count_object()
        sleep(1.5)
        bot.edit_message_text(chat_id=call.message.chat.id,
                              message_id=call.message.message_id,
                              text=easy_travel.get('count_hotels'), reply_markup=count)


@bot.callback_query_handler(state=InfoHotel.count_hotels, func=lambda call: call)
def hotel_count(call: CallbackQuery) -> None:

    """
    Функция ловит кол-во отелей. Выводится инлайн клавиатура с запросом необходимости фотографий.
    :param call: количество отелей (int).
    """

    with bot.retrieve_data(user_id=call.from_user.id, chat_id=call.message.chat.id) as data:
        data['count_hotels'] = int(call.data)
    bot.set_state(user_id=call.from_user.id, state=InfoHotel.count_foto, chat_id=call.message.chat.id)
    answer = yes_no()
    bot.edit_message_text(chat_id=call.message.chat.id,
                          message_id=call.message.message_id,
                          text=easy_travel.get('need_photo'),
                          reply_markup=answer)


@bot.callback_query_handler(state=InfoHotel.count_foto, func=lambda call: call.data == "yes")
def foto(call: CallbackQuery) -> None:

    """
    Функция запрашивает кол-во фотографий, для этого выводится инлайн клавиатура.
    :param call: yes.
    :return:
    """

    bot.set_state(user_id=call.from_user.id, state=InfoHotel.hotel, chat_id=call.message.chat.id)
    count = count_object()
    bot.edit_message_text(chat_id=call.message.chat.id,
                          message_id=call.message.message_id,
                          text=easy_travel.get('photo'), reply_markup=count)


def check_command(func: Callable) -> Callable:

    """Функция декоратор.
    Если введена команда для поиска наиболее подходящих по цене и расположению от центра,
    то выводится инлайн клавиатура с получением минимальной стоимости.
    Иначе выполняется функция "hotel"."""

    def wrapper(call: CallbackQuery):
        func(call)

        with bot.retrieve_data(user_id=call.from_user.id, chat_id=call.message.chat.id) as data:
            command = data['command']
        if command == '/bestdeal':
            bestdeal(call=call)
        else:
            hotel(call=call)
    return wrapper


@bot.callback_query_handler(state=InfoHotel.count_foto, func=lambda call: call.data == "no")
@check_command
def photo_pass(call: CallbackQuery) -> CallbackQuery:
    """
    Функция ловит ответ "нет" из инлайн клавиатуры, присваивается 0 для кол-ва фотографий.
    :param call: no.
    """

    bot.set_state(user_id=call.from_user.id, state=InfoHotel.hotel, chat_id=call.message.chat.id)
    with bot.retrieve_data(user_id=call.from_user.id, chat_id=call.message.chat.id) as data:
        data['count_foto'] = 0
        data['msg_id'] = call.message.message_id
    return call


@bot.callback_query_handler(state=InfoHotel.hotel, func=lambda call: call)
@check_command
def count_foto(call: CallbackQuery) -> CallbackQuery:
    """
    Функция ловит ответ кол-во фотографий из инлайн клавиатуры.
    :param call: количество фотографий (int).
    """

    with bot.retrieve_data(user_id=call.from_user.id, chat_id=call.message.chat.id) as data:
        data['count_foto'] = call.data
        data['msg_id'] = call.message.message_id
    return call


def bestdeal(call: CallbackQuery) -> None:
    """
    Функция выводит инлайн клавиатуру для получения минимальной стоимости номера.
    :param call: клавиатура.
    :return:
    """

    keyboard_min_price = KeyboardNumber()
    with bot.retrieve_data(user_id=call.from_user.id, chat_id=call.message.chat.id) as data:
        data['keyboard_min_price'] = keyboard_min_price

    bot.set_state(user_id=call.from_user.id, chat_id=call.message.chat.id, state=InfoHotel.min_price)
    bot.edit_message_text(chat_id=call.from_user.id,
                          message_id=call.message.message_id,
                          text=easy_travel.get('min_price') + '0',
                          reply_markup=keyboard_min_price.get_number_keyboard())


def hotel(call: CallbackQuery) -> None:
    """
    Функция обрабатывает полученные данные от пользователя, делает запрос к базе данных.
    Если в базе данных нет адреса, то делается запрос на получение и запись адреса и фотографий.
    """

    with bot.retrieve_data(user_id=call.from_user.id, chat_id=call.message.chat.id) as data:

        command = data.get('command')
        count_hotels = data.get('count_hotels')
        data['count_nights'] = (data.get('check_out') - data.get('check_in')).days
        min_price = data.get('min_price')
        max_price = data.get('max_price')
        city_id = data.get('city_id')
        check_in = data.get('check_in')
        check_out = data.get('check_out')
        data['number'] = -1
        data['number_photo'] = 0
        msg_id = data.get('msg_id')

    bot.edit_message_text(chat_id=call.message.chat.id,
                          message_id=msg_id,
                          text=easy_travel.get('performing_search'))
    sleep(0.8)
    user_input = (check_in, check_out)
    info = (command, count_hotels, min_price, max_price, city_id)
    hotel_id_list = db.get_hotels_id(info, user_input)

    hotel_id_address_photo_lst = []
    for i_hotel_id in hotel_id_list:

        if db.get_address_hotel(i_hotel_id) == 'None':
            data = get_address_photo(i_hotel_id)
            hotel_id_address_photo_lst.append(data)
    db.write_hotels_address_photo(hotel_id_address_photo_lst)
    get_hotel_info(call, hotel_id_list)


@bot.callback_query_handler(state=InfoHotel.min_price, func=lambda call: call)
def min_price_hotel(call: CallbackQuery) -> None:
    """Функция ловит минимальную стоимость отеля. Если стоимость 0, то устанавливается значение 0.01.
    Выводит инлайн клавиатуру для получения максимальной стоимости отеля."""

    with bot.retrieve_data(user_id=call.from_user.id, chat_id=call.message.chat.id) as data:
        keyboard_min_price = data.get('keyboard_min_price')

    keyboard_min_price.get_price(call)
    keyboard_max_price = KeyboardNumber()
    if call.data == 'OK':
        min_price = float(keyboard_min_price.get_value())
        with bot.retrieve_data(user_id=call.from_user.id, chat_id=call.message.chat.id) as data:
            data['min_price'] = min_price if min_price != 0 else 0.01
            data['keyboard_max_price'] = keyboard_max_price
        bot.set_state(user_id=call.from_user.id, chat_id=call.message.chat.id, state=InfoHotel.max_price)
        bot.send_message(chat_id=call.from_user.id,
                         text=easy_travel.get('max_price') + f'{data.get("min_price")}$\n0',
                         reply_markup=keyboard_max_price.get_number_keyboard())


@bot.callback_query_handler(state=InfoHotel.max_price, func=lambda query: True)
def max_price_hotel(call: CallbackQuery) -> None:
    """Функция ловит максимальную стоимость отеля, которая больше минимальной.
    Выполняется функция "hotel"."""

    with bot.retrieve_data(user_id=call.from_user.id, chat_id=call.message.chat.id) as data:
        keyboard_max_price = data.get('keyboard_max_price')

    min_pr = data.get("min_price")
    max_pr = float(keyboard_max_price.get_value())
    keyboard_max_price.get_price(call, min_p=easy_travel.get('max_price') + f'{min_pr}$\n')

    if call.data == 'OK' and max_pr > min_pr:

        data['max_price'] = max_pr

        msg = bot.send_message(chat_id=call.from_user.id, text=f'Минимальная стоимость - {min_pr}\n'
                                                               f'Максимальная стоимость - {max_pr}')
        data['msg_id'] = msg.message_id

        sleep(0.5)
        bot.set_state(user_id=call.from_user.id, chat_id=call.message.chat.id, state=InfoHotel.hotel)
        hotel(call=call)

    elif call.data == 'OK' and max_pr <= min_pr:

        bot.send_message(chat_id=call.message.chat.id,
                         text=easy_travel.get('max_price') + f'{min_pr}$\n'
                         f'{keyboard_max_price.get_value()}',
                         reply_markup=keyboard_max_price.get_number_keyboard())
