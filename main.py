import telebot
import sqlite3
from telebot import types
from threading import Thread
from datetime import datetime

# Создание бота и подключение к API
bot = telebot.TeleBot('6793241518:AAHpaOlIMXZUfSu2AO8dc5n7W5gIPSXwMGE')

# Подключение к базе данных
conn = sqlite3.connect('comments.db')
cursor = conn.cursor()

# Создание таблицы "comments"
cursor.execute('''
    CREATE TABLE IF NOT EXISTS comments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        comment TEXT NOT NULL
    )
''')

# Сохранение изменений и закрытие подключения
conn.commit()
cursor.close()
conn.close()

# Обработчик команды /start
@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "📓 Привет! Присылайте мне юзернеймы для получения информации. Мой создатель - @equinoxcoder")

# Обработчик сообщений с юзернеймами и кнопкой "Комментарии пользователя"
@bot.message_handler(func=lambda message: message.text.startswith('@'))
def get_user_info(message):
    username = message.text[1:]

    # Получение информации о пользователе
    user_id = message.from_user.id
    last_visit = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    comments_count = get_comments_count(username)

    # Создание сообщения с информацией и кнопками
    user_info = f"📓 Информация о юзере @{username}:\n"
    user_info += f"⚙️ ID: {user_id}\n"
    user_info += f"✉️ Количество комментариев: {comments_count}\n"

    markup = types.InlineKeyboardMarkup()
    comments_button = types.InlineKeyboardButton('Комментарии пользователя', callback_data=f'comments_{username}')
    add_comment_button = types.InlineKeyboardButton('Добавить комментарий', callback_data=f'add_{username}')
    markup.row(comments_button)
    markup.row(add_comment_button)
    
    bot.send_message(message.chat.id, user_info, reply_markup=markup, reply_to_message_id=message.message_id)

# Обработчик нажатий кнопок "Комментарии пользователя" и "Добавить комментарий"
@bot.callback_query_handler(func=lambda call: call.data.startswith(('comments_', 'add_')))
def handle_comments_add(call):
    command, username = call.data.split('_')
    
    if command == 'comments':
        # Отправка комментариев пользователя
        comments = get_user_comments(username)
        if comments:
            for comment in comments:
                bot.send_message(call.message.chat.id, f"Комментарий : {comment}")
        else:
            bot.send_message(call.message.chat.id, "У пользователя нет комментариев.")
    
    if command == 'add':
        # Проверка, что пользователь пытается оставить комментарий другому пользователю
        if call.from_user.username != username:
            # Запрос комментария у пользователя
            bot.send_message(call.message.chat.id, "Введите комментарий:")
            bot.register_next_step_handler(call.message, save_comment, username)
        else:
            bot.send_message(call.message.chat.id, "Вы не можете оставить комментарий самому себе.")

# Функция для сохранения комментария в базе данных
def save_comment(message, username):
    comment = message.text
    # Сохранение комментария в базе данных
    save_user_comment(username, comment)
    bot.send_message(message.chat.id, "Комментарий успешно добавлен.")

# Функция для получения комментариев пользователя из базы данных
def get_user_comments(username):
    conn = sqlite3.connect('comments.db')
    cursor = conn.cursor()
    cursor.execute("SELECT comment FROM comments WHERE username = ?", (username,))
    comments = cursor.fetchall()
    cursor.close()
    conn.close()
    return [comment[0] for comment in comments] if comments else []

# Функция для получения количества комментариев пользователя
def get_comments_count(username):
    conn = sqlite3.connect('comments.db')
    cursor = conn.cursor()
    cursor.execute("SELECT count(*) FROM comments WHERE username = ?", (username,))
    count = cursor.fetchone()[0]
    cursor.close()
    conn.close()
    return count

# Функция для сохранения комментария в базе данных
def save_user_comment(username, comment):
    conn = sqlite3.connect('comments.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO comments (username, comment) VALUES (?, ?)", (username, comment))
    conn.commit()
    cursor.close()
    conn.close()

# Запуск бота в отдельном потоке
def bot_polling():
    bot.polling(none_stop=True)

# Запуск потока для бота
bot_thread = Thread(target=bot_polling)
bot_thread.start()