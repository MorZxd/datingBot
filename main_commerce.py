import telebot
from random import choice,randint
from telebot import types
import sqlite3
from datetime import datetime
import time
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

#создаем таблицы внутри БД 

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

with conn:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS referrals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            referred_user_id INTEGER NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS referral_rewards (
            user_id INTEGER PRIMARY KEY,
            referral_count INTEGER DEFAULT 0
        );
    """)

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
but_referals = types.KeyboardButton('Реферальная система')
but_balance = types.KeyboardButton('Пополнить баланс')
markup_settings.add(but_change_anket, but_referals, but_balance, but_back)

markup_change_anket = types.ReplyKeyboardMarkup(resize_keyboard=True)
but_name = types.KeyboardButton('Изменить имя')
but_city = types.KeyboardButton('Изменить город')
but_age = types.KeyboardButton('Изменить возраст')
but_prefer_age = types.KeyboardButton('Изменить предпочтения по возрасту')
but_gender = types.KeyboardButton('Изменить пол')
but_photo = types.KeyboardButton('Изменить фото')
markup_change_anket.add(but_photo, but_name, but_age, but_city, but_prefer_age, but_gender, but_back)


markup_referals = types.ReplyKeyboardMarkup(resize_keyboard=True)
but_referals = types.KeyboardButton('🔗Реферальная ссылка')
markup_referals.add(but_referals, "🏆Мои награды", "🔢Количество рефералов", but_back)

#define bot
bot = telebot.TeleBot('7686184399:AAE05Ll7kwOtIP9SmbNwhiSL4jh0zD-UB9E')

#define token for pay
TELEGRAM_PROVIDER_TOKEN = "390540012:LIVE:60900"

ADMIN_CHAT_ID = 6670128924 #Катя доп аккаунт

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
        bot.send_message(message.chat.id, "Ваше имя успешно изменено!", reply_markup = start_menu)
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
            bot.send_message(chat_id, f'Ваш пол успешно изменен!', reply_markup = start_menu)
        else:
            bot.send_message(chat_id, f'Отлично! Теперь выбери, люди какого пола тебе интересны\n\n<i>Выберите: Девушки/Парни/Не важно</i>',reply_markup = looking_for_menu, parse_mode='HTML')
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
            bot.send_message(chat_id, f'Ваши предпочтения успешно изменены!', reply_markup = start_menu)
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
            bot.send_message(chat_id, f'Ваше описание успешно изменено!', reply_markup=start_menu)
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
            bot.send_message(chat_id, f'Ваш возраст успешно изменен!', reply_markup=start_menu)
        else:
            bot.send_message(chat_id, f'Теперь напишите, в каком диапазоне возраста вы ищите людей\nНапишите 2 числа через пробел: минимальный и максимальный возраст соответсвенно\n\n<i>Пример: 20 30\nОзначает, что вы ищите людей возрастом от 20 до 30 лет включительно</i>',parse_mode="HTML")
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
            bot.send_message(chat_id, f'Ваши предпочтения успешно изменены!', reply_markup= start_menu)
        else:
            bot.send_message(chat_id, f'Хорошо, теперь введите название города/населенного пункта, в котором вы ищите знакомства\n\n<i>Примечание: В случае с малоизвестным городом программа может неправильно определеять его точное название. Если не уверены -- проверьте город после заполнения анкеты. Анкету всегда можно изменить в настройках</i>', parse_mode='HTML')
            bot.register_next_step_handler(message, get_city, is_edit)
    else:
        bot.send_message(chat_id, f'Введите 2 числа через пробел')
        bot.register_next_step_handler(message, get_pref_age, is_edit)

def normalize_city_to_russian(city_name):
    geolocator2 = Nominatim(user_agent="city_normalizer")
    location = geolocator2.geocode(city_name, language="ru")  # Приведение к русскому языку
    if location:
        city = location.address.split(",")[0]  # Берем только первую часть названия
        # Удаляем префиксы вроде "городской округ"
        if city.startswith("городской округ "):
            city = city.replace("городской округ ", "", 1)
        return city.strip()
    return None

def get_city(message, is_edit):
    chat_id = message.chat.id
    user_id = message.from_user.id
    if message.content_type == 'text':
        text = message.text
        loc = normalize_city_to_russian(text)
        if loc:
            text = text.title()
            with conn:
                        conn.execute('''
                UPDATE user_profiles
                SET city = ?
                WHERE user_id = ?
            ''', (loc, user_id))
            if is_edit:
                bot.send_message(chat_id, f'Город успешно изменен!', reply_markup=start_menu)
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
        with conn:
            conn.execute('''
                DELETE FROM evaluations
                WHERE evaluator_id = ? OR evaluated_id = ?
            ''', (user_id, user_id))
            conn.commit()
        if is_edit:
            bot.reply_to(message, "Новое фото успешно загружено!",reply_markup = start_menu)
        else:
            bot.reply_to(message, "Фото успешно загружено, ваша анкета готова!",reply_markup = start_menu)
            with conn:
                conn.execute('''
                    DELETE FROM evaluations
                    WHERE evaluator_id = ? OR evaluated_id = ?
                ''', (user_id, user_id))
                conn.commit()
    else:
        bot.send_message(chat_id, 'Отправьте ваше Фото',reply_markup = types.ReplyKeyboardRemove())
        bot.register_next_step_handler(message, get_photo, is_edit)
        return 

def add_referral(referrer_id, referred_id):
    with conn:
        # all_amount = conn.execute("""
        #     SELECT COUNT(*) FROM referrals WHERE user_id = ? AND referred_user_id = ?
        # """, (referrer_id, referred_id))
        is_user_exists = conn.execute("""
            SELECT COUNT(*) FROM user_profiles WHERE user_id = ?
        """, (referred_id,)).fetchone()[0]
        if is_user_exists:
            bot.send_message(referred_id, f'Вы уже запускали бота.')
            return
        conn.execute("INSERT INTO referrals (user_id, referred_user_id) VALUES (?, ?)", (referrer_id, referred_id))
        conn.execute("""
            INSERT INTO referral_rewards (user_id, referral_count)
            VALUES (?, 1)
            ON CONFLICT(user_id) DO UPDATE SET referral_count = referral_count + 1
        """, (referrer_id,))
        bot.send_message(referred_id, "Вы зарегистрированы по реферальной ссылке!")
        bot.send_message(referrer_id, f"К вам присоединился новый реферал!")

#------------------------------------------------------------------------------------------------------------------------------------------
#ФУНКЦИИ ДЛЯ ЗНАКОМСТВ
#------------------------------------------------------------------------------------------------------------------------------------------

#когда пользователь оценяет чью-то анкету, отмечаем это, чтобы не показывать ее снова
def mark_as_viewed(user_id, match_id):
    with conn:
        conn.execute('''
            INSERT INTO evaluations (evaluator_id, evaluated_id) VALUES (?, ?)
        ''', (user_id, match_id))
        conn.commit()
        
#в каких-то случаях нужно удалять отметки, что анкета уже показывалась. Например тогда, когда пользователь создает новую анкету
def remove_match(user_id, match_id):
    with conn:
        conn.execute('''
            DELETE FROM evaluations
            WHERE evaluator_id = ? AND evaluated_id = ?
        ''', (user_id, match_id))
        conn.commit()
        
#Когда количество зависимостей между пользователями превышает какое-то большое количество, лучше их обнулять, чтобы не переполнять память 
def clear_evaluations_if_needed():
    with conn:
        # Проверяем количество строк
        row_count = conn.execute('SELECT COUNT(*) FROM evaluations').fetchone()[0]
        # Если строк больше 300,000, очищаем таблицу
        if row_count >= 100000:
            conn.execute('DELETE FROM evaluations')
            conn.commit()

#Функция для поиска оптимальной анкеты пользователю + генерация и отправка сообщения.        
def find_matc(user_id, chat_id):
    with conn:
        result = conn.execute('SELECT preferences, gender  FROM user_profiles WHERE user_id = ?', (user_id,)).fetchone()
    if result:
        prefs, user_gender = result
        with conn:
            result = conn.execute('''
                SELECT u.user_id, u.name, u.photo, u.bio, u.age, u.amount_of_wins, u.amount_of_pars, u.city
                FROM user_profiles u
                LEFT JOIN evaluations e ON u.user_id = e.evaluated_id AND e.evaluator_id = ?
                WHERE e.evaluated_id IS NULL
                AND u.user_id != ?
                AND u.city = (SELECT city FROM user_profiles WHERE user_id = ?)
                AND (u.gender = ? OR ? = 3)
                AND (u.preferences = ? OR u.preferences = 3)
                AND u.age BETWEEN (SELECT min_age FROM user_profiles WHERE user_id = ?) 
                            AND (SELECT max_age FROM user_profiles WHERE user_id = ?)
                AND (u.min_age <= (SELECT age FROM user_profiles WHERE user_id = ?)
                    AND u.max_age >= (SELECT age FROM user_profiles WHERE user_id = ?))
                AND u.name IS NOT NULL 
                AND u.photo IS NOT NULL 
                AND u.bio IS NOT NULL 
                AND u.age IS NOT NULL 
                AND u.amount_of_wins IS NOT NULL
                AND u.amount_of_pars IS NOT NULL
                ORDER BY u.last_online DESC
                LIMIT 1
            ''', (user_id, user_id, user_id, prefs, prefs, user_gender, user_id, user_id, user_id, user_id)).fetchone()
        if result:
            match_id, match_name, match_photo, match_bio, match_age, match_wins, match_pars, match_city= result
            match_text = f"{match_name}, {match_age}, {match_city} - {match_bio}\n{match_wins} побед из {match_pars} Баттлов"
            markup = types.InlineKeyboardMarkup()
            btn_like = types.InlineKeyboardButton("Познакомиться", callback_data=f"like_{match_id}")
            btn_dislike = types.InlineKeyboardButton("Не нравится", callback_data=f"dislike_{match_id}")
            btn_exit = types.InlineKeyboardButton("Выход", callback_data=f"exit_{match_id}")
            btn_report = types.InlineKeyboardButton("Жалоба", callback_data=f"report_{match_id}")
            btn_message = types.InlineKeyboardButton("💌", callback_data = f"message_{match_id}")
            markup.add(btn_like, btn_dislike, btn_message)
            markup.add(btn_exit, btn_report)
            mark_as_viewed(user_id,match_id)
            bot.send_photo(chat_id, match_photo, caption=match_text,reply_markup=markup)
        else:
            # Если не найдено подходящих анкет, выводим сообщение
            bot.send_message(chat_id, "Все анкеты уже просмотрены\nПриглашай друзей, чем больше людей в боте, тем интереснее им пользоваться!",reply_markup=dating_menu)
    else:
        bot.send_message(chat_id, f'У вас еще нет анкеты, или она заполнена не до конца.\nИспользуйте команду /create_profile , чтобы создать или обновить анкету.')

#есть много разветвлений, когда человек ставит лайк. вынесем в отдельную функцию
def give_like(chat_id, user_id, match_id, evaluator_username, from_girl_to_man = False, with_message = False, message = ""):
    with conn:
        evaluator_profile = conn.execute('''
            SELECT name, photo, bio, age, amount_of_wins, amount_of_pars, city FROM user_profiles WHERE user_id = ?
        ''', (user_id,)).fetchone()
    if evaluator_profile:
        evaluator_name, evaluator_photo, evaluator_bio, ev_age, ev_wins, ev_pars, ev_city = evaluator_profile
        match_user_id = match_id
        if match_user_id in user_states and user_states[match_user_id] == 'banned':
            bot.send_message(user_id, 'К сожалению, данный пользователь был забанен.')
        else:
            vzaim = types.InlineKeyboardMarkup()
            but_vzaim = types.InlineKeyboardButton(f'👍', callback_data=f'vzaim {user_id} {evaluator_username}')
            but_dontlike = types.InlineKeyboardButton(f'👎', callback_data=f'nevzaim {user_id}')
            vzaim.add(but_vzaim, but_dontlike)
            if (evaluator_username != None):
                if from_girl_to_man:
                    evaluator_text = f"Ваша анкета понравилась пользователю ???||\(если вы взаимно лайкните — вам покажется юзернейм\)||\nЕго анкета:\n\n"
                    if with_message:
                        evaluator_text += f"{evaluator_name}, {ev_age}, {ev_city} \- {evaluator_bio}\n\n{ev_wins} побед из {ev_pars} Баттлов\n\nЛичное сообщение💌: {message}"
                        bot.send_message(chat_id, 'Сообщение успешно отправлено!',reply_markup=dating_menu)
                    else:
                        evaluator_text += f"{evaluator_name}, {ev_age}, {ev_city} \- {evaluator_bio}\n\n{ev_wins} побед из {ev_pars} Баттлов"
                    bot.send_photo(match_user_id, evaluator_photo, caption=evaluator_text, reply_markup=vzaim, parse_mode="MarkdownV2")
                else:
                    evaluator_text = f"Ваша анкета понравилась пользователю @{evaluator_username}!\nЕго анкета:\n\n"
                    if with_message:
                        evaluator_text += f"{evaluator_name}, {ev_age}, {ev_city} - {evaluator_bio}\n\n{ev_wins} побед из {ev_pars} Баттлов\n\nЛичное сообщение💌: {message}"
                        
                    else:
                        evaluator_text += f"{evaluator_name}, {ev_age}, {ev_city} - {evaluator_bio}\n\n{ev_wins} побед из {ev_pars} Баттлов"
                    bot.send_photo(match_user_id, evaluator_photo, caption=evaluator_text, reply_markup=vzaim)
            else:
                evaluator_text = f"Ваша анкета понравилась пользователю {evaluator_name}!\nЕго анкета:\n\n"
                evaluator_text += f"{evaluator_name}, {ev_age}, {ev_city} - {evaluator_bio}\n\n{ev_wins} побед из {ev_pars} Баттлов"
                bot.send_photo(match_user_id, evaluator_photo, caption=evaluator_text, reply_markup=vzaim)
    find_matc(user_id,chat_id)

def give_vzaim(user_id, match_id, evaluator_username):
    with conn:
        evaluator_profile = conn.execute('''
        SELECT name, photo, bio, age, amount_of_wins, amount_of_pars, city FROM user_profiles WHERE user_id = ?
        ''', (user_id,)).fetchone()
    if evaluator_profile:
        evaluator_name, evaluator_photo, evaluator_bio, ev_age, ev_wins, ev_pars, ev_city = evaluator_profile
        with conn:
            result = conn.execute('SELECT user_id FROM user_profiles WHERE user_id = ?', (match_id,)).fetchone()
        if result:
            match_user_id = result
            if match_user_id in user_states and user_states[match_user_id] == 'banned':
                bot.send_message(user_id, 'К сожалению, данный пользователь был забанен.')
            else:
                if evaluator_username != None:
                    evaluator_text = f"Ура! Взаимный лайк с @{evaluator_username}!\n\nЕго анкета:\n\n"
                else:
                    evaluator_text = f"Ура! Взаимный лайк с @{evaluator_name}!\n\nЕго анкета:\n\n"
                evaluator_text += f"{evaluator_name}, {ev_age}, {ev_city} - {evaluator_bio}\n\n{ev_wins} побед из {ev_pars} Баттлов"
                bot.send_photo(match_user_id, evaluator_photo, caption=evaluator_text)
                with conn:
                    conn.execute('''
                        INSERT INTO evaluations (evaluator_id, evaluated_id) VALUES (?, ?)
                    ''', (user_id, match_id))
                    conn.commit()
                with conn:
                    conn.execute('''
                        INSERT INTO evaluations (evaluator_id, evaluated_id) VALUES (?, ?)
                    ''', (match_id, user_id))
                    conn.commit()
                # bot.send_message(user_id, f'Отправили взаимный лайк!', reply_markup=start_menu)
    


#------------------------------------------------------------------------------------------------------------------------------------------
#ФУНКЦИИ ДЛЯ ФОТО-БАТТЛОВ
#------------------------------------------------------------------------------------------------------------------------------------------

#Функция для начала баттла, когда уже нашлись участники 
def start_battle(part_1_id,part_2_id):
    start_time = int(time.time())
    end_time = start_time + 86400
    participant_1_photo = conn.execute('SELECT photo FROM user_profiles WHERE user_id = ?', (part_1_id,)).fetchone()[0]
    participant_2_photo = conn.execute('SELECT photo FROM user_profiles WHERE user_id = ?', (part_2_id,)).fetchone()[0]
    # Сохраняем новый баттл с фото участников
    with conn:
        conn.execute('''
            INSERT INTO battles (participant_1, participant_2, participant_1_photo, participant_2_photo, start_time, end_time)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (part_1_id, part_2_id, participant_1_photo, participant_2_photo, start_time, end_time))
        conn.commit()
        
#Функция для поиска 2ого человека для баттла
def find_opponent_for_battle(user_id):
    with conn:
        user = conn.execute('SELECT gender FROM user_profiles WHERE user_id = ?', (user_id,)).fetchone()
    if user:
        user_gender = user[0]
        opponent = conn.execute('''
                SELECT battle_queue.user_id FROM battle_queue
                JOIN user_profiles ON battle_queue.user_id = user_profiles.user_id
                WHERE user_profiles.gender = ? AND battle_queue.user_id != ?
                ORDER BY battle_queue.join_time ASC
                LIMIT 1
            ''', (user_gender, user_id)).fetchone()
        if opponent:
            opponent_id = opponent[0]
            start_battle(user_id, opponent_id)
            with conn:
                res1 = conn.execute('SELECT name, age, photo FROM user_profiles WHERE user_id = ?', (user_id,)).fetchone()
                res2 = conn.execute('SELECT name, age, photo FROM user_profiles WHERE user_id = ?', (opponent_id,)).fetchone()
                conn.execute('DELETE FROM battle_queue WHERE user_id IN (?, ?)', (user_id, opponent_id))
                conn.commit()
            if res1 and res2:
                name1, age1, photo1 = res1
                name2, age2, photo2  = res2
                bot.send_photo(user_id, photo2, f"Соперник найден!\n\n{name2}, {age2}")
                bot.send_photo(opponent_id,photo1, f"Соперник найден!\n\n{name1}, {age1}")
            else:
                bot.send_message(user_id, 'какая-то ошибка с баттлом. пишите в поддержку')
                bot.send_message(opponent_id, 'какая-то ошибка с баттлом. пишите в поддержку')
        else:
            bot.send_message(user_id, "На данный момент нет доступных соперников. Вам придет уведомление, как только баттл начнется.")
        
#добавление в очередь поиска 2ого человека для баттла 
def join_battle(message):
    current_time = int(time.time())
    user_id = message.from_user.id
    chat_id = message.chat.id
    with conn:
        active_battles_count = conn.execute('''
            SELECT COUNT(*)
            FROM battles
            WHERE (participant_1 = ? OR participant_2 = ?) AND end_time > ?
        ''', (user_id, user_id, current_time)).fetchone()[0]
        if active_battles_count >= 1:
            bot.send_message(chat_id, f'Вы уже участвуете в баттле, дождитесь его завершения')
            return 
    if is_profile_exists(message):
        with conn:
            in_battle = conn.execute('SELECT 1 FROM battle_queue WHERE user_id = ?', (user_id,)).fetchone()
            if in_battle:
                bot.send_message(chat_id, "Вы уже в очереди на участие в фото-баттле")
                return 
            conn.execute('INSERT INTO battle_queue (user_id, join_time) VALUES (?, ?)', (user_id, int(time.time())))
            conn.commit()
        bot.send_message(chat_id, "Вы успешно записались на участие в фото-баттле! Ждем соперника...")
        find_opponent_for_battle(user_id)
        
#Функция для отображения баттла, в котором ты сейчас участвуешь 

def my_battles(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    battles = conn.execute('''
        SELECT battle_id, participant_1, participant_2, participant_1_photo, participant_2_photo, end_time, votes_participant_1, votes_participant_2
        FROM battles
        WHERE (participant_1 = ? OR participant_2 = ?) AND end_time > ?
    ''', (user_id, user_id, int(time.time()))).fetchall()
    if not battles:
        bot.send_message(chat_id, "У вас нет активных баттлов.")
    else:
        for battle in battles:
            battle_id, participant_1, participant_2,photo1, photo2, end_time, votes1, votes2 = battle
            if participant_1 == user_id:
                opponent_id = participant_2
                yourvotes = votes1
                oppvotes = votes2
                opphoto = photo2
            else:
                opponent_id = participant_1
                yourvotes = votes2
                oppvotes = votes1
                opphoto = photo1
                
            opponent = conn.execute('SELECT name FROM user_profiles WHERE user_id = ?', (opponent_id,)).fetchone()
            opponent_name = opponent[0] if opponent else "Неизвестно"
            bot.send_photo(chat_id,opphoto,caption= f"Баттл с {opponent_name}\nГолосов за вас: {yourvotes}\nГолосов за {opponent_name}: {oppvotes}")
            
#Баттлы длятся 24 часа. Чтобы не писать отдельную программу, проверяющую каждую секунду, закончился ли щас какой-то баттл, я написал эту функцию. Но правильнее и удобнее было бы написать отдельный файл с проверкой.
def check_for_completed_battles():
    current_time = int(time.time())
    finished_battles = conn.execute('''
        SELECT battle_id, participant_1, participant_2, votes_participant_1, votes_participant_2
        FROM battles
        WHERE end_time <= ? AND status = ?
    ''', (current_time, 'active')).fetchall()
    for battle in finished_battles:
        battle_id, participant_1, participant_2, votes_1, votes_2 = battle
        if votes_1 > votes_2:
            winner_id = participant_1
            loser_id = participant_2
        elif votes_2 > votes_1:
            winner_id = participant_2
            loser_id = participant_1
        else:
            winner_id = None
        conn.execute('''
            UPDATE battles
            SET status = 'completed'
            WHERE battle_id = ?
        ''', (battle_id,))
        clean_up_votes(battle_id)
        notify_battle_result(participant_1, participant_2, winner_id, votes_1, votes_2)
        
emoji_dict = {
    1: '1️⃣',
    2: '2️⃣',
    3: '3️⃣',
    4: '4️⃣',
    5: '5️⃣'
}

#Поиск топ5 участникам по количеству побед в баттлах 
def top_5_participants(message):
    flag = True
    chat_id = message.chat.id
    with conn:
        top_users = conn.execute('''
            SELECT name, age, photo, amount_of_wins 
            FROM user_profiles 
            ORDER BY amount_of_wins DESC
            LIMIT 5
        ''').fetchall()
    if top_users and len(top_users)==5:
        media_group = []
        text = ''
        i = 0
        for user in top_users:
            i += 1
            name, age, photo, wins = user
            if name and age and photo and (wins >= 0):
                media_group.append(types.InputMediaPhoto(photo))
                text += f'{emoji_dict.get(i,i)} Место - {name}, {age}, {wins} побед\n'
            else:
                flag = False
                bot.send_message(chat_id, f'У некоторых людей из топа не заполнена анкета. Сейчас невозможно определить Топ 5')
                break
                
        if flag:
            bot.send_media_group(chat_id,media_group)
            bot.send_message(chat_id,text)
    else:
        bot.send_message(chat_id,f'Пока слишком мало участников для составления рейтинга')

#функция для отображения баттлов пользователям 
def show_next_battle(chat_id, user_id):
    current_time = int(time.time())
    with conn:
        # Получаем первый активный баттл, в котором пользователь еще не голосовал
        battle = conn.execute('''
            SELECT battle_id, participant_1, participant_2, end_time, participant_1_photo, participant_2_photo
            FROM battles
            WHERE end_time > ? AND battle_id NOT IN (SELECT battle_id FROM votes WHERE user_id = ?)
            ORDER BY end_time ASC
            LIMIT 1
        ''', (current_time, user_id)).fetchone()
    if battle:
        battle_id, left_user_id, right_user_id, end_time, photo1, photo2 = battle
        left_user = conn.execute('SELECT name, age FROM user_profiles WHERE user_id = ?', (left_user_id,)).fetchone()
        right_user = conn.execute('SELECT name, age FROM user_profiles WHERE user_id = ?', (right_user_id,)).fetchone()
        if left_user and right_user:
            left_username, age1 = left_user
            right_username, age2 = right_user
            media_group = [
            types.InputMediaPhoto(photo1),
            types.InputMediaPhoto(photo2)
            ]
            bot.send_media_group(
                user_id,media_group
            )
            bot.send_message(user_id,f'За кого голосуешь?\nНа 1 фото: {left_username}, {age1}\nНа 2 фото: {right_username}, {age2}', reply_markup=create_battle_vote_exit_markup(battle_id, left_username,right_username))
        else:
            bot.send_message(chat_id, f'нет баттлов {left_user}, {right_user}, {left_user_id}, {right_user_id}')
    else:
        bot.send_message(user_id, f'Нет активных баттлов.')
        
#когда баттл закончился, отправляем его участникам сообщение с его результатами
def notify_battle_result(participant_1, participant_2, winner_id, votes1, votes2):
    with conn:
        res1 = conn.execute('SELECT name, photo, age FROM user_profiles WHERE user_id = ?', (participant_1,)).fetchone()
        res2 = conn.execute('SELECT name, photo, age FROM user_profiles WHERE user_id = ?', (participant_2,)).fetchone()
    if res1 and res2:
        name1,photo1,age1 = res1
        name2, photo2, age2 = res2
        if winner_id:
            if participant_1 == winner_id:
                with conn:
                    conn.execute('UPDATE user_profiles SET amount_of_wins = amount_of_wins + 1 WHERE user_id = ?', (participant_1,))
                    conn.execute('UPDATE user_profiles SET amount_of_pars = amount_of_pars + 1 WHERE user_id = ?', (participant_1,))
                    conn.execute('UPDATE user_profiles SET amount_of_pars = amount_of_pars + 1 WHERE user_id = ?', (participant_2,))
                bot.send_photo(participant_1,photo2, caption=f'Поздравляем! Вы выйграли в баттле против {name2}, {age2} со счетом {votes1}-{votes2}')
                bot.send_photo(participant_2,photo1, caption=f'Вы проиграли в баттле против {name1}, {age1} со счетом {votes2}-{votes1}')
            else:
                with conn:
                    conn.execute('UPDATE user_profiles SET amount_of_wins = amount_of_wins + 1 WHERE user_id = ?', (participant_2,))
                    conn.execute('UPDATE user_profiles SET amount_of_pars = amount_of_pars + 1 WHERE user_id = ?', (participant_2,))
                    conn.execute('UPDATE user_profiles SET amount_of_pars = amount_of_pars + 1 WHERE user_id = ?', (participant_1,))
                bot.send_photo(participant_2,photo1, caption=f'Поздравляем! Вы выйграли в баттле против {name1}, {age1} со счетом {votes2}-{votes1}')
                bot.send_photo(participant_1,photo2, caption=f'Вы проиграли в баттле против {name2}, {age2} со счетом {votes1}-{votes2}')
        else:
            with conn:
                conn.execute('UPDATE user_profiles SET amount_of_pars = amount_of_pars + 1 WHERE user_id = ?', (participant_2,))
                conn.execute('UPDATE user_profiles SET amount_of_pars = amount_of_pars + 1 WHERE user_id = ?', (participant_1,))
            bot.send_photo(participant_2,photo1, caption=f'Баттл против {name1}, {age1} завершился ничьей со счетом {votes2}-{votes1}')
            bot.send_photo(participant_1,photo2, caption=f'Баттл против {name2}, {age2} завершился ничьей со счетом {votes2}-{votes1}')
        
#создание умной клавиатуры под баттлом для голосования
def create_battle_vote_exit_markup(battle_id, left_name, right_name):
    markup = types.InlineKeyboardMarkup()
    markup.row(
        types.InlineKeyboardButton(f"{left_name}", callback_data=f"vote_left_{battle_id}"),
        types.InlineKeyboardButton(f"{right_name}", callback_data=f"vote_right_{battle_id}")
    )
    markup.row(types.InlineKeyboardButton("Выход", callback_data=f"exit_battle"))
    return markup

#Функция, чтобы очищать таблицу с голосами от голосов, относящихся к уже прошедшим баттлам
def clean_up_votes(battle_id):
    with conn:
        conn.execute('''
            DELETE FROM votes
            WHERE battle_id = ?
        ''', (battle_id,))
        conn.commit()

#------------------------------------------------------------------------------------------------------------------------------------------
#ФУНКЦИИ ДЛЯ ПЛАТЕЖЕЙ И ПОПОЛНЕНИЯ БАЛАНСА
#------------------------------------------------------------------------------------------------------------------------------------------

import json
import telebot

# Функция для обновления баланса в базе данных
def update_balance(user_id, amount):
    # print(user_id, amount)
    with conn:
        conn.execute('UPDATE user_profiles SET balance = balance + ? WHERE  user_id = ?',(amount, user_id,))
    pass

#по комманде pay предлагаем пользователю создать платеж 
@bot.message_handler(commands=['pay'])
def request_payment(message):
    if is_profile_verified(message.from_user.id):
        markup = types.InlineKeyboardMarkup()
        markup.row_width = 2
        markup.add(
            types.InlineKeyboardButton("100 рублей", callback_data="pay_100"),
            types.InlineKeyboardButton("500 рублей", callback_data="pay_500"),
            types.InlineKeyboardButton("1000 рублей", callback_data="pay_1000"),
            types.InlineKeyboardButton("5000 рублей", callback_data="pay_5000"),
            types.InlineKeyboardButton("20000 рублей", callback_data="pay_20000")
        )
        bot.send_message(message.chat.id, "Выберите сумму для пополнения:", reply_markup=markup)
    else:
        bot.send_message(message.chat.id, 'Сначала нужно подтвердить аккаунт! Чтобы это сделать, пропиши команду /verify')
    

#обрабатываем нажатие на кнопку (сколько пользователь хочет заплатить), создаем и отправляем платеж
@bot.callback_query_handler(func=lambda call: call.data.startswith('pay_'))
def handle_payment_choice(call):
    if call.from_user.id not in payloads_ids:
        amount = int(call.data.split('_')[1])
        invoice_payload = f"payment_{call.message.chat.id}_{amount}"
        prices = [types.LabeledPrice("Пополнение баланса", amount * 100)]
        provider_data = {
            "receipt": {
                "items": [
                    {
                        "description": "Пополнение баланса",
                        "quantity": "1.00",
                        "amount": {
                            "value": str(amount),
                            "currency": "RUB"
                        },
                        "vat_code": "1"
                    }
                ]
            }
        }
        invoice_message = bot.send_invoice(
            chat_id=call.message.chat.id,
            title="Пополнение баланса",
            description=f"Пополнение на {amount} рублей",
            invoice_payload=invoice_payload,
            provider_token=TELEGRAM_PROVIDER_TOKEN,
            currency="RUB",
            prices=prices,
            need_email=True,
            send_email_to_provider=True,
            provider_data=json.dumps(provider_data)  # Передача данных для фискализации
        )
        payloads_ids[call.from_user.id] = invoice_message.message_id
    else:
        markup_close = types.ReplyKeyboardMarkup(resize_keyboard=True)
        but_close = types.KeyboardButton("Закрыть")
        but_dont_close = types.KeyboardButton("Я оплачу открытый счет")
        markup_close.add(but_close, but_dont_close)
        bot.send_message(call.message.chat.id, f'Вы не можете создавать новые счета, пока не оплатите/закроете старые\nЧтобы закрыть неоплаченные счета - напишите одно сообщение "Закрыть"', reply_markup = markup_close)

@bot.pre_checkout_query_handler(lambda query: True)
def pre_checkout_query(pre_checkout_q: types.PreCheckoutQuery):
    # Извлекаем invoice_payload из запроса
    invoice_payload = pre_checkout_q.invoice_payload

    # Проверяем, есть ли пользователь в словаре payload_ids
    user_id = pre_checkout_q.from_user.id
    if user_id in payloads_ids:
        expected_payload = payloads_ids[user_id]

        # Разбираем payload, чтобы извлечь amount
        payload_parts = invoice_payload.split('_')
        if len(payload_parts) == 3 and payload_parts[0] == 'payment':
            bot.answer_pre_checkout_query(pre_checkout_q.id, ok=True)
            return
        else:
            bot.answer_pre_checkout_query(pre_checkout_q.id, ok=False, error_message="Ошибка: неверный формат payload. Обратитесь в поддержку")
            return
    else:
        bot.answer_pre_checkout_query(pre_checkout_q.id, ok=False, error_message="Ошибка: не найден соответствующий счет. Обратитесь в поддержку")

#когда пользователь оптатил какой-то счет, смотрим, на какую сумму этот счет был и пополняем его баланс 
@bot.message_handler(content_types=['successful_payment'])
def successful_payment(message):
    # Проверяем уникальный payload
    invoice_payload = message.successful_payment.invoice_payload
    payload_parts = invoice_payload.split('_')
    try:
        to_delete = payloads_ids[message.from_user.id]
    except KeyError:
        amount = int(payload_parts[2])
        update_balance(message.from_user.id, amount)
        bot.send_message(message.chat.id, f'Видимо, вы хотели пополнить чужой счет, но это так не работает\nТакие транзакции отследить сложнее, но возможно. Ваш баланс пополнен на {amount} рублей')
    if len(payload_parts) == 3 and payload_parts[0] == 'payment':
        amount = int(payload_parts[2])
        update_balance(message.from_user.id, amount)
        bot.delete_message(message.chat.id, to_delete)
        payloads_ids.pop(message.from_user.id, None)
        bot.send_message(message.chat.id,f"Оплата прошла успешно! Баланс пополнен на {amount} рублей",reply_markup=start_menu)
    else:
        bot.send_message(message.chat.id, "Ошибка: неверный инвойс.")


#------------------------------------------------------------------------------------------------------------------------------------------
#ФУНКЦИОНАЛ БОТА. IF MESSAGE.TEXT == X DO FUNC(1) ELSE DO FUNC(2)
#------------------------------------------------------------------------------------------------------------------------------------------
#отсюда начинается обработка разных команд/текста/нажатий кнопок ботом. Примерно все имеет вид if текст == x вызови функцию func1, иначе функцию func2.


#команда start
@bot.message_handler(commands=['start'])
def handle_start(message):
    referrer_id = message.text.split()[1] if len(message.text.split()) > 1 else None
    user_id = message.from_user.id
    if referrer_id and referrer_id.isdigit() and int(referrer_id) != user_id:
        add_referral(referrer_id=int(referrer_id), referred_id=user_id)
    elif referrer_id and referrer_id.isdigit() and int(referrer_id) == user_id:
        bot.send_message(user_id, "Нельзя переходить по своей же реферальной ссылке!")
    update_last_online(message)
    chat_id = message.chat.id
    markup = types.InlineKeyboardMarkup()
    btn = types.InlineKeyboardButton("Далее 👉",callback_data='next')
    markup.add(btn)
    bot.send_message(chat_id,f"Привет, {message.from_user.first_name}!\nДобро пожаловать в Twinkl - Сервис дорогих знакомств!\n\nЗнакомься по принципу <i>лайк с ценой - интерес с намерением</i>", reply_markup=markup, parse_mode='HTML')

#вторая часть команды start
@bot.callback_query_handler(func=lambda call: call.data == 'next')
def send(call):
    bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
    markup = types.InlineKeyboardMarkup()
    btn = types.InlineKeyboardButton('Принимаю!👌', callback_data= 'ready')
    markup.add(btn)
    bot.send_message(call.message.chat.id, f'❕Чтобы зарегистрироваться в боте, нужно подтвердить свою электронную почту\nНесмотря на обязательную верификацию, помните, что интернет - опасная среда, где люди могут выдавать себя за других\n\nПродолжая, вы принимаете [пользовательское соглашение](https://docs.google.com/document/d/e/2PACX-1vTIQFG3VuFD4XnyP9GDER9gYJJVew4dwDXvzxgurOn376VKE3KAUSh6U9-pRUHMwX9aygCapkC5iDKu/pub) и [политику конфиденциальности](https://docs.google.com/document/d/e/2PACX-1vRm9ZbciP3xHc0QniRrb_EijvhYW3Lm_2BfyOdvGIjQ1rPrUvBXybhiMaCsE-ac2QJVr685N4XwQ-af/pub)', reply_markup=markup, parse_mode='Markdown')
    
#третья часть команды start
@bot.callback_query_handler(func=lambda call: call.data == 'ready')
def send2(call):
    bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
    bot.send_message(call.message.chat.id, 'Для начала тебе нужно подтвердить свою почту\nЧтобы это сделать, пропиши команду /verify\n\nПоддержка 24/7 - @help_username_bot')

#команда verify - подтверждение по почте 
@bot.message_handler(commands=['verify'])
def verif(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    if get_status(user_id) == 'banned':
        bot.send_message(user_id, f'Вы были забанены. Чтобы обжаловать блокировку или купить разбан пишите @help_username_bot')
    else:
        if is_profile_verified(user_id):
            bot.send_message(chat_id,'Ваш профиль уже подтвержден', reply_markup=start_menu)
        else:
            user_states[user_id] = 'wait email'
            bot.send_message(chat_id,'Отправьте вашу почту')

#команда create_profile - создать анкету
@bot.message_handler(commands=['create_profile'])
def make_profile(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    if get_status(user_id) == 'banned':
        bot.send_message(user_id, f'Вы были забанены. Чтобы обжаловать блокировку или купить разбан пишите @help_username_bot')
    else:
        if is_profile_verified(user_id):
            with conn:
                conn.execute('''
                    DELETE FROM evaluations
                    WHERE evaluator_id = ? OR evaluated_id = ?
                ''', (user_id, user_id))
                conn.commit()
            with conn:
                conn.execute('''
                             DELETE FROM battle_queue WHERE user_id = ?
                             ''', (user_id,))
                conn.commit()
            with conn:
                result = conn.execute('SELECT user_id FROM user_profiles WHERE user_id = ?', (user_id,)).fetchone()
            if result is None:
                with conn:
                    conn.execute('''
                        INSERT INTO user_profiles (user_id) VALUES (?)
                    ''', (user_id,))
            bot.send_message(chat_id,'Мы рады, что вы решили создать анкету!\nДавайте начнем, как вас зовут?',reply_markup = types.ReplyKeyboardRemove())
            bot.register_next_step_handler(message, get_name, is_edit = False)
        else:
            bot.send_message(chat_id, 'Сначала нужно подтвердить аккаунт! Чтобы это сделать, пропиши команду /verify')

#обработка нажатия на инлайн кнопки во время голосования в баттле. голос за левого/правого, выход из баттлов. 
@bot.callback_query_handler(func=lambda call: call.data.startswith('vote_') or call.data == 'exit_battle')
def handle_vote_or_exit(call):
    chat_id = call.message.chat.id
    user_id = call.from_user.id
    if get_status(user_id) == 'banned':
        bot.send_message(user_id, f'Вы были забанены. Чтобы обжаловать блокировку или купить разбан пишите @help_username_bot')
    else:
        if is_profile_verified(user_id):
            bot.delete_message(chat_id, call.message.message_id)
            if call.data == 'exit_battle':
                bot.send_message(chat_id, "Вы вышли из баттлов.")
                return
            battle_id = int(call.data.split('_')[-1])
            vote_side = call.data.split('_')[1]
            with conn:
                existing_vote = conn.execute('''
                    SELECT vote_side FROM votes WHERE user_id = ? AND battle_id = ?
                ''', (user_id, battle_id)).fetchone()
                if existing_vote:
                    bot.send_message(chat_id, "Вы уже голосовали в этом баттле.")
                    return
                conn.execute('''
                    INSERT INTO votes (user_id, battle_id, vote_side) VALUES (?, ?, ?)
                ''', (user_id, battle_id, vote_side))
                if vote_side == 'left':
                    conn.execute('UPDATE battles SET votes_participant_1 = votes_participant_1 + 1 WHERE battle_id = ?', (battle_id,))
                else:
                    conn.execute('UPDATE battles SET votes_participant_2 = votes_participant_2 + 1 WHERE battle_id = ?', (battle_id,))
                conn.commit()
            show_next_battle(chat_id,user_id)
        else:
            bot.send_message(chat_id, 'Сначала нужно подтвердить аккаунт! Чтобы это сделать, пропиши команду /verify')

#обработка нажатий на inline клавиатуру под анкетой пользователя. ставим лайк/дизлайк/итд.
@bot.callback_query_handler(func=lambda call: call.data.startswith(('like_', 'dislike_', 'exit', 'report', 'message')))
def handle_evaluation(call):
    chat_id = call.message.chat.id
    user_id = call.from_user.id
    if get_status(user_id) == 'banned':
        bot.send_message(user_id, f'Вы были забанены. Чтобы обжаловать блокировку или купить разбан пишите @help_username_bot')
    else:
        if is_profile_verified(user_id):
            bot.edit_message_reply_markup(chat_id, call.message.message_id, reply_markup=None)
            with conn:
                user_gender = conn.execute('SELECT gender FROM user_profiles WHERE user_id = ?', (user_id,)).fetchone()
            user_gender = user_gender[0]
                # user_gender = int(user_gender)
            if call.data.startswith('like_'):
                match_id = int(call.data.split('_')[1])
                with conn:
                    match_gender = conn.execute('SELECT gender FROM user_profiles WHERE user_id = ?', (match_id,)).fetchone()
                match_gender = match_gender[0]
                    # match_gender = int(match_gender)
                if user_gender == 1 and match_gender == 2:
                    with conn: 
                        balance = conn.execute('SELECT balance FROM user_profiles WHERE user_id = ?', (user_id,)).fetchone()
                    balance = int(balance[0])
                    if balance >= 50:
                        bot.send_message(chat_id,f'Отправили лайк!\nБаланс: {balance - 50}', reply_markup=dating_menu)
                        with conn:
                            conn.execute('''UPDATE user_profiles SET balance = balance - 50 WHERE user_id = ?''', (user_id,))
                        give_like(chat_id, user_id, match_id, call.from_user.username)
                    else:
                        bot.send_message(chat_id, "Стоп! Недостаточно средств на балансе!\n\nНаш сервис разработан так, чтобы каждый лайк был осознанным и значимым. Мы уверены, что серьезные отношения начинаются с ответственности и четкого выбора. Платные лайки помогают вам более внимательно подходить к выбору партнерш, создавая условия для того, чтобы каждый шаг был продуманным и целенаправленным.\n\nПополните баланс и продолжайте знакомиться с теми, кто действительно вам интересен!\n\nЦена одного лайка - 50 рублей, казалось бы - совсем немного, но готовы ли вы тратить 50 рублей на каждую анкету?...\n\n👉Пополнить баланс можно по команде /pay", reply_markup=start_menu)
                        remove_match(user_id, match_id)
                else:
                    give_like(chat_id, user_id, match_id, call.from_user.username, (user_gender == 2 and match_gender == 1))
            elif call.data.startswith('message_'):
                match_id = int(call.data.split('_')[1])
                user_states[user_id] = f'wait message {match_id}'
                bot.send_message(user_id, "Напишите сообщение, которое хотели бы отправить пользователю вместе с лайком\n\nЕсли передумали отправлять сообщение - напишите в сообщение один символ - 0")
            elif call.data.startswith('dislike_'):
                # match_id = int(call.data.split('_')[1])
                # Просто переходим к следующей анкете
                find_matc(user_id,chat_id)
            elif call.data.startswith('exit_'):
                match_id = int(call.data.split('_')[1])
                remove_match(user_id, match_id)
                bot.send_message(chat_id, "Вы вышли из режима знакомств.",reply_markup=dating_menu)
            elif call.data.startswith('report_'):
                bot.send_message(user_id, f'Вы успешно отправили жалобу! Скоро мы ее рассмотрим.')
                match_id = int(call.data.split('_')[1])
                with conn:
                    result = conn.execute('''
                    SELECT name, photo, gender, bio, age 
                    FROM user_profiles 
                    WHERE user_id = ?
                    ''', (match_id,)).fetchone()
                name, photo, gender, bio, age = result
                bot.send_photo(671084247,photo,caption= f'Жалоба на {match_id}. Его анкета:\n\n{name}, {age}\n\n{bio}\n\nЧтобы его забанить, напишите боту ban match_id')
                bot.send_photo(7515729537,photo,caption= f'Жалоба на {match_id}. Его анкета:\n\n{name}, {age}\n\n{bio}\n\nЧтобы его забанить, напишите боту ban match_id')
                find_matc(user_id, chat_id)
        else:
            bot.send_message(chat_id, 'Сначала нужно подтвердить аккаунт! Чтобы это сделать, пропиши команду /verify')

#обработка нажатий на взаимный/невзаимный лайк (когда тебя лайкают - приходит уведомление с анкетой лайкнвушего и предложением дать обратную связь)
@bot.callback_query_handler(func=lambda call: call.data.startswith(('vzaim', 'nevzaim')))
def handle_evaluation(call):
    chat_id = call.message.chat.id
    user_id = call.from_user.id
    match_id = int(call.data.split(' ')[1])
    if call.data.startswith('vzaim'):
        with conn:
            user_gender = conn.execute('SELECT gender FROM user_profiles WHERE user_id = ?', (user_id,)).fetchone()
        user_gender = user_gender[0]
        with conn:
            match_gender = conn.execute('SELECT gender FROM user_profiles WHERE user_id = ?', (match_id,)).fetchone()
        match_gender = match_gender[0]
        if user_gender == 1 and match_gender == 2:
            with conn: 
                balance = conn.execute('SELECT balance FROM user_profiles WHERE user_id = ?', (user_id,)).fetchone()
            balance = int(balance[0])
            if balance >= 25:
                bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
                with conn:
                    conn.execute('''UPDATE user_profiles SET balance = balance - 25 WHERE user_id = ?''', (user_id,))
                    username = (call.data.split(" ")[2])
                bot.send_message(chat_id,f'Отправили взаимный лайк!\nЮзернейм девушки: @{username}\nБаланс: {balance - 25}', reply_markup=dating_menu)
                give_vzaim(user_id, match_id, call.from_user.username)
            else:
                bot.send_message(chat_id, f'💬 Взаимный лайк — шаг навстречу!\n\nВзаимный лайк стоит в 2 раза дешевле обычного. Мы сделали это специально, чтобы вы могли ответить взаимностью тем, кто действительно вам интересен, а не просто отвечать взаимностью всем подряд. Это делает каждый взаимный лайк более значимым.\n\nВсего лишь 25 рублей, но готовы ли вы отдать их любой?...\n\n👉Пополнить баланс можно по команде /pay', reply_markup=start_menu)
        else:
            bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
            bot.send_message(chat_id,f'Отправили взаимный лайк!', reply_markup=dating_menu)
            give_vzaim(user_id, match_id, call.from_user.username)
    else:
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
        with conn:
            conn.execute('''
                INSERT INTO evaluations (evaluator_id, evaluated_id) VALUES (?, ?)
            ''', (user_id, match_id))
            conn.commit()
        with conn:
            conn.execute('''
                INSERT INTO evaluations (evaluator_id, evaluated_id) VALUES (?, ?)
            ''', (match_id, user_id))
            conn.commit()

@bot.callback_query_handler(func=lambda call: call.data in ["reward_like", "reward_cash", "invite_more"])
def handle_reward_buttons(call):
    user_id = call.from_user.id
    cursor = conn.execute("SELECT referral_count FROM referral_rewards WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    referral_count = row[0] if row else 0

    if call.data == "reward_like":
        if referral_count >= 3:
            # Начисляем бесплатный лайк и уменьшаем количество рефералов
            conn.execute("UPDATE referral_rewards SET referral_count = referral_count - 3 WHERE user_id = ?", (user_id,))
            update_balance(user_id, 50)  # 50 рублей = стоимость одного лайка
            bot.send_message(user_id, "Вам начислен бесплатный лайк!")
        else:
            bot.send_message(user_id, "Недостаточно рефералов для этой награды.")
    elif call.data == "reward_cash":
        if referral_count >= 100:
            # Уменьшаем количество рефералов и отправляем уведомление админу
            conn.execute("UPDATE referral_rewards SET referral_count = referral_count - 100 WHERE user_id = ?", (user_id,))
            bot.send_message(user_id, "Вы выбрали 300₽. Администратор скоро свяжется с вами.")
            bot.send_message(ADMIN_CHAT_ID, f"Пользователь {user_id} запросил выплату 300₽.")
        else:
            bot.send_message(user_id, "Недостаточно рефералов для этой награды.")
    elif call.data == "invite_more":
        referral_link = f"https://t.me/{bot.get_me().username}?start={user_id}"
        bot.send_message(user_id, f"Приглашайте друзей по этой ссылке: {referral_link}")
                        
#обработка всех фоток, которые пользователь присылает. фото нам нужно только тогда, когда пользователь заполняет анкету, у него появляется особый статус в этот момент. в других случаях игнорируем
@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    if get_status(user_id) == 'banned':
        bot.send_message(user_id, f'Вы были забанены. Чтобы обжаловать блокировку или купить разбан пишите @help_username_bot')
    else:
        bot.send_message(chat_id, f'Зачем вы отправили фото?',reply_markup=start_menu)
            
#обработка всевозможных текстовых сообщений боту
@bot.message_handler(content_types=['text'])
def answer(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    is_profile_verified(user_id)
    update_last_online(message)
    if get_status(user_id) == 'banned':
        bot.send_message(user_id, f'Вы были забанены. Чтобы обжаловать блокировку или купить разбан пишите @help_username_bot')
    else:
        if user_id in user_states and user_states[user_id] == 'wait email':
            email = message.text
            if validate_email(email) and my_valid_email(email): 
                code = ''
                for i in range(6):
                    x = str(randint(0,9))
                    code += x
                with conn:
                    last_sent = conn.execute('SELECT last_email_send FROM user_profiles WHERE user_id = ?', (user_id,)).fetchone()
                if last_sent != (None,) and int(time.time()) - last_sent[0] < 60*2:
                    bot.send_message(user_id, 'Вы отправляете слишком много писем\nПожалуйста, напишите боту через 2 минуты (с момента отправки предыдущего кода)')
                    user_states[user_id] = 'wait email'
                else:
                    bot.send_message(chat_id, 'Вам на почту отправлен шестизначный код\nОтправьте мне его, чтобы подтвердить почту\n\nЕсли код не пришел - обязательно проверьте папку "Спам"!\n\nЕсли что-то не получается, поддержка 24/7 - @help_username_bot')
                    with conn:
                        conn.execute('UPDATE user_profiles SET last_email_send = ? WHERE user_id = ?', (int(time.time()), user_id,))
                    send_verification_email(email, code, user_id)
                    verif_codes[user_id] = code
                    user_states[user_id] = f'wait code {email}'
            else:
                bot.send_message(chat_id, 'Вы ввели некорректную почту. Введите почту в формате ivanov.i.i@edu.mirea.ru\n\nЕсли что-то не получается, поддержка 24/7 - @help_username_bot')
                user_states[user_id] = 'wait email'
        elif user_id in user_states and user_states[user_id].startswith('wait code'):
            code = message.text
            if code == verif_codes[user_id]:
                email = user_states[user_id].split()[2]
                with conn:
                    conn.execute('UPDATE user_profiles SET email = ? WHERE user_id = ?', (email, user_id,))
                bot.send_message(message.chat.id, "Почта подтверждена!\nПриятных знакомств 😉\n\nЧтобы создать анкету, пропишите /create_profile",reply_markup=start_menu)
                user_states[user_id] = ''
            else:
                bot.send_message(chat_id, f'Вы ввели неправильный код!\n\nОбычно код переадресовывается на вашу личную почту (mail.ru, gmail, итд), привязанную к личному кабинету МИРЭА. Обязательно проверьте папку "Спам"!\n\nЕсли что-то не получается, поддержка 24/7 - @help_username_bot')
                user_states[user_id] = 'wait email'
        if (is_profile_verified(user_id)):
            if user_id in user_states and user_states[user_id].startswith('wait message'):
                evaluator_username = message.from_user.username
                match_id = user_states[user_id].split()[2]
                user_states[user_id] = ''
                with conn:
                    user_gender = conn.execute('SELECT gender FROM user_profiles WHERE user_id = ?', (user_id,)).fetchone()
                    user_gender = user_gender[0]
                    match_gender = conn.execute('SELECT gender FROM user_profiles WHERE user_id = ?', (match_id,)).fetchone()
                    match_gender = match_gender[0]
                if message.text == "0":
                    user_states[user_id] = ''
                    remove_match(user_id, match_id)
                    find_matc(user_id, chat_id)
                else:
                    if (user_gender == 1 and match_gender == 2):
                        with conn:
                            balance = conn.execute('SELECT balance FROM user_profiles WHERE user_id = ?', (user_id,)).fetchone()
                        balance = int(balance[0])
                        if balance >= 50:
                            bot.send_message(chat_id,f'Отправили лайк с сообщением!\nБаланс: {balance - 50}', reply_markup=dating_menu)
                            with conn:
                                conn.execute('''UPDATE user_profiles SET balance = balance - 50 WHERE user_id = ?''', (user_id,))
                            give_like(chat_id, user_id, match_id, message.from_user.username, (user_gender == 2 and match_gender == 1), True, message.text)
                        else:
                            bot.send_message(chat_id, "Стоп! Недостаточно средств на балансе!\n\nНаш сервис разработан так, чтобы каждый лайк был осознанным и значимым. Мы уверены, что серьезные отношения начинаются с ответственности и четкого выбора. Платные лайки помогают вам более внимательно подходить к выбору партнерш, создавая условия для того, чтобы каждый шаг был продуманным и целенаправленным.\n\nПополните баланс и продолжайте знакомиться с теми, кто действительно вам интересен!\n\nЦена одного лайка - 50 рублей, казалось бы - совсем немного, но готовы ли вы тратить 50 рублей на каждую анкету?...\n\n👉Пополнить баланс можно по команде /pay", reply_markup=start_menu)
                            remove_match(user_id, match_id)
                    else:
                        give_like(chat_id, user_id, match_id, message.from_user.username, (user_gender == 2 and match_gender == 1), True, message.text)
            else:
                if message.text == 'Знакомства ❤️':
                    bot.send_message(chat_id, f"Вы в меню Знакомств", reply_markup=dating_menu)
                elif message.text == 'Баттл Фото 🔥':
                    check_for_completed_battles()
                    bot.send_message(chat_id,f'Вы в меню Фото-Баттлов',reply_markup=battle_menu)
                elif message.text == 'Назад':
                    bot.send_message(chat_id, f"Вы в главном меню\nВыберите раздел", reply_markup=start_menu)
                elif message.text == 'Моя Анкета':
                    flag = is_profile_exists(message)
                    if flag:
                        with conn:
                            result = conn.execute('''
                                SELECT name, photo, gender, bio, age, amount_of_wins, amount_of_pars, city, balance
                                FROM user_profiles 
                                WHERE user_id = ?
                                ''', (user_id,)).fetchone()
                        name, photo_data, gender, bio, age, am_wins, am_pars, city, balance = result
                        if photo_data:
                            bot.send_photo(message.chat.id, photo_data, caption = f'{name}, {age}, {city} - {bio}\n\nВаша статистика в Баттлах: {am_wins} побед из {am_pars} Баттлов\n\nВаш балланс: {balance} (Видно только вам)\n\nЧтобы пересоздать анкету, используйте команду /create_profile')
                elif message.text == 'Смотреть анкеты':
                    flag = is_profile_exists(message)
                    if flag:
                        find_matc(user_id,chat_id)
                elif message.text == 'К Анкете':
                    bot.send_message(chat_id, f'Вы в меню Знакомств!',reply_markup=dating_menu)
                #тут для батла фоток
                elif message.text == 'Мой Профиль':
                    flag = is_profile_exists(message)
                    if flag:
                        with conn:
                            result = conn.execute('''
                                SELECT name, photo, gender, age, amount_of_wins, amount_of_pars, city, balance
                                FROM user_profiles 
                                WHERE user_id = ?
                                ''', (user_id,)).fetchone()
                        name, photo_data, gender, age, am_wins, am_pars, city, balance = result
                        if photo_data:
                            bot.send_photo(message.chat.id, photo_data, caption = f'{name}, {age}, {city}\n\nВаша статистика в Баттлах: {am_wins} побед из {am_pars} Баттлов\n\nВаш баланс: {balance} (Видно только вам)\n\nЧтобы пересоздать анкету, используйте команду /create_profile')
                elif message.text == 'Активные Баттлы':
                    flag = is_profile_exists(message)
                    if flag:
                        show_next_battle(chat_id,user_id)
                elif message.text == 'Принять Участие':
                    join_battle(message)
                elif message.text == 'Топ 5 участников':
                    top_5_participants(message)
                elif message.text == 'Закрыть':
                    if user_id in payloads_ids:
                        bot.delete_message(chat_id, payloads_ids[user_id])
                        payloads_ids.pop(user_id, None)
                        bot.send_message(chat_id, "Неоплаченные платежи закрыты, можете создать новый\nКоманда /pay",reply_markup=start_menu)
                    else:
                        bot.send_message(chat_id, f'У вас нет активных неоплаченных платежей', reply_markup=start_menu)
                elif message.text == 'Я оплачу открытый счет':
                    bot.send_message(chat_id, f'Хорошо, ожидаем оплаты', reply_markup=start_menu, reply_to_message_id=payloads_ids[user_id])    
                elif message.text == 'Мои Баттлы':
                    clear_evaluations_if_needed()
                    if is_profile_exists(message):
                        my_battles(message)
                elif message.text == 'Настройки ⚙️':
                    bot.send_message(chat_id, "Вы в меню настроек. Выберите нужную опцию", reply_markup=markup_settings)
                elif message.text == "Изменить анкету":
                    if is_profile_exists(message):
                        bot.send_message(chat_id, "Выберите, что хотите изменить в своей анкете\n\nЧтобы пересоздать анкету, используйте команду /create_profile", reply_markup=markup_change_anket)
                elif message.text == "Изменить имя":
                    if is_profile_exists(message):
                        bot.send_message(chat_id, "Напишите новое имя",reply_markup=types.ReplyKeyboardRemove())
                        bot.register_next_step_handler(message, get_name, 1)
                elif message.text == "Изменить город":
                    if is_profile_exists(message):
                        bot.send_message(chat_id, "Напишите новый город",reply_markup=types.ReplyKeyboardRemove())
                        bot.register_next_step_handler(message, get_city, 1)
                elif message.text == "Изменить возраст":
                    if is_profile_exists(message):
                        bot.send_message(chat_id, "Напишите ваш возраст",reply_markup=types.ReplyKeyboardRemove())
                        bot.register_next_step_handler(message, get_age, 1)
                elif message.text == "Изменить предпочтения по возрасту":
                    if is_profile_exists(message):
                        bot.send_message(chat_id, "Напишите ваш возраст",reply_markup=types.ReplyKeyboardRemove())
                        bot.register_next_step_handler(message, get_pref_age, 1)
                elif message.text == "Изменить пол":
                    if is_profile_exists(message):
                        bot.send_message(chat_id, "Выберите ваш пол",reply_markup=types.ReplyKeyboardRemove())
                        bot.register_next_step_handler(message, get_gender, 1)
                elif message.text == "Изменить фото":
                    if is_profile_exists(message):
                        bot.send_message(chat_id, "Отправьте новое фото",reply_markup=types.ReplyKeyboardRemove())
                        bot.register_next_step_handler(message, get_photo, 1)
                elif message.text == "Реферальная система":
                    bot.send_message(user_id, f'Вы в меню реферальной системы', reply_markup = markup_referals)
                elif message.text == "🔗Реферальная ссылка":
                    referral_link = f"https://t.me/twinkl_datebot?start={user_id}"
                    bot.send_message(user_id, f"Ваша реферальная ссылка: {referral_link}", reply_markup=markup_referals)
                elif message.text == "🔢Количество рефералов":
                        all_amount = conn.execute("SELECT COUNT(*) FROM referrals WHERE user_id = ?", (user_id,))
                        all_amount = all_amount.fetchone()[0]
                        avaliable_amount = conn.execute("SELECT referral_count FROM referral_rewards WHERE user_id = ?", (user_id,)).fetchone()
                        avaliable_amount = avaliable_amount[0] if avaliable_amount else 0
                        bot.send_message(user_id, f"Всего рефералов: {all_amount}\nИз них доступно для обмена на награды: {avaliable_amount} ", reply_markup=markup_referals)
                elif message.text == "Пополнить баланс":
                    bot.send_message(chat_id, f'Чтобы пополнить баланс, воспользуйтесь командой /pay')
                elif message.text == "🏆Мои награды":
                    cursor = conn.execute("SELECT referral_count FROM referral_rewards WHERE user_id = ?", (user_id,))
                    row = cursor.fetchone()
                    referral_count = row[0] if row else 0
                    # Создаем меню наград
                    rewards_menu = types.InlineKeyboardMarkup()
                    rewards_text = f"У вас {referral_count} рефералов.\nДоступные награды:\n"
                    rewards_menu.add(types.InlineKeyboardButton("♥️Бесплатный лайк = 3 реф.", callback_data="reward_like"))
                    rewards_menu.add(types.InlineKeyboardButton("💸Получить 300₽ = 100 реф.", callback_data="reward_cash"))
                    rewards_menu.add(types.InlineKeyboardButton("➕Пригласить ещё", callback_data="invite_more"))
                    bot.send_message(user_id, rewards_text, reply_markup=rewards_menu)
                else:
                    if not(user_id in verif_codes and message.text == verif_codes[user_id]):
                        if user_id != 671084247 and user_id != 7515729537:
                            bot.send_message(chat_id, f'Неизвестная комманда.',reply_markup=start_menu)
                        else:
                            txt = message.text
                            if txt.startswith('ban '):
                                id_ban = txt.split()[1]
                                with conn:
                                    conn.execute('UPDATE user_profiles SET status_ban = ?, photo = ? WHERE user_id = ?', ('banned', None, id_ban))
                                bot.send_message(id_ban, f'Вы были забанены. Чтобы обжаловать блокировку или купить разбан пишите @help_username_bot')
                                bot.send_message(user_id, 'забанили')
                            elif txt.startswith('unban '):
                                id_ban = txt.split()[1]
                                with conn:
                                    conn.execute('UPDATE user_profiles SET status_ban = ? WHERE user_id = ?', ('norm', id_ban),)
                                bot.send_message(id_ban, f'Вы были разбанены. Впредь не нарушайте правила бота.')
                                bot.send_message(user_id,'разбанили')
                            elif txt.startswith('verif '):
                                id_verif, email_verif = txt.split()[1], txt.split()[2]
                                with conn:
                                    conn.execute('UPDATE user_profiles SET email = ? WHERE user_id = ?', (email_verif, id_verif),)
                                bot.send_message(user_id, 'верифицировали')
                                bot.send_message(id_verif, 'Теперь ваш аккаунт подтвержден! Хорошего пользования!',reply_markup=start_menu)
                                user_states[id_verif] = ''
                            elif txt == 'бд':
                                try:
                                    with open('usersDating.db', 'rb') as file:
                                        bot.send_document(user_id, file)
                                except Exception as e:
                                    bot.reply_to(message, f"Произошла ошибка при отправке файла: {e}")
                            elif txt.startswith('пополнить'):
                                id_popln = txt.split()[1]
                                am = txt.split()[2]
                                update_balance(id_popln, am)
                            else:
                                bot.send_message(chat_id, f'Неизвестная комманда.',reply_markup=start_menu)
                                
        else:
            if not(user_id in user_states and user_states[user_id].startswith('wait code')) and not(user_id in user_states and user_states[user_id] == 'wait email'):
                    bot.send_message(chat_id, 'Сначала нужно подтвердить почту. Это можно сделать с помощью команды /verify')
bot.polling(none_stop=True)
