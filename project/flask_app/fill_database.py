import sqlite3

# Путь к вашей базе данных
db_path = r'C:\Users\kotonai\Downloads\project\database\db.sqlite3'

# Подключение к базе данных
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row  # Устанавливаем формат строк как словарь
cur = conn.cursor()

# Выполняем запрос
cur.execute('''ALTER TABLE subscriptions ADD COLUMN final_price REAL;
ALTER TABLE subscriptions ADD COLUMN sale REAL;

''')
rows = cur.fetchall()

# Закрываем соединение
conn.close()
