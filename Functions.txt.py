import csv
import requests
import json
from config import *
from telebot import TeleBot
from telebot import types
from datetime import datetime

bot = TeleBot(token=token)
date_time = datetime.now().strftime("%m/%d/%Y, %H:%M:%S")

def serrch_query(query):
    '''
    :param query: город
    :return: долгото широта города или None если город не найден
    '''
    url = "https://hotels-com-provider.p.rapidapi.com/v1/destinations/search"
    querystring = {"query": query, "currency": "USD", "locale": "en_US"}
    headers = {
        "X-RapidAPI-Host": "hotels-com-provider.p.rapidapi.com",
        "X-RapidAPI-Key": "30c78cf861msh204dfe2d76a262fp1fa6eajsncabbe1fb2378"
    }
    try:
        response = requests.request("GET", url, headers=headers, params=querystring).json()
        serch = response["suggestions"][0]["entities"][0]
        latitude = serch["latitude"]
        longitude = serch["longitude"]
        return [latitude, longitude]
    except Exception:
        return None


def serach_hotel(latitude, longitude, hotel_count, photo_count, checkin_date, checkout_date,
                 sort_order=None, min =None, max = None, centr_hotel = None):
    '''

    :param latitude: долгата города
    :param longitude: штрота города
    :param hotel_count: колисество отелей
    :param photo_count: количесмтво фото
    :param checkin_date: дата вход в отел
    :param checkout_date: дата выход из отеля
    :param sort_order: сортировка отелей PRICE_HIGHEST_FIRS - самые дорагие отели
                                          PRICE - дешовые отели
                                          DISTANCE_FROM_LANDMARK - отели максимално ближу к центру


    :param min: минималная ценя отеля
    :param max: максималня цена отеля
    :param centr_hotel: пойск отеля по указанному дистанции
    :return: генератор
            No find
            список отелей с фото
            список отелей ьез фото
            картеж (No find distance by hotel, все доступные дистанции)
    '''
    url = "https://hotels-com-provider.p.rapidapi.com/v1/hotels/nearby"
    querystring = {"latitude": str(latitude), "currency": "USD", "longitude": str(longitude),
                   "checkout_date": checkout_date,
                   "sort_order": sort_order, "checkin_date": checkin_date,
                   "adults_number": "2", "locale": "en_US"
                   }
    if min and max:
        querystring = querystring | {"price_min": min, "price_max": max}
    headers = {
        "X-RapidAPI-Host": "hotels-com-provider.p.rapidapi.com",
        "X-RapidAPI-Key": "30c78cf861msh204dfe2d76a262fp1fa6eajsncabbe1fb2378"
    }
    try:
        response = requests.request("GET", url, headers=headers, params=querystring).json()
        with open("поиск_отелей.json", "w", encoding="utf-8") as file:
            json.dump(response, file, indent=4)
        response = response["searchResults"]["results"]
    except Exception:
        response = None
    if response and len(response) > 0:
        '''если отели не найдени возврашаем NO find'''
        if centr_hotel:
            '''если ползватель указал дистанция для пойска пробуем найти отели'''
            distance_hotel = []
            distance = []
            for i_distance in response:
                miles = float(i_distance["landmarks"][0]["distance"].split()[0])
                distance.append(str(miles))
                if miles in [centr_hotel - 0.1, centr_hotel, centr_hotel + 0.1]:
                    distance_hotel.append(i_distance)
            if len(distance_hotel) > 0:
                response = distance_hotel
            else:
                '''если по указаному дистанцикй отелей не найдены возвращаем кортеж с уведамлением и 
                сдоступнымы ростаяниями'''
                yield "No find distance by hotel", distance
        count = hotel_count if hotel_count < len(response) else len(response)
        history_values["name"] = []
        for i in range(count):
            '''id отеля'''
            id = response[i]["id"]
            try:
                '''название и адрес отеля'''
                n_a = f"{response[i]['name']}\nАдрес- {response[i]['address']['streetAddress']}"
            except Exception:
                n_a = "-"
            '''словарь для истории , добавлаем имена отелей'''
            history_values["name"].append(response[i]['name'])
            '''стоймость за ночь'''
            current = f"стоймость за начь - {response[i]['ratePlan']['price']['current']}"
            url = f"https://hu.hotels.com/ho{id}/?q-check-in=f{checkin_date}&q-check-out={checkout_date}"
            try:
                '''обшая стоймсть'''
                total_current = f"обшая сиоймость - {response[i]['ratePlan']['price']['fullyBundledPricePerStay'].split()[1]}"
            except Exception:
                total_current = "-"
            if photo_count:
                '''вызваесм функцию get_photo для получения фото'''
                result_photo = get_photo(id=id, count=photo_count)
                if len(result_photo) > 0:
                    '''если функция вернула сылки фото , дабавлаем их в список 
                    элементы
                    0- список с 1 фото и url
                    1-данные отеля'''
                    result = [[result_photo[0], url], f"{n_a}\n{current}\n{total_current}"]
                    if photo_count > 1:
                        photo_count = len(result_photo) if photo_count > len(result_photo) else photo_count
                        '''добавлаем в спсиок другие фото с индексом 3'''
                        result.append([result_photo[i] for i in range(1, photo_count)])
                else:
                    '''если фото не найденно возврашаем даннные от отеля и url'''
                    result = [["No foto"], f"{n_a}\n{current}\n{total_current}",
                              url]
            else:
                '''если поиск без фото'''
                result = [f"{n_a}\n{current}\n{total_current}",
                            url]
            yield result
    else:
        yield "No find"


def get_photo(id, count):
    '''
    :param id: ид города
    :param count: количество фото
    :return:
    '''
    url = "https://hotels-com-provider.p.rapidapi.com/v1/hotels/photos"
    querystring = {"hotel_id": str(id)}
    headers = {
        "X-RapidAPI-Host": "hotels-com-provider.p.rapidapi.com",
        "X-RapidAPI-Key": "30c78cf861msh204dfe2d76a262fp1fa6eajsncabbe1fb2378"
    }

    response = requests.request("GET", url, headers=headers, params=querystring).json()
    photo = []
    try:
        for img_link in range(count if count < len(response) else len(response)):
            photo.append(response[img_link]["mainUrl"])
    except Exception:
        pass

    return photo


def query(message):
    if len(tasks) > 0:
        tasks.clear()
    if message.text.isalpha() and len(message.text) >= 2:
        _task = serrch_query(message.text)
        if _task is None:
            msg = bot.send_message(message.chat.id, "город не найден\nвведите ешо раз")
            bot.register_next_step_handler(msg, query)
        else:
            tasks["latitude"] = _task[0]
            tasks["longitude"] = _task[1]
            if order == [1]:
                tasks["sort_order"] = "PRICE"
                history_values["каманда"] = "/lowprice"
                msg = bot.send_message(message.chat.id, "введите количество  отелей")
                bot.register_next_step_handler(msg, hotel_count)
            elif order == [2]:
                tasks["sort_order"] = "PRICE_HIGHEST_FIRST"
                history_values["каманда"] = "/highprice"
                msg = bot.send_message(message.chat.id, "введите количество  отелей")
                bot.register_next_step_handler(msg, hotel_count)
            elif order == [3]:
                tasks["sort_order"] = "DISTANCE_FROM_LANDMARK"
                history_values["каманда"] = "/besdeal"
                msg = bot.send_message(message.chat.id, "введите диапазон цен для пойска\n"
                                                     "10-1000000")
                bot.register_next_step_handler(msg, price)
    else:
        msg = bot.send_message(message.chat.id, "неправили ввод\nвведите город ешо раз")
        bot.register_next_step_handler(msg, query)


def price(message):
    try:
        msg = message.text.split("-")
        if len(msg) == 2 and int(msg[0]) >= 10 and int(msg[0]) <= 1000000 and int(msg[1]) >= int(msg[0]) and int(msg[1]) <= 1000000:
            tasks["min"] = int(msg[0])
            tasks["max"] = int(msg[1])
            markup = types.InlineKeyboardMarkup()
            button_1 = types.InlineKeyboardButton(text="ввести диапазон для пойска", callback_data="4")
            button_2 = types.InlineKeyboardButton(text="максимално близко к центру", callback_data="5")
            markup.add(button_1, button_2)
            msg = bot.send_message(message.chat.id, "выбкрите тип пойска", reply_markup=markup)
        else:
            msg = bot.send_message(message.chat.id, "введите диапазон цен для пойска\n"
                                                         "10-1000000")
            bot.register_next_step_handler(msg, price)
    except Exception:
        bot.send_message(message.chat.id, "eeror")
        msg = bot.send_message(message.chat.id, "неправилный формат ввода")
        bot.register_next_step_handler(msg, price)



def func_order(x):
    '''
    :param x: номер команды
    :return: None
    '''
    if x == 1:
        order[0] = 1
    elif x == 2:
        order[0] = 2
    elif x == 3:
        order[0] = 3


def centre(message):
    try:
        msg = float(message.text)
        tasks["centr_hotel"] = msg
        msg = bot.send_message(message.chat.id, "введите количество  отелей")
        bot.register_next_step_handler(msg, hotel_count)
    except Exception:
        msg = bot.send_message(message.chat.id, "неправилный формат ввода")
        bot.register_next_step_handler(msg, centre)


def hotel_count(message):
    if message.text.isdigit() and int(message.text) > 0:
        tasks["hotel_count"] = int(message.text)
        markup = types.InlineKeyboardMarkup()
        item_yes = types.InlineKeyboardButton(text="да", callback_data="1")
        items_no = types.InlineKeyboardButton(text="нет", callback_data="2")
        markup.add(item_yes, items_no)
        msg = bot.send_message(message.chat.id, "фотаграфия от отеля?", reply_markup=markup)
    else:
        msg = bot.send_message(message.chat.id, "неправилный ввод\nколичество должен быть положителным числом")
        bot.register_next_step_handler(msg, hotel_count)



def hotel_link(url):
    hotel_link = types.InlineKeyboardMarkup()
    text = types.InlineKeyboardButton(text="---->", url=url)
    hotel_link.add(text)
    return hotel_link


@bot.callback_query_handler(func = lambda call: True)
def keybord(call):
    """

    :param call: оббект клавятуры
    :return: data
    """
    distance_list = None
    if call.data:
        if call.data == "1":
            bot.delete_message(call.message.chat.id, call.message.message_id)
            msg = bot.send_message(call.message.chat.id, "ведите количество фото")
            bot.register_next_step_handler(msg, photo_count)
        elif call.data == "2":
            bot.delete_message(call.message.chat.id, call.message.message_id)
            msg = bot.send_message(call.message.chat.id, "введите дату входа и выхода пример\n"
                                                    "(год)xxxx-(месяц)xx-(день)xx (пробел) xxxx-xx-xx")
            bot.register_next_step_handler(msg, data)
        elif call.data == "3":
            bot.delete_message(call.message.chat.id, call.message.message_id)
            response = serach_hotel(*[tasks.get(args) for args in arguments_sample])
            for result in response:
                if result == "No find":
                    bot.send_message(call.message.chat.id, "по указаннами данами нет отелей")
                    break
                elif isinstance(result, tuple):
                    distance_list = result[1]
                    with open("distance.txt", "w") as file:
                        file.write(str(distance_list))
                    markup = types.InlineKeyboardMarkup()
                    button1 = types.InlineKeyboardButton(text="ввести дистанцию", callback_data="6")
                    button2 = types.InlineKeyboardButton(text="найти другой отель", callback_data="7")
                    markup.add(button1, button2)
                    msg = bot.send_message(call.message.chat.id, f"{result[0]}\nвыберите команду", reply_markup=markup)
                    break
                elif isinstance(result, list):
                    if isinstance(result[0], list):
                        if result[0][0] == "No foto":
                            result.pop(0)
                            _hotel_link = hotel_link(result[1])
                            bot.send_message(call.message.chat.id, result[0], reply_markup=_hotel_link)
                        else:
                            _hotel_link = hotel_link(url=result[0][1])
                            bot.send_photo(call.message.chat.id, photo=result[0][0], caption=result[1], reply_markup=_hotel_link)
                            if len(result) > 2:
                                for photo in result[2]:
                                    bot.send_photo(call.message.chat.id, photo=photo)
                    else:
                        for result in response:
                            _hotel_link = hotel_link(result[1])
                            bot.send_message(call.message.chat.id, result[0], reply_markup=_hotel_link)

            with open("history.csv", "a", encoding="cp1251") as file:
                writer = csv.writer(file)
                komands, name = [value for value in history_values.values()]
                writer.writerow((
                    komands,
                    date_time,
                    " | ".join(name)
                ))

        elif call.data == "4":
            bot.delete_message(call.message.chat.id, call.message.message_id)
            msg = bot.send_message(call.message.chat.id, "введите диапазон ростаяние\nпример 2.8")
            bot.register_next_step_handler(msg, centre)
        elif call.data == "5":
            bot.delete_message(call.message.chat.id, call.message.message_id)
            msg = bot.send_message(call.message.chat.id, "введите количество  отелей")
            bot.register_next_step_handler(msg, hotel_count)
        elif call.data == "6":
            bot.delete_message(call.message.chat.id, call.message.message_id)
            with open("distance.txt", "r") as file:
                src = file.read()
            msg = bot.send_message(call.message.chat.id, f"Дступные ростяния для поиска\n{src}")
            bot.register_next_step_handler(msg, distance)
        elif call.data == "7":
            bot.delete_message(call.message.chat.id, call.message.message_id)
            msg = bot.send_message(call.message.chat.id, "введите город")
            bot.register_next_step_handler(msg, query)



def distance(message):
    with open("distance.txt", "r") as file:
        src = file.read()
    if message.text not in src:
        msg = bot.send_message(message.chat.id, "ведите по указаном ростояниям")
        bot.register_next_step_handler(msg, distance)
    else:
        tasks["centr_hotel"] = float(message.text)
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(text="начать поиск", callback_data="3"))
        msg = bot.send_message(message.chat.id, "?", reply_markup=markup)


def photo_count(message):
    if message.text.isdigit() and int(message.text) > 0:
        tasks["photo_count"] = int(message.text)
        msg = bot.send_message(message.chat.id, "введите дату входа и выхода пример\n"
                                                   "(год)xxxx-(месяц)xx-(день)xx (пробел) xxxx-xx-xx")
        bot.register_next_step_handler(msg, data)
    else:
        msg = bot.send_message(message.chat.id, "неправилный ввод\nколичество должен быть числом ")
        bot.register_next_step_handler(msg, photo_count)


def data(message):
    try:
        _data = message.text.split()
        _data1 = _data[0].split("-")
        _data2 = _data[1].split("-")
        if len(_data1) == 3 and len(_data2) == 3:
            for i in range(2):
                if int(_data1[i + 1]) < 10:
                    _data1[i + 1] = "0" + str(int(_data1[i + 1]))
                if int(_data2[i + 1]) < 10:
                    _data2[i + 1] = "0" + str(int(_data2[i + 1]))
            tasks["checkin_date"] = "-".join(_data1)
            tasks["checkout_date"] = "-".join(_data2)

            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton(text="начать поиск", callback_data="3"))
            msg = bot.send_message(message.chat.id, "?", reply_markup=markup)
        else:
            msg = bot.send_message(message.chat.id, "неправилный флрмат даты\nвведите дату ещо раз")
            bot.register_next_step_handler(msg, data)
    except Exception:
        msg = bot.send_message(message.chat.id, "неправилный флрмат даты\nвведите дату ещо раз")
        bot.register_next_step_handler(msg, data)

@bot.message_handler(commands="help")
def help(message):
    with open("help.txt", "r", encoding="utf-8") as file:
        help = file.read()
    bot.send_message(message.chat.id, help)


@bot.message_handler(commands="history")
def history(message):
    bot.send_document(message.chat.id, document=open("history.csv", "rb"))

