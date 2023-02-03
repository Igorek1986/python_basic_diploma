from telebot.types import CallbackQuery, InputMediaPhoto
from loader import bot
from states.contact_information import InfoHotel
from typing import List
from database import db
from keyboards.inline.inline_keyboard import hotel_inline, photos
from time import sleep
from datetime import datetime
from telebot.apihelper import ApiTelegramException
from config_data import easy_travel
from keyboards.reply.menu import button_menu


def get_hotel_info(call: CallbackQuery, hotel_id_lst: List[str]) -> None:
    """
    Функция получает информацией об отелях из базы данных.
    :param call: CallbackQuery
    :param hotel_id_lst: Список уникальных номеров отелей.
    """

    with bot.retrieve_data(user_id=call.from_user.id, chat_id=call.message.chat.id) as data:

        count_foto_hotels = data.get('count_foto')
        msg_id = data.get('msg_id')

        data['hotels'] = db.result_hotels(hotel_id_lst, count_foto_hotels)
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=msg_id,
                              text=f'Найдено отелей: {len(data.get("hotels"))}')
        if not len(data.get("hotels")):
            bot.delete_message(chat_id=call.message.chat.id, message_id=msg_id)
            bot.send_message(chat_id=call.from_user.id,
                             text=easy_travel.get('no_city'), reply_markup=button_menu())

    db.write_user(call)
    db.write_history(call, hotel_id_lst)
    sleep(1)
    send_info_hotel(call, back=False)


def set_num(call: CallbackQuery, back: bool, num: str) -> None:
    """

    :param call: CallbackQuery
    :param back: Булевое значение для уменьшения текущего номера отеля или фотографии.
    :param num: Если значение 'number', то устанавливается номер текущего отеля, иначе номер текущей фотографии.
    """

    with bot.retrieve_data(user_id=call.from_user.id, chat_id=call.message.chat.id) as data:

        if num == 'number':
            len_lst = len(data.get("hotels")) - 1
        else:
            len_lst = len(data.get("hotels")[data.get('number')][1]) - 1
        if data['hotels']:
            if back:
                if data[num] > 0:
                    data[num] -= 1
                else:
                    return
            else:
                if data[num] < len_lst:
                    data[num] += 1
                else:
                    return


def send_info_hotel(call: CallbackQuery, back: bool) -> None:
    """
    Функция выводит сообщение в телеграм бот с найденной информацией об отелях.
    :param call: CallbackQuery
    :param back: Булевое значение для установления номера отеля.
    """

    set_num(call, back, 'number')
    with bot.retrieve_data(user_id=call.from_user.id, chat_id=call.message.chat.id) as data:
        hotels = data.get('hotels')
        history = data.get('history')
        msg_id = data['msg_id']
        text = ''
        if history:
            command = hotels[data.get('number')][0][6]
            command_date = hotels[data.get('number')][0][7]
            count_nights = hotels[data.get('number')][0][8]
            check_in = hotels[data.get('number')][0][9]
            check_out = hotels[data.get('number')][0][10]
            text = f'Введенная команда - {command}\n' \
                   f'Дата и время ввода команды: ' \
                   f'{datetime.strptime(command_date, "%Y-%m-%d-%H.%M.%S").strftime("%d-%m-%Y %H:%M:%S")}\n'

        else:
            count_nights = data.get('count_nights')
            check_in = str(data.get('check_in'))
            check_out = str(data.get('check_out'))

    if data['hotels']:

        photo = hotels[data.get('number')][0][5]
        name_hotel = hotels[data.get('number')][0][0]
        address = hotels[data.get('number')][0][1]
        distance = hotels[data.get('number')][0][2]
        amount = hotels[data.get('number')][0][3]

        text += f'Отель: {name_hotel}\nСтоимость за ночь: {amount}\n' \
                f'Общая стоимость: {round(amount * count_nights, 2)} \n' \
                f'Адрес: {address}\nДо центра города: {distance}\nНочей: {count_nights}\n' \
                f'Заезд: {datetime.strptime(check_in, "%Y-%m-%d").strftime("%d-%m-%Y")},' \
                f' выезд: {datetime.strptime(check_out, "%Y-%m-%d").strftime("%d-%m-%Y")}'

        if data['number'] == 0 and not back:
            bot.delete_message(chat_id=call.message.chat.id, message_id=msg_id)
            bot.send_photo(chat_id=call.message.chat.id, photo=photo, caption=text,
                           reply_markup=hotel_inline(hotels, data['number']))
        else:
            media = InputMediaPhoto(media=photo, caption=text)
            bot.edit_message_media(media=media, chat_id=call.message.chat.id, message_id=call.message.message_id,
                                   reply_markup=hotel_inline(hotels, data['number']))


def send_photo_hotel(call: CallbackQuery, back_photo: bool) -> None:
    """
    Функция выводит сообщение в телеграм бот с найденными фотографиями отеля.
    :param call: CallbackQuery
    :param back_photo: Булевое значение для установления номера фотографии.
    """
    set_num(call, back_photo, 'number_photo')
    with bot.retrieve_data(user_id=call.from_user.id, chat_id=call.message.chat.id) as data:
        hotels = data.get('hotels')

    if data['hotels']:

        photo = hotels[data.get('number')][1][data.get('number_photo')]
        text = 'Фотографии отеля:'

        media = InputMediaPhoto(media=photo, caption=text)
        bot.edit_message_media(media=media, chat_id=call.message.chat.id, message_id=call.message.message_id,
                               reply_markup=photos(hotels, data.get('number_photo'), data.get('number')))


@bot.callback_query_handler(state=InfoHotel.hotel, func=lambda call: call.data == 'back' or call.data == 'next')
def hotel_view(call: CallbackQuery) -> None:
    """
    Функция показывает следующий отель или предыдущий.
    :param call: back or next
    """
    try:
        if call.data == 'next':
            send_info_hotel(call, back=False)
        elif call.data == 'back':
            send_info_hotel(call, back=True)
    except ApiTelegramException:
        pass


@bot.callback_query_handler(state=InfoHotel.hotel, func=lambda call: call.data == 'hotel')
def hotel_back(call: CallbackQuery) -> None:
    """
    Функция возвращает инлайн клавиатуру с информацией об отеле.
    Текущей фотография устанавливается на первую, что в следующем отеле смотреть фотографии с начала.
    :param call: hotel
    """
    with bot.retrieve_data(user_id=call.from_user.id, chat_id=call.message.chat.id) as data:
        data['number'] -= 1
        data['number_photo'] = 0
        data['msg_id'] = call.message.message_id
    if call.data == 'hotel':
        send_info_hotel(call, back=False)


@bot.callback_query_handler(state=InfoHotel.hotel,
                            func=lambda call: call.data == 'back_photo' or call.data == 'next_photo')
def photo_view(call: CallbackQuery) -> None:
    """
    Функция показывает следующую фотографию или предыдущую.
    :param call: back_photo or next_photo
    """
    try:
        if call.data == 'next_photo':
            send_photo_hotel(call, back_photo=False)
        elif call.data == 'back_photo':
            send_photo_hotel(call, back_photo=True)
    except ApiTelegramException:
        pass


@bot.callback_query_handler(state=InfoHotel.hotel, func=lambda call: call.data == 'photos')
def callback_photos(call: CallbackQuery):
    """
    Функция выводит инлайн клавиатуру фотографий отеля.
    :param call: photos
    """

    with bot.retrieve_data(user_id=call.from_user.id, chat_id=call.message.chat.id) as data:
        hotels = data.get('hotels')
        photo = hotels[data.get('number')][1][data.get('number_photo')]
        media = InputMediaPhoto(media=photo, caption='Фотографии отеля:')
        bot.edit_message_media(media=media, chat_id=call.from_user.id, message_id=call.message.message_id,
                               reply_markup=photos(hotels, data.get('number_photo'), data.get('number')))


@bot.callback_query_handler(state=InfoHotel.hotel, func=lambda call: call.data == 'None')
def callback_none() -> None:
    """Функция игнорирует нажатие."""
    pass


@bot.callback_query_handler(state='*', func=lambda call: call.data in ['close', 'other_city', 'menu'])
def callback_other(call: CallbackQuery):
    """
    Функция закрывает отель и удаляет сообщение или предлагает найти новый отель, выводит меню.
    :param call: close or other_city or menu
    """
    if call.data == 'close':
        bot.delete_message(chat_id=call.from_user.id, message_id=call.message.message_id)

    elif call.data == 'other_city':
        bot.set_state(user_id=call.from_user.id,
                      state=InfoHotel.city,
                      chat_id=call.message.chat.id)
        bot.delete_message(chat_id=call.from_user.id, message_id=call.message.message_id)
        bot.send_message(chat_id=call.from_user.id,
                         text=easy_travel.get('city'))

    elif call.data == 'menu':
        bot.set_state(user_id=call.from_user.id,
                      state=None,
                      chat_id=call.message.chat.id)
        bot.delete_message(chat_id=call.from_user.id, message_id=call.message.message_id)
        bot.send_message(chat_id=call.from_user.id, text='Главное меню', reply_markup=button_menu())
