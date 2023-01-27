from telebot.handler_backends import State, StatesGroup


class UserInfoState(StatesGroup):
    """Сбор информации о пользователе."""

    name = State()
    age = State()
    country = State()
    city = State()
    phone_number = State()


class InfoHotel(StatesGroup):
    """Сбор необходимой информации об отеле."""

    city = State()
    city_id = State()
    check_in = State()
    check_out = State()
    count_hotels = State()
    foto = State()
    count_foto = State()
    hotel = State()
    min_price = State()
    max_price = State()
    distance = State()
