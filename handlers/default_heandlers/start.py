from telebot.types import Message
from keyboards.reply.menu import button_menu
from loader import bot
from telebot.apihelper import ApiTelegramException


@bot.message_handler(commands=['start'])
def bot_start(message: Message):
    try:
        bot.delete_message(chat_id=message.chat.id, message_id=message.message_id-1)
    except ApiTelegramException:
        pass
    bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
    bot.send_message(chat_id=message.chat.id, text=f"Добро пожаловать в телеграм бот по поиску отелей. "
                                                   f"Подробности в справке /help, {message.from_user.full_name}!",
                     reply_markup=button_menu())

