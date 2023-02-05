from telebot.types import ReplyKeyboardMarkup, KeyboardButton


def button_menu() -> ReplyKeyboardMarkup:
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=3, one_time_keyboard=True)
    buttons = [
        KeyboardButton('ТОП дешевых'),
        KeyboardButton('ТОП лучших'),
        KeyboardButton('ТОП дорогих'),
        KeyboardButton('История \U0001F4D7'),
        KeyboardButton('Помощь')
    ]

    return markup.add(*buttons)
