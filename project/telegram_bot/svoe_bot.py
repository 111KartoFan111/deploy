import os
import sqlite3
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext, ConversationHandler

# Установите путь к базе данных с учетом местоположения скрипта
DB_FILE = os.path.join(os.path.dirname(__file__), '..', 'database', 'db.sqlite3')

# Этапы для добавления новости и выбора новости для редактирования/удаления
TITLE, CONTENT, EDIT_ID, DELETE_ID = range(4)

# Функция для подключения к базе данных
def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row  # Получать строки как словари
    return conn

# Команда /start
async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text("Здравствуйте! Используйте команды:\n/applications, /news, /add_news, /edit_news, /delete_news.")

# Команда /applications — показывает все заявки
async def applications(update: Update, context: CallbackContext) -> None:
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, name, phone, comment, processed FROM applications")
    applications = cur.fetchall()
    conn.close()

    message = "Заявки:\n\n"
    for app in applications:
        message += f"ID: {app['id']}, Имя: {app['name']}, Телефон: {app['phone']}, Комментарий: {app['comment']}, Обработано: {app['processed']}\n"

    await update.message.reply_text(message)

# Команда /news — показывает все новости
async def news(update: Update, context: CallbackContext) -> None:
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, title, content, date FROM news ORDER BY date DESC")
    news_items = cur.fetchall()
    conn.close()

    message = "Новости:\n\n"
    for news_item in news_items:
        message += f"ID: {news_item['id']}, Заголовок: {news_item['title']}, Дата: {news_item['date']}\n{news_item['content']}\n\n"

    await update.message.reply_text(message)

# Начало процесса добавления новости
async def add_news_start(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text("Пожалуйста, введите заголовок новости.")
    return TITLE

# Получение заголовка новости
async def get_title(update: Update, context: CallbackContext) -> int:
    context.user_data['title'] = update.message.text  # Сохраняем заголовок
    await update.message.reply_text("Теперь введите текст новости.")
    return CONTENT

# Получение текста новости и сохранение новости в базе данных
async def get_content(update: Update, context: CallbackContext) -> int:
    title = context.user_data['title']
    content = update.message.text

    # Добавление новости в базу данных
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO news (title, content) VALUES (?, ?)", (title, content))
    conn.commit()
    conn.close()

    await update.message.reply_text(f"Новость добавлена!\nЗаголовок: {title}\nТекст: {content}")
    return ConversationHandler.END

# Команда /edit_news — редактирование новости
async def edit_news_start(update: Update, context: CallbackContext) -> int:
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, title FROM news ORDER BY date DESC")
    news_items = cur.fetchall()
    conn.close()

    if not news_items:
        await update.message.reply_text("Нет новостей для редактирования.")
        return ConversationHandler.END

    message = "Выберите новость для редактирования:\n\n"
    for news_item in news_items:
        message += f"ID: {news_item['id']}, Заголовок: {news_item['title']}\n"

    await update.message.reply_text(message)
    return EDIT_ID

# Получение ID новости для редактирования
async def get_news_id_for_edit(update: Update, context: CallbackContext) -> int:
    try:
        news_id = int(update.message.text)  # Преобразуем в ID
        context.user_data['edit_id'] = news_id  # Сохраняем ID новости
        await update.message.reply_text("Теперь введите новый текст новости.")
        return CONTENT
    except ValueError:
        await update.message.reply_text("Пожалуйста, введите корректный ID новости.")
        return EDIT_ID

# Обработка нового текста новости и обновление в базе данных
async def edit_news_content(update: Update, context: CallbackContext) -> int:
    news_id = context.user_data['edit_id']
    new_content = update.message.text

    # Редактирование новости в базе данных
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("UPDATE news SET content = ? WHERE id = ?", (new_content, news_id))
    conn.commit()
    conn.close()

    await update.message.reply_text(f"Новость с ID {news_id} успешно отредактирована.")
    return ConversationHandler.END

# Команда /delete_news — удаление новости
async def delete_news(update: Update, context: CallbackContext) -> int:
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, title FROM news ORDER BY date DESC")
    news_items = cur.fetchall()
    conn.close()

    if not news_items:
        await update.message.reply_text("Нет новостей для удаления.")
        return ConversationHandler.END

    message = "Выберите новость для удаления:\n\n"
    for news_item in news_items:
        message += f"ID: {news_item['id']}, Заголовок: {news_item['title']}\n"

    await update.message.reply_text(message)
    return DELETE_ID

# Получение ID новости для удаления
async def get_news_id_for_delete(update: Update, context: CallbackContext) -> None:
    try:
        news_id = int(update.message.text)  # Преобразуем в ID
        # Удаление новости из базы данных
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM news WHERE id = ?", (news_id,))
        conn.commit()
        conn.close()

        await update.message.reply_text(f"Новость с ID {news_id} успешно удалена.")
    except ValueError:
        await update.message.reply_text("Пожалуйста, введите корректный ID новости.")

# Обработчик для отмены процесса
async def cancel(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text("Процесс отменен.")
    return ConversationHandler.END

# Главная функция, запускающая бота
def main():
    application = Application.builder().token('7914597565:AAF8fSKolDiY_QlJs3sEoovYWxUAzJnIn-U').build()

    # Настройка ConversationHandler для добавления новости
    add_news_handler = ConversationHandler(
        entry_points=[CommandHandler('add_news', add_news_start)],
        states={
            TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_title)],
            CONTENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_content)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    # Настройка ConversationHandler для редактирования новости
    edit_news_handler = ConversationHandler(
        entry_points=[CommandHandler('edit_news', edit_news_start)],
        states={
            EDIT_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_news_id_for_edit)],
            CONTENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_news_content)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    # Настройка ConversationHandler для удаления новости
    delete_news_handler = ConversationHandler(
        entry_points=[CommandHandler('delete_news', delete_news)],
        states={
            DELETE_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_news_id_for_delete)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    # Регистрация обработчиков команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(add_news_handler)
    application.add_handler(edit_news_handler)
    application.add_handler(delete_news_handler)
    application.add_handler(CommandHandler("applications", applications))
    application.add_handler(CommandHandler("news", news))

    application.run_polling()

if __name__ == '__main__':
    main()