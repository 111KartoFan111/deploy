import sqlite3

# Укажите путь к вашей базе данных
DB_PATH = r'../database/db.sqlite3'

def assign_admin(full_name):
    try:
        # Подключение к базе данных
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()

        # Поиск пользователя по полному имени
        cur.execute('SELECT user_id, full_name, email, role FROM users WHERE full_name = ?', (full_name,))
        user = cur.fetchone()

        if not user:
            print(f"Пользователь с именем '{full_name}' не найден.")
            return

        print(f"Пользователь найден: ID={user[0]}, Имя={user[1]}, Email={user[2]}, Текущая роль={user[3]}")

        # Назначение роли администратора
        cur.execute('UPDATE users SET role = ? WHERE full_name = ?', ('admin', full_name))
        conn.commit()

        # Проверка изменений
        cur.execute('SELECT user_id, full_name, email, role FROM users WHERE full_name = ?', (full_name,))
        updated_user = cur.fetchone()
        print(f"Роль успешно обновлена: ID={updated_user[0]}, Имя={updated_user[1]}, Email={updated_user[2]}, Новая роль={updated_user[3]}")

    except sqlite3.Error as e:
        print(f"Ошибка базы данных: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    # Запрашиваем полное имя пользователя у администратора
    full_name = input("Введите полное имя пользователя, которому нужно назначить роль администратора: ")
    assign_admin(full_name)
