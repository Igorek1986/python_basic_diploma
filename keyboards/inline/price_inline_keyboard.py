from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from loader import bot
from telebot.apihelper import ApiTelegramException
from config_data import easy_travel


class KeyboardNumber:
    """Класс для создания цифровой клавиатуры"""
    def __init__(self):
        self.value = ''

    @staticmethod
    def get_number_keyboard() -> InlineKeyboardMarkup:

        keyboard = InlineKeyboardMarkup()
        keyboard.row(InlineKeyboardButton('C', callback_data='C'),
                     InlineKeyboardButton(' ', callback_data=' '),
                     InlineKeyboardButton('<=', callback_data='<='))

        keyboard.row(InlineKeyboardButton('7', callback_data='7'),
                     InlineKeyboardButton('8', callback_data='8'),
                     InlineKeyboardButton('9', callback_data='9'))

        keyboard.row(InlineKeyboardButton('4', callback_data='4'),
                     InlineKeyboardButton('5', callback_data='5'),
                     InlineKeyboardButton('6', callback_data='6'))

        keyboard.row(InlineKeyboardButton('1', callback_data='1'),
                     InlineKeyboardButton('2', callback_data='2'),
                     InlineKeyboardButton('3', callback_data='3'))

        keyboard.row(InlineKeyboardButton('.', callback_data='.'),
                     InlineKeyboardButton('0', callback_data='0'),
                     InlineKeyboardButton('✅', callback_data='OK'))

        return keyboard

    def get_value(self):
        if self.value == '':
            return '0'
        return self.value

    def get_price(self, call, min_p=easy_travel.get('min_price')) -> None:
        data = call.data

        if data == 'C':
            self.value = ''
        elif data == '<=':
            if self.value != '':
                self.value = self.value[:len(self.value) - 1]
        elif data == '.' and '.' not in self.value:
            if self.value == '':
                self.value = '0'
            self.value = self.value + data
        elif data in [str(num) for num in range(0, 10)]:
            self.value += data
        elif data == 'OK':
            bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
        if data != 'OK':
            self._send_message(call, min_p)

    def _send_message(self, call, text):

        try:
            if self.value == '':
                bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                      text=f'{text}',
                                      reply_markup=KeyboardNumber.get_number_keyboard())
            else:
                bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                      text=f'{text}{self.value}',
                                      reply_markup=KeyboardNumber.get_number_keyboard())
        except ApiTelegramException:
            pass
