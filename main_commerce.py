import telebot
from random import choice,randint
from telebot import types
import sqlite3
from datetime import datetime
import time
import smtplib
from email.mime.text import MIMEText
from geopy.geocoders import Nominatim
from validate_email import validate_email #pip install py3dns (?)
from email_check_and_send import my_valid_email, send_verification_email

geolocator = Nominatim(user_agent="city_validator") #city validator

#Создаем БД

conn = sqlite3.connect('users.db', check_same_thread=False)

with conn:
    conn.execute('''
        CREATE TABLE IF NOT EXISTS user_profiles (
            user_id INTEGER PRIMARY KEY,
            city TEXT,
            min_age INTEGER,
            max_age INTEGER,
            email TEXT,
            gender INTEGER,
            preferences INTEGER,
            name TEXT,
            age TEXT,
            balance INTEGER DEFAULT 0,
            photo BLOB,
            bio TEXT,
            status_dating INTEGER,
            last_online TEXT,
            amount_of_wins INTEGER DEFAULT 0,
            amount_of_pars INTEGER DEFAULT 0,
            subscribe INTEGER,
            last_email_send INTEGER,
            status_ban TEXT DEFAULT norm
        )
    ''')

with conn: 
    conn.execute('''
        CREATE TABLE IF NOT EXISTS votes (
            user_id INTEGER,
            battle_id INTEGER,
            vote_side TEXT,  -- 'left' или 'right'
            PRIMARY KEY (user_id, battle_id)
        )
    ''')
    
with conn:
    conn.execute('''
        CREATE TABLE IF NOT EXISTS evaluations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            evaluator_id INTEGER,
            evaluated_id INTEGER,
            evaluation_date TEXT,
            FOREIGN KEY (evaluator_id) REFERENCES user_profiles(user_id),
            FOREIGN KEY (evaluated_id) REFERENCES user_profiles(user_id)
        );
    ''')
    conn.commit()

with conn:
    conn.execute('''
        CREATE TABLE IF NOT EXISTS battle_queue (
        user_id INTEGER PRIMARY KEY,
        join_time INTEGER
        );
    ''')
    
with conn:
    conn.execute('''CREATE TABLE IF NOT EXISTS battles (
    battle_id INTEGER PRIMARY KEY AUTOINCREMENT,
    participant_1 INTEGER,
    participant_2 INTEGER,
    participant_1_photo BLOB,  -- Фото первого участника
    participant_2_photo BLOB,  -- Фото второго участника
    start_time INTEGER,
    end_time INTEGER,
    votes_participant_1 INTEGER DEFAULT 0,
    votes_participant_2 INTEGER DEFAULT 0,
    winner INTEGER,
    status TEXT DEFAULT 'active',
    FOREIGN KEY (participant_1) REFERENCES user_profiles(user_id),
    FOREIGN KEY (participant_2) REFERENCES user_profiles(user_id)
    );
    ''')

#Создаем кнопки, inline клавиатуры 
genders = types.ReplyKeyboardMarkup(resize_keyboard=True)
but_m = types.KeyboardButton('Парень')
but_j = types.KeyboardButton('Девушка')
genders.add(but_m,but_j)


start_menu = types.ReplyKeyboardMarkup(resize_keyboard=True)
but_znakomstva = types.KeyboardButton('Знакомства ❤️')
but_battle = types.KeyboardButton('Баттл Фото 🔥')
but_settings = types.KeyboardButton('Настройки ⚙️')
start_menu.add(but_znakomstva,but_battle, but_settings)

but_back = types.KeyboardButton('Назад')

dating_menu = types.ReplyKeyboardMarkup(resize_keyboard=True)
but_my_anket = types.KeyboardButton('Моя Анкета')
but_find = types.KeyboardButton('Смотреть анкеты')
dating_menu.add(but_my_anket, but_find, but_back)

looking_for_menu = types.ReplyKeyboardMarkup(resize_keyboard=True)
but_girl = types.KeyboardButton('Девушки')
but_boy = types.KeyboardButton('Парни')
but_dont_matter = types.KeyboardButton('Не важно')
looking_for_menu.add(but_girl,but_boy,but_dont_matter)

battle_menu = types.ReplyKeyboardMarkup(resize_keyboard=True)
but_my_profile = types.KeyboardButton('Мой Профиль')
but_list_battles = types.KeyboardButton('Активные Баттлы')
but_participation = types.KeyboardButton('Принять Участие')
but_my_battles = types.KeyboardButton('Мои Баттлы')
but_top_5 = types.KeyboardButton('Топ 5 участников')
battle_menu.add(but_my_profile, but_list_battles, but_participation, but_my_battles, but_top_5, but_back)

rating_menu = types.ReplyKeyboardMarkup(resize_keyboard=True)
but_like = types.KeyboardButton('Познакомиться')
but_dislike = types.KeyboardButton('Не нравится')
but_to_anket = types.KeyboardButton('К Анкете')
rating_menu.add(but_like,but_dislike,but_to_anket)

curr_battle_menu = types.ReplyKeyboardMarkup(resize_keyboard=True)
but_first = types.KeyboardButton('Слева лучше!')
but_sec = types.KeyboardButton('Справа лучше!')
but_to_menu = types.KeyboardButton('В меню')
curr_battle_menu.add(but_first, but_sec, but_to_menu)

univs = types.InlineKeyboardMarkup()
but_mirea = types.InlineKeyboardButton(f'РТУ МИРЭА', callback_data='univ_mirea')
but_hse = types.InlineKeyboardButton(f'НИУ ВШЭ', callback_data='univ_hse')
univs.add(but_mirea, but_hse)

markup_settings = types.ReplyKeyboardMarkup(resize_keyboard=True)
but_change_anket = types.KeyboardButton('Изменить анкету')
markup_settings.add(but_change_anket, but_back)

markup_change_anket = types.ReplyKeyboardMarkup(resize_keyboard=True)
but_name = types.KeyboardButton('Изменить имя')
but_city = types.KeyboardButton('Изменить город')
but_age = types.KeyboardButton('Изменить возраст')
but_prefer_age = types.KeyboardButton('Изменить предпочтения по возрасту')
but_gender = types.KeyboardButton('Изменить пол')
but_photo = types.KeyboardButton('Изменить фото')
markup_change_anket.add(but_photo, but_name, but_age, but_city, but_prefer_age, but_gender, but_back)

#define bot
bot = telebot.TeleBot('')

#define token for pay
TELEGRAM_PROVIDER_TOKEN = ""

#временные словари для разных функций
user_states = {} #в основном используется для заполнения анкеты. user_states[user_id] = 'wait bio' => следующее сообщение, которое отправит пользоавтель, будет описанием его анкеты
verif_codes = {} #тут хранятся коды для верификации email
payloads_ids = {} #сохраняем id платежей юзеров 


#------------------------------------------------------------------------------------------------------------------------------------------
#СИСТЕМНЫЕ ФУНКЦИИ
#------------------------------------------------------------------------------------------------------------------------------------------

#Проверка, сущесвует ли у пользователя анкета, или ее нужно создать
def is_profile_exists(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    with conn:
        result = conn.execute('''
            SELECT name, photo, gender, bio, age, city 
            FROM user_profiles 
            WHERE user_id = ?
        ''', (user_id,)).fetchone()
    if result:
        name, photo, gender, bio, age, city = result
        if name and photo and (gender == 1 or gender == 2) and bio and age and city:
            return True
        else:
            bot.send_message(chat_id, f'У вас еще нет анкеты, или она заполнена не до конца.\nИспользуйте команду /create_profile , чтобы создать или обновить анкету.')
            return False
    else:
        bot.send_message(chat_id, f'У вас еще нет анкеты, или она заполнена не до конца.\nИспользуйте команду /create_profile , чтобы создать или обновить анкету.')
        return False

    
#проверяем, забанен пользователь или нет. его статус мы сохраняем в БД. 
def get_status(user_id):
    with conn:
        res1 = conn.execute('SELECT status_ban FROM user_profiles WHERE user_id = ?', (user_id,)).fetchone()
    if res1:
        return res1[0]
    else:
        return 'norm'
    
#проверка, подтвердил ли пользователь свою почту 
def is_profile_verified(user_id):
    with conn:
        email = conn.execute('SELECT email FROM user_profiles WHERE user_id = ?',(user_id,)).fetchone()
    if email != (None,) and email != None:
        return True
    else:
        return False
        
#При поиске анкеты учитывается ласт онлайн в боте. При нажатии любой кнопки пользователем, запускается эта функция, обновляя его ласт онлайн в боте.
def update_last_online(message):
    user_id = message.from_user.id
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with conn:
        result = conn.execute('SELECT user_id FROM user_profiles WHERE user_id = ?', (user_id,)).fetchone()
    if result is None:
        with conn:
            conn.execute('''
                INSERT INTO user_profiles (user_id) VALUES (?)
            ''', (user_id,))
    with conn:
        conn.execute('''
            UPDATE user_profiles
            SET last_online = ?
            WHERE user_id = ?
        ''', (current_time, user_id))
        conn.commit()


#для заполнения / изменения анкеты
        
def get_name(message, is_edit):
    if message.content_type != 'text':
        bot.send_message(message.chat.id, "Пожалуйста, введите текст для имени")
        bot.register_next_step_handler(message, get_name, is_edit)
        return
    name = message.text
    if len(name) >= 25:
        bot.send_message(message.chat.id, "Длина имени должна быть меньше 25 символов. Попробуйте снова.")
        bot.register_next_step_handler(message, get_name, is_edit)
        return
    with conn:
                        conn.execute('''
        UPDATE user_profiles
        SET name = ?
        WHERE user_id = ?
    ''', (name, message.from_user.id))
    if is_edit:
        bot.send_message(message.chat.id, "Ваше имя успешно изменено!")
    else:
        bot.send_message(message.chat.id, f'Приятно познакомиться! {name}, ты Парень или Девушка?',reply_markup = genders)
        bot.register_next_step_handler(message, get_gender, is_edit = False)

def get_gender(message, is_edit):
    chat_id = message.chat.id
    user_id = message.from_user.id
    if message.content_type == 'text':
        gender = message.text
        gender = gender.lower()
        if gender != 'парень' and gender != 'девушка':
            bot.send_message(chat_id, 'Напишите текстом: Парень вы или Девушка',reply_markup = genders)
            bot.register_next_step_handler(message, get_gender, is_edit)
            return 
        else:
            if gender == 'парень':
                gender = 1
                with conn:
                    conn.execute('''
                    UPDATE user_profiles
                    SET gender = ?
                    WHERE user_id = ?
                ''', (gender,user_id))
            else:
                gender = 2
                with conn:
                    conn.execute('''
                    UPDATE user_profiles
                    SET gender = ?
                    WHERE user_id = ?
                ''', (gender,user_id))
        if is_edit:
            bot.send_message(chat_id, f'Ваш пол успешно изменен!')
        else:
            bot.send_message(chat_id, f'Отлично! Теперь выбери, люди какого пола тебе интересны\nДевушки/Парни/Не важно',reply_markup = looking_for_menu)
            bot.register_next_step_handler(message, get_prefs, is_edit)
    else:
        bot.send_message(chat_id, 'Напишите: Парень вы или Девушка',reply_markup = genders)
        bot.register_next_step_handler(message, get_gender, is_edit)
        return 
        
def get_prefs(message, is_edit):
    chat_id = message.chat.id
    user_id = message.from_user.id
    if message.content_type == 'text':
        prefers = message.text
        prefers = prefers.lower()
        if prefers not in ['девушки','парни','не важно']:
            bot.send_message(chat_id, 'Выбери 1 из вариантов:\nДевушки\nПарни\nНе важно',reply_markup=looking_for_menu)
            bot.register_next_step_handler(message, get_prefs, is_edit)
            return 
        with conn:
            if prefers == "парни":
                conn.execute('UPDATE user_profiles SET preferences = 1 WHERE user_id = ?', (user_id,))
            elif prefers == "девушки":
                conn.execute('UPDATE user_profiles SET preferences = 2 WHERE user_id = ?', (user_id,))
            elif prefers == "не важно":
                conn.execute('UPDATE user_profiles SET preferences = 3 WHERE user_id = ?', (user_id,))
        if is_edit:
            bot.send_message(chat_id, f'Ваши предпочтения успешно изменены!')
        else:
            bot.send_message(chat_id, f'Теперь расскажи немного о себе',reply_markup = types.ReplyKeyboardRemove())
            bot.register_next_step_handler(message, get_bio, is_edit)
    else:
        bot.send_message(chat_id, 'Выбери 1 из вариантов:\nДевушки\nПарни\nНе важно',reply_markup=looking_for_menu)
        bot.register_next_step_handler(message, get_prefs, is_edit)
        return

def get_bio(message, is_edit):
    chat_id = message.chat.id
    user_id = message.from_user.id
    if message.content_type == 'text':
        bio = message.text
        if len(bio) >= 150:
            bot.send_message(chat_id, 'Длина описания должна быть меньше 150 символов')
            bot.register_next_step_handler(message, get_bio, is_edit)
            return 
        with conn:
            conn.execute('''
            UPDATE user_profiles
            SET bio = ?
            WHERE user_id = ?
        ''', (bio,user_id))
        if is_edit:
            bot.send_message(f'Ваше описание успешно изменено!')
        else:
            bot.send_message(chat_id, f'Отлично! Введи свой возраст')
            bot.register_next_step_handler(message, get_age, is_edit)
    else:
        bot.send_message(chat_id, 'Напишите описание текстом')
        bot.register_next_step_handler(message, get_bio, is_edit)
        return 

def get_age(message, is_edit):
    chat_id = message.chat.id
    user_id = message.from_user.id
    if message.content_type == 'text':
        age = message.text
        if not(age.isdigit()) or int(age)<=10 or int(age) >= 150:
            bot.send_message(chat_id,'Введите одно число - ваш настоящий возраст')
            bot.register_next_step_handler(message, get_age, is_edit)
            return 
        with conn:
            conn.execute('''
            UPDATE user_profiles
            SET age = ?
            WHERE user_id = ?
            ''', (age,user_id))
        if is_edit:
            bot.send_message(f'Ваш возраст успешно изменен!')
        else:
            bot.send_message(chat_id, f'Теперь напишите, в каком диапазоне возраста вы ищите людей\nНапишите 2 числа через пробел: минимальный и максимальный возраст соответсвенно\n\nПример: 20 30\nОзначает, что вы ищите людей возрастом от 20 до 30 лет включительно')
            bot.register_next_step_handler(message, get_pref_age, is_edit)
    else:
        bot.send_message(chat_id, 'Введите одно число - ваш настоящий возраст')
        bot.register_next_step_handler(message, get_age, is_edit)
        return

def get_pref_age(message, is_edit):
    chat_id = message.chat.id
    user_id = message.from_user.id
    if message.content_type == 'text':
        text = message.text
        if len(text.split()) != 2:
            bot.send_message(chat_id, f'Введите 2 числа через пробел')
            bot.register_next_step_handler(message, get_pref_age, is_edit)
            return 
        age1,age2 = text.split()
        if not(age1.isdigit()) or not(age2.isdigit()):
            bot.send_message(chat_id, f'Введите 2 числа через пробел')
            bot.register_next_step_handler(message, get_pref_age, is_edit)
            return 
        if int(age1) <= 10 or int(age1)>150 or int(age2)<=10 or int(age2)>150:
            bot.send_message(chat_id, f'Оба числа должны быть более 10, и менее 150')
            bot.register_next_step_handler(message, get_pref_age, is_edit)
            return
        elif int(age1)>int(age2):
            bot.send_message(chat_id, f'Первое число - минимальная возрастная граница, оно не может быть меньше второго')
            bot.register_next_step_handler(message, get_pref_age, is_edit)
            return 
        with conn:
            conn.execute('''
            UPDATE user_profiles
            SET min_age = ?, max_age = ?
            WHERE user_id = ?
            ''', (age1,age2, user_id))
        if is_edit:
            bot.send_message(f'Ваши предпочтения успешно изменены!')
        else:
            bot.send_message(chat_id, f'Хорошо, теперь введите название города/населенного пункта, в котором вы ищите знакомства\nПримечание: Лучше писать название города на русском языке, в поиске Москва ≠ Moscow')
            bot.register_next_step_handler(message, get_city, is_edit)
    else:
        bot.send_message(chat_id, f'Введите 2 числа через пробел')
        bot.register_next_step_handler(message, get_pref_age, is_edit)

def get_city(message, is_edit):
    chat_id = message.chat.id
    user_id = message.from_user.id
    if message.content_type == 'text':
        text = message.text
        loc = geolocator.geocode(text)
        if loc:
            text = text.title()
            with conn:
                        conn.execute('''
                UPDATE user_profiles
                SET city = ?
                WHERE user_id = ?
            ''', (text, user_id))
            if is_edit:
                bot.send_message(f'Город успешно изменен!')
            else:
                bot.send_message(chat_id, f'Отлично! Осталось прикрепить фото')
                bot.register_next_step_handler(message, get_photo, is_edit)
        else:
            bot.send_message(chat_id, f'Вы ввели город, неизвестный нам\nПопробуйте ввести название другого ближайшего к вам города или населенного пункта')
            bot.register_next_step_handler(message, get_city, is_edit)
            return 
    else:
        bot.send_message(chat_id, f'Введите название города текстом')
        bot.register_next_step_handler(message, get_city, is_edit)
        return 

def get_photo(message, is_edit):
    chat_id = message.chat.id
    user_id = message.from_user.id
    if message.content_type == 'photo':
        file_id = message.photo[-1].file_id
        file_info = bot.get_file(file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        with conn:
            conn.execute('''
            UPDATE user_profiles
            SET photo = ?
            WHERE user_id = ?
        ''', (downloaded_file,user_id))
        if is_edit:
            bot.reply_to(message, "Новое фото успешно загружено!",reply_markup = start_menu)
        else:
            bot.reply_to(message, "Фото успешно загружено, ваша анкета готова!",reply_markup = start_menu)
    else:
        bot.send_message(chat_id, 'Отправьте ваше Фото',reply_markup = types.ReplyKeyboardRemove())
        bot.register_next_step_handler(message, get_photo, is_edit)
        return 
