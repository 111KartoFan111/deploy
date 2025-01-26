import sqlite3

# Путь к вашей базе данных
db_path = r'../database/db.sqlite3'

# Подключение к базе данных
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute('''CREATE TABLE subscriptions (
                subscription_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                service_id INTEGER NOT NULL,
                price_id INTEGER NOT NULL,
                start_date DATE NOT NULL,
                end_date DATE NOT NULL,
                period INTEGER NOT NULL,
                receipt_path TEXT,
                FOREIGN KEY (service_id) REFERENCES services(id),
                FOREIGN KEY (user_id) REFERENCES users(user_id),
                FOREIGN KEY (price_id) REFERENCES prices(id)
            )''')

conn.commit()

conn.close()
