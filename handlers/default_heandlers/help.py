from telebot.types import Message
from telebot.apihelper import ApiTelegramException
from config_data.config import DEFAULT_COMMANDS
from loader import bot


@bot.message_handler(func=lambda message: message.text in ['/help', 'Помощь'])
def bot_help(message: Message):
    try:
        bot.delete_message(chat_id=message.chat.id, message_id=message.message_id-1)
    except ApiTelegramException:
        pass
    bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
    text = [f'/{command} - {desk}' for command, desk in DEFAULT_COMMANDS]
    bot.send_message(chat_id=message.chat.id, text='\n'.join(text))
