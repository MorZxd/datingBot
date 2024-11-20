import json
import sqlite3
import telebot
from telebot import types

# Инициализация бота
BOT_TOKEN = "7745700166:AAEk4ENGSMH6EVofznsBqkKAU2MuGu5T7iw"
bot = telebot.TeleBot(BOT_TOKEN)

# Администраторский ID
ADMIN_CHAT_ID = 6670128924 #Катя доп аккаунт 

# Подключение к базе данных
conn = sqlite3.connect("referral_bot.db", check_same_thread=False)

# Инициализация базы данных
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

# Функция добавления реферала
def add_referral(referrer_id, referred_id):
    with conn:
        cursor = conn.execute("""
            SELECT COUNT(*) FROM referrals WHERE user_id = ? AND referred_user_id = ?
        """, (referrer_id, referred_id))
        if cursor.fetchone()[0] > 0:
            return
        conn.execute("INSERT INTO referrals (user_id, referred_user_id) VALUES (?, ?)", (referrer_id, referred_id))
        conn.execute("""
            INSERT INTO referral_rewards (user_id, referral_count)
            VALUES (?, 1)
            ON CONFLICT(user_id) DO UPDATE SET referral_count = referral_count + 1
        """, (referrer_id,))


# Функция для обновления баланса в базе данных
def update_balance(user_id, amount):
    pass

# Главное меню с кнопками
def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🔗Реферальная ссылка", "🔢Количество рефералов")
    markup.add("🏆Мои награды", "📢Помощь")
    return markup

# Стартовая команда
@bot.message_handler(commands=['start'])
def start_command(message):
    referrer_id = message.text.split()[1] if len(message.text.split()) > 1 else None
    user_id = message.from_user.id

    # Если пользователь пришел по реферальной ссылке
    if referrer_id and referrer_id.isdigit() and int(referrer_id) != user_id:
        add_referral(referrer_id=int(referrer_id), referred_id=user_id)
        bot.send_message(user_id, "Вы зарегистрированы по реферальной ссылке!")
        bot.send_message(referrer_id, f"К вам присоединился новый реферал!")

    # Отправляем главное меню
    bot.send_message(user_id, "Добро пожаловать! Выберите действие:", reply_markup=main_menu())

# Обработка кнопки "Мои награды"
@bot.message_handler(func=lambda message: message.text == "🏆Мои награды")
def handle_rewards(message):
    user_id = message.from_user.id

    # Получаем количество рефералов
    cursor = conn.execute("SELECT referral_count FROM referral_rewards WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    referral_count = row[0] if row else 0

    # Создаем меню наград
    rewards_menu = types.InlineKeyboardMarkup()
    rewards_text = f"У вас {referral_count} рефералов.\nДоступные награды:\n"
    rewards_menu.add(types.InlineKeyboardButton("♥️Получить лайк", callback_data="reward_like"))
    rewards_menu.add(types.InlineKeyboardButton("💸Получить 300₽", callback_data="reward_cash"))
    rewards_menu.add(types.InlineKeyboardButton("➕Пригласить ещё", callback_data="invite_more"))
    bot.send_message(user_id, rewards_text, reply_markup=rewards_menu)

# Обработка нажатий на кнопки наград
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

# Обработка других кнопок
@bot.message_handler(func=lambda message: message.text == "🔗Реферальная ссылка")
def handle_referral_link(message):
    user_id = message.from_user.id
    referral_link = f"https://t.me/twinkl_datebot?start={user_id}"
    bot.send_message(user_id, f"Ваша реферальная ссылка: {referral_link}")

@bot.message_handler(func=lambda message: message.text == "🔢Количество рефералов")
def handle_referral_count(message):
    user_id = message.from_user.id
    cursor = conn.execute("SELECT COUNT(*) FROM referrals WHERE user_id = ?", (user_id,))
    count = cursor.fetchone()[0]
    bot.send_message(user_id, f"У вас {count} рефералов.")

@bot.message_handler(func=lambda message: message.text == "📢Помощь")
def handle_help(message):
    bot.send_message(message.chat.id, "Вот что умеет бот:\n"
                                  "- 🔗Реферальная ссылка: получить вашу уникальную ссылку.\n"
                                  "- 🔢Количество рефералов: узнать, сколько человек вы пригласили.\n"
                                  "- 🏆Мои награды: посмотреть ваши текущие награды.\n"
                                  "               ‼️ВНИМАНИЕ‼️\n"
                                  "При получении награды количество ваших рефералов обновляется")

# Запуск бота
bot.polling()
