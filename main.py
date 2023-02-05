from loader import bot
import handlers
from telebot.custom_filters import StateFilter
from utils.set_bot_commands import set_default_commands
import logging


logging.basicConfig(level=logging.INFO, filename="bot_log.log",
                    format="%(asctime)s %(levelname)s %(message)s")


def main():
    bot.add_custom_filter(StateFilter(bot))
    set_default_commands(bot)
    bot.infinity_polling()


if __name__ == '__main__':
    try:
        main()
    except Exception:
        import traceback
        logging.warning(traceback.format_exc())
