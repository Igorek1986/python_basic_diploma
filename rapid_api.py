from typing import List, Tuple
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


def get_region_names(message: Message) -> List[Tuple[str, str, str]]:
    querystring = {"q": message.text, "locale": "ru_RU", "langid": "1033", "siteid": "300000001"}
    response = requests.request("GET", url=city_url,
                                headers=headers,
                                params=querystring,
                                timeout=10)

    data_json = json.loads(response.text)
    data = _search_city(data_json)
    return data


def _search_city(data: json) -> List[Tuple[str, str, str]]:
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


def get_hotels(region_id: str, user_input: tuple, price_min: int = 0,
               price_max: int = 0) -> List[Tuple[str, str, str, str, str, str]]:
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
    response = requests.request("POST", url=hotel_url, json=payload, headers=headers, timeout=10)

    data_json = json.loads(response.text)["data"]["propertySearch"]["properties"]
    data = _search_hotels(data_json)
    return data


def _search_hotels(data: json) -> List[Tuple[str, str, str, str, str, str]]:
    hotels_lst = []
    for elem in data[:]:
        hotel_id = elem.get('id')
        name = elem.get('name')
        amount = elem.get('price').get('lead').get('amount')
        distance = elem.get("destinationInfo").get("distanceFromDestination").get("value")
        hotel_link = f'https://www.hotels.com/h{hotel_id}.Hotel-Information'
        hotel_image_link = elem.get("propertyImage").get("image").get('url')
        _hotel = (hotel_id, name, amount, distance, hotel_link, hotel_image_link)
        hotels_lst.append(_hotel)
    return hotels_lst


def get_address_photo(hotel_id: str) -> Tuple[str, str, List[str]]:

    payload = {
        "currency": "USD",
        "eapid": 1,
        "locale": "en_US",
        "siteId": 300000001,
        "propertyId": hotel_id
    }

    response = requests.request("POST", url=photo_url, json=payload, headers=headers)
    data_json = json.loads(response.text).get('data').get('propertyInfo')
    data = _add_address_photo_hotel(data_json)

    return data


def _add_address_photo_hotel(data: json) -> Tuple[str, str, List[str]]:
    photo_lst = []
    hotel_id = data.get('summary').get('id')
    hotel_address = data.get('summary').get('location').get('address').get('addressLine')
    images_data = data.get('propertyGallery').get('images')
    for image_url in images_data:
        image = image_url.get('image').get('url')
        photo_lst.append(image)
    _hotel = (hotel_id, hotel_address, photo_lst)

    return _hotel
