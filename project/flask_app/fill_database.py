import sqlite3

# Подключение к базе данных SQLite
db_file = r'C:\Users\kotonai\Downloads\project\database\db.sqlite3'
conn = sqlite3.connect(db_file)
cursor = conn.cursor()

# Функция для изменения роли пользователя на "администратор"
def set_admin_by_email():
    email = input("Введите email пользователя: ")  # Ввод email с консоли

    # Проверяем, существует ли пользователь с таким email
    cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
    user = cursor.fetchone()

    if not user:
        print(f"Пользователь с email {email} не найден.")
        return

    # Изменяем роль на 'admin'
    cursor.execute('UPDATE users SET role = ? WHERE email = ?', ('admin', email))
    conn.commit()
    print(f"Роль пользователя с email {email} успешно изменена на 'admin'.")

# Основная часть программы
if __name__ == "__main__":
    while True:
        print("\nМеню:")
        print("1. Добавить пользователя")
        print("2. Изменить роль на админа")
        print("3. Показать всех пользователей")
        print("4. Выйти")

        choice = input("Выберите действие: ")

        if choice == "1":
            email = input("Введите email нового пользователя: ")
            try:
                cursor.execute('INSERT INTO users (email) VALUES (?)', (email,))
                conn.commit()
                print(f"Пользователь {email} успешно добавлен.")
            except sqlite3.IntegrityError:
                print(f"Пользователь с email {email} уже существует.")
        elif choice == "2":
            set_admin_by_email()
        elif choice == "3":
            cursor.execute('SELECT * FROM users')
            users = cursor.fetchall()
            print("\nСписок пользователей:")
            for user in users:
                print(f"ID: {user[0]}, Email: {user[1]}, Role: {user[2]}")
        elif choice == "4":
            print("Выход из программы.")
            break
        else:
            print("Неверный выбор. Попробуйте снова.")

# Закрытие соединения с базой данных
conn.close()
