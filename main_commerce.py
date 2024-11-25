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
bot = telebot.TeleBot('')

#define token for pay
TELEGRAM_PROVIDER_TOKEN = ""

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
