from config_data import config
from telebot.types import Message
import requests
import json

city_url = "https://hotels4.p.rapidapi.com/locations/v3/search"
hotel_url = "https://hotels4.p.rapidapi.com/properties/v2/list"
photo_url = "https://hotels4.p.rapidapi.com/properties/v2/detail"

headers = {
    "X-RapidAPI-Key": config.RAPID_API_KEY,
    "X-RapidAPI-Host": config.RAPID_HOST,
    }


def get_json(method: str, url: str,
             querystring: dict | None = None,
             json_obj: dict | None = None) -> json:

    """
    Функция получает json объект с API.
    :param method: метод зпроса GET или POST.
    :param url: сслыка для запроса.
    :param querystring: словарь запроса.
    :param json_obj: словарь с данными для запроса.
    :return: json
    """

    while True:

        try:
            response = requests.request(method, url=url,
                                        headers=headers,
                                        params=querystring,
                                        json=json_obj,
                                        timeout=10)

            return response
        except requests.exceptions.ReadTimeout:
            pass


def get_region_names(message: Message) -> list[tuple[str, str, str]]:
    """
    Функция получает список городов.
    :param message: Сообщение пользователя.
    :return: Список кортежей состоящих из (Города, Старны и Уникального номера города).
    """
    querystring = {"q": message.text, "locale": "ru_RU", "langid": "1033", "siteid": "300000001"}
    response = get_json(method="GET", url=city_url, querystring=querystring)
    data_json = json.loads(response.text)
    data = _search_city(data_json)
    return data


def _search_city(data: json) -> list[tuple[str, str, str]]:
    """
    Вспомогательная функция для get_region_names
    :param data: JSON
    :return: Список кортежей состоящих из (Города, Старны и Уникального номера города).
    """
    elements = data.get('sr')

    city_lst = []

    for element in elements:

        city_id = element.get('gaiaId')
        if city_id:
            city_region = element.get('regionNames').get("lastSearchName")
            city_country = element.get('regionNames').get("secondaryDisplayName").split()[-1]

            _city = (city_region, city_country, city_id)
            city_lst.append(_city)

    return city_lst


def get_hotels(region_id: str, user_input: tuple, price_min: int | float = 0,
               price_max: int | float = 0) -> list[tuple[str, str, int | float, int | float, str, str]]:
    """
    Функция получает список отелей выбранного города.
    :param region_id: id выбранного города (str).
    :param user_input: Дата заезда и дата выезда (tuple(datetime, datetime)).
    :param price_min: Минимальная стоимость проживания за ночь. По умолчанию 0 (int | float).
    :param price_max: Максимальная стоимость проживания за ночь. По умолчанию 0 (int | float).
    :return: Список кортежей содержащих Id номер отеля, название отеля, стоимость проживания, дистанцию до центра,
    ссылку на отель и ссылку на фотографию.
    """
    check_in, check_out, = user_input

    payload = {
        "currency": "RUB",
        "locale": "ru_RU",
        "destination": {"regionId": region_id},
        "checkInDate": {
            "day": check_in.day,
            "month": check_in.month,
            "year": check_in.year
        },
        "checkOutDate": {
            "day": check_out.day,
            "month": check_out.month,
            "year": check_out.year
        },
        "rooms": [{
            "adults": 1,
        }
        ],
        "resultsStartingIndex": 0,
        "resultsSize": 200,
        "sort": 'PRICE_LOW_TO_HIGH',
        "filters": {
            "price": {
                "max": price_max,
                "min": price_min
            }
        }
    }

    response = get_json(method="POST", url=hotel_url, json_obj=payload)
    data_json = json.loads(response.text)["data"]["propertySearch"]["properties"]
    data = _search_hotels(data_json)
    return data


def _search_hotels(data: json) -> list[tuple[str, str, int | float, int | float, str, str]]:
    """
    Вспомогательная функция для get_hotels
    :param data: JSON
    :return: Список кортежей содержащих Id номер отеля, название отеля, стоимость проживания, дистанцию до центра,
    ссылку на отель и ссылку на фотографию.
    """
    hotels_lst = []
    for elem in data[:]:
        try:
            hotel_id = elem.get('id')
            name = elem.get('name')
            amount = elem.get('price').get('lead').get('amount')
            distance = elem.get("destinationInfo").get("distanceFromDestination").get("value")
            hotel_link = f'https://www.hotels.com/h{hotel_id}.Hotel-Information'
            hotel_image_link = elem.get("propertyImage").get("image").get('url')
            _hotel = (hotel_id, name, amount, distance, hotel_link, hotel_image_link)
            hotels_lst.append(_hotel)
        except AttributeError:
            pass
    return hotels_lst


def get_address_photo(hotel_id: str) -> tuple[str, str, list[str]]:
    """
    Функция получает адрес и фотографии отеля.
    :param hotel_id: Id отеля (str)
    :return: кортеж состоящий из Id отеля, адреса и списка фотографий.
    """

    payload = {
        "currency": "USD",
        "eapid": 1,
        "locale": "en_US",
        "siteId": 300000001,
        "propertyId": hotel_id
    }
    response = get_json(method="POST", url=photo_url, json_obj=payload)
    data_json = json.loads(response.text).get('data').get('propertyInfo')
    data = _add_address_photo_hotel(data_json)
    return data


def _add_address_photo_hotel(data: json) -> tuple[str, str, list[str]]:
    """
    Вспомогательная функция для get_address_photo.
    :param data: JSON
    :return: кортеж состоящий из Id отеля, адреса и списка фотографий.
    """
    photo_lst = []
    hotel_id = data.get('summary').get('id')
    hotel_address = data.get('summary').get('location').get('address').get('addressLine')
    images_data = data.get('propertyGallery').get('images')
    for image_url in images_data:
        image = image_url.get('image').get('url')
        photo_lst.append(image)
    _hotel = (hotel_id, hotel_address, photo_lst)

    return _hotel
