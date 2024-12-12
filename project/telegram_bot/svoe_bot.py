from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
import sqlite3

# Установите подключение к базе данных
DB_FILE = '../database/app.db'

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

# Пароль для администратора
ADMIN_PASSWORD = "2222"  # Замените на реальный пароль администратора

# Глобальная переменная для отслеживания статуса авторизации пользователя
authorized_users = {}
# Глобальная переменная для отслеживания состояния ввода новостей
news_input_state = {}

# Обработчик команды /start
async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text("Здравствуйте! Пожалуйста, введите пароль для авторизации.")

# Обработчик пароля
async def password_handler(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id

    # Проверка, находится ли пользователь в процессе ввода новости
    if user_id in news_input_state:
        await text_handler(update, context)
        return

    password = update.message.text.strip()
    if password == ADMIN_PASSWORD:
        authorized_users[user_id] = True
        await update.message.reply_text("Вы авторизованы как администратор. Теперь используйте команды /applications или /news.")
    else:
        await update.message.reply_text("Неверный пароль. Попробуйте снова.")

# Обработчик команды /applications — показывает все заявки
async def applications(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id

    # Проверка, авторизован ли пользователь
    if user_id not in authorized_users or not authorized_users[user_id]:
        await update.message.reply_text("Для доступа к этой команде вам нужно ввести пароль администратора.")
        return

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, name, phone, comment, processed FROM applications")
    applications = cur.fetchall()
    conn.close()

    # Формирование списка заявок
    message = "Заявки:\n\n"
    for app in applications:
        message += f"ID: {app['id']}, Имя: {app['name']}, Телефон: {app['phone']}, Комментарий: {app['comment']}, Обработано: {app['processed']}\n"

    await update.message.reply_text(message)

# Обработчик команды /news — показывает все новости
async def news(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id

    # Проверка, авторизован ли пользователь
    if user_id not in authorized_users or not authorized_users[user_id]:
        await update.message.reply_text("Для доступа к этой команде вам нужно ввести пароль администратора.")
        return

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, title, content, date FROM news ORDER BY date DESC")
    news_items = cur.fetchall()
    conn.close()

    # Формирование списка новостей
    message = "Новости:\n\n"
    for news_item in news_items:
        message += f"ID: {news_item['id']}, Заголовок: {news_item['title']}, Дата: {news_item['date']}\n{news_item['content']}\n\n"

    await update.message.reply_text(message)

# Обработчик команды /add_news — начало ввода новости
async def add_news(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id

    # Проверка, авторизован ли пользователь
    if user_id not in authorized_users or not authorized_users[user_id]:
        await update.message.reply_text("Для доступа к этой команде вам нужно ввести пароль администратора.")
        return

    # Установка состояния ввода заголовка
    news_input_state[user_id] = {'step': 'title', 'title': '', 'content': ''}
    await update.message.reply_text("Введите заголовок новости (многострочный ввод). Когда закончите, отправьте \"/done\".")

# Обработчик текстовых сообщений для многострочного ввода
async def text_handler(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id

    # Проверка, находится ли пользователь в процессе ввода новости
    if user_id in news_input_state:
        state = news_input_state[user_id]

        if state['step'] == 'title':
            # Добавление строки в заголовок
            state['title'] += update.message.text + '\n'
        elif state['step'] == 'content':
            # Добавление строки в основной текст
            state['content'] += update.message.text + '\n'

        await update.message.reply_text("Текст добавлен. Если завершили ввод, отправьте \"/done\".")

# Обработчик команды /done — завершение ввода текущего этапа
async def done(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id

    # Проверка, находится ли пользователь в процессе ввода новости
    if user_id in news_input_state:
        state = news_input_state[user_id]

        if state['step'] == 'title':
            # Завершение ввода заголовка
            state['step'] = 'content'
            await update.message.reply_text("Заголовок сохранен. Теперь введите текст новости (многострочный ввод). Когда закончите, отправьте \"/done\".")
        elif state['step'] == 'content':
            # Завершение ввода текста новости
            title = state['title'].strip()
            content = state['content'].strip()

            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO news (title, content, date)
                VALUES (?, ?, datetime('now'))
                """,
                (title, content)
            )
            conn.commit()
            conn.close()

            del news_input_state[user_id]  # Очистка состояния ввода

            await update.message.reply_text(f"Новость успешно добавлена!\n\nЗаголовок:\n{title}\n\nТекст:\n{content}")

# Главная функция, вызываемая
def main():
    application = Application.builder().token('7705461504:AAHNbj_cY44V10LQS9LXWdNgw3wLBQ1qr2U').build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, password_handler))
    application.add_handler(CommandHandler("applications", applications))
    application.add_handler(CommandHandler("news", news))
    application.add_handler(CommandHandler("add_news", add_news))
    application.add_handler(CommandHandler("done", done))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
    application.run_polling()

if __name__ == '__main__':
    main()