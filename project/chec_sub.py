import sqlite3
from datetime import datetime, timedelta

# Функция для проверки подписок и отправки уведомлений
def check_and_notify_subscriptions():
    # Подключаемся к базе данных
    conn = sqlite3.connect('your_database.db')
    cursor = conn.cursor()

    # Получаем текущую дату и дату через 3 дня
    today = datetime.today().date()
    three_days_later = today + timedelta(days=3)

    # Выполняем SQL-запрос для поиска подписок, которые заканчиваются через 3 дня
    cursor.execute("""
        SELECT s.subscription_id, s.user_id, u.username, s.end_date, srv.name
        FROM subscriptions s
        JOIN users u ON s.user_id = u.user_id
        JOIN services srv ON s.service_id = srv.id
        WHERE s.end_date = ?
    """, (three_days_later,))

    subscriptions_to_notify = cursor.fetchall()

    # Проверяем каждую подписку
    for subscription in subscriptions_to_notify:
        subscription_id, user_id, username, end_date, service_name = subscription

        # Сообщение для уведомления
        message = f"Ваша подписка на сервис {service_name} заканчивается через 3 дня. Пожалуйста, продлите её."

        # Записываем уведомление в таблицу notifications
        cursor.execute("""
            INSERT INTO notifications (user_id, subscription_id, message)
            VALUES (?, ?, ?)
        """, (user_id, subscription_id, message))

        # Выводим сообщение на консоль (или используем другой механизм уведомлений)
        print(f"Уведомление отправлено пользователю {username} ({user_id}) о подписке {service_name}.")

    # Сохраняем изменения и закрываем соединение
    conn.commit()
    conn.close()

# Функция для запуска проверки и уведомлений
if __name__ == '__main__':
    check_and_notify_subscriptions()