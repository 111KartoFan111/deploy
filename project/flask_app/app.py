from flask import Flask, request, render_template, redirect, url_for
from flask_login import LoginManager
import sqlite3
from flask_login import UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf.csrf import CSRFProtect
from flask import jsonify
from datetime import datetime, timedelta
import os
import traceback

app = Flask(__name__)
app.config['SECRET_KEY'] = '#\xcbK\x8f\xa1,\x8b\x85H\x9b\xdd\xa2\xd9:\xcf2\xb3>\x15\xce\x12aBS\xff\xe4\xb0|\xa9x\xdeR'

# Настраиваем LoginManager
login_manager = LoginManager(app)
login_manager.init_app(app)

# Настраиваем папку для загрузки
UPLOAD_FOLDER = r'C:\Users\kotonai\Downloads\project\database\file'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Класс пользователя
class User(UserMixin):
    def __init__(self, user_id, username, role, email,phone):
        self.id = user_id
        self.username = username
        self.role = role
        self.email = email
        self.phone = phone

# Загрузка пользователя
@login_manager.user_loader
def load_user(user_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT user_id, full_name,email,user_phone, role FROM users WHERE user_id = ?', (user_id,))
    user = cur.fetchone()
    conn.close()
    if user:
        return User(user_id=user['user_id'], username=user['full_name'], role=user['role'], email=user['email'],phone=user['user_phone'])
    return None

# Конфигурация базы данных
def get_db_connection():
    conn = sqlite3.connect(r'C:\Users\kotonai\Downloads\project\database\db.sqlite3')
    conn.row_factory = sqlite3.Row  # Для доступа к данным по имени столбца
    return conn


# Инициализация базы данных
def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    # Таблица пользователей
    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name VARCHAR(255) NOT NULL,
            email VARCHAR(255) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL,
            role VARCHAR(255) NOT NULL,
            user_phone VARCHAR(255) NOT NULL
        );
    ''')
    # Создание таблицы user_links
    cur.execute('''
        CREATE TABLE IF NOT EXISTS user_links (
            link_id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(user_id),
            link TEXT NOT NULL,
            app_name VARCHAR(255)
        );
    ''')
    # Создание таблицы subscriptions с receipt_path
    cur.execute('''
        CREATE TABLE IF NOT EXISTS subscriptions (
            subscription_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            service_id INTEGER NOT NULL,
            start_date DATE NOT NULL,
            end_date DATE NOT NULL,
            receipt_path TEXT,
            FOREIGN KEY (service_id) REFERENCES services(id),
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        );
    ''')

    # Создание таблицы notifications
    cur.execute('''
        CREATE TABLE IF NOT EXISTS notifications (
            notification_id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(user_id),
            subscription_id INTEGER REFERENCES subscriptions(subscription_id),
            sent_at TIMESTAMP,
            message TEXT
        );
    ''')
    cur.execute('''
    CREATE TABLE IF NOT EXISTS services (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT,
        base_price NUMERIC(10, 2) NOT NULL
    );
    ''')

    cur.execute('''
        CREATE TABLE IF NOT EXISTS prices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            service_id INTEGER NOT NULL,
            price_type TEXT NOT NULL,
            price NUMERIC(10, 2) NOT NULL,
            duration INTEGER,
            FOREIGN KEY (service_id) REFERENCES services(id)
        );
    ''')

    # Создание таблицы applications
    cur.execute('''
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            comment TEXT,
            processed BOOLEAN DEFAULT FALSE,
            admin_comment TEXT
        );
    ''')
    # Создание таблицы news
    cur.execute('''
        CREATE TABLE IF NOT EXISTS news (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    ''')
    conn.commit()
    conn.close()


# Главная страница
@app.route('/')
def home():
    conn = get_db_connection()
    cur = conn.cursor()
    # Извлекаем только последние 2 новости
    cur.execute('SELECT title, date, content FROM news ORDER BY date DESC LIMIT 2;')
    data = cur.fetchall()
    conn.close()
    return render_template('index.html', data=data)

# Форма отправки заявки
@app.route('/submit_application', methods=['POST'])
def submit_application():
    name = request.form['name']
    phone = request.form['phone']
    comment = request.form['comment']

    # Сохраняем заявку в базе
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO applications (name, phone, comment, processed)
        VALUES (?, ?, ?, ?)
        """, (name, phone, comment, False))  # по умолчанию заявка не обработана
    conn.commit()
    conn.close()

    return redirect('/')

@app.route('/login', methods=['POST'])
def login():
    email = request.form['email']
    password = request.form['password']
    # Проверка данных в базе
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT user_id, full_name, email,user_phone, password, role FROM users WHERE email = ?', (email,))
    user = cur.fetchone()
    conn.close()

    if user and check_password_hash(user['password'], password):
        # Создание объекта пользователя и вход в систему
        login_user(User(user_id=user['user_id'], username=user['full_name'], role=user['role'], email=user['email'],phone=user['user_phone']))
        # Перенаправление в зависимости от роли
        if user['role'] == 'admin':
            return redirect('/admin')
        elif user['role'] == 'user':
            return redirect('/profile')
    else:
        # Возврат на главную страницу при неудачной аутентификации
        return redirect('/')

# Маршрут для обработки формы регистрации
@app.route('/register', methods=['POST'])
def register():
    name = request.form['name']
    email = request.form['email']
    password = request.form['password']
    phone = request.form['phone']
    confirm_password = request.form['confirm_password']

    if password != confirm_password:
        return redirect('/')

    hashed_password = generate_password_hash(password)

    # Сохранение пользователя в базе данных
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO users (full_name, email, password ,user_phone, role)
            VALUES (?, ?, ?, ?, ?)
        """, (name, email , hashed_password,phone, 'user'))
        conn.commit()
    finally:
        conn.close()
    return redirect('/')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/')


@app.route('/dogovor')
def dogovor():
    return render_template('dogovor.html')

# Новости
@app.route('/news')
def news():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT title, date, content FROM news ORDER BY date DESC;')
    data = cur.fetchall()
    conn.close()
    return render_template('news.html', data=data)

# О нас
@app.route('/about')
def about():
    return render_template('about.html')

# Прайс
@app.route('/price')
def price():
    return render_template('price.html')

def calculate_end_date(duration):
    if duration:
        return (datetime.now() + timedelta(days=duration * 30)).strftime('%Y-%m-%d')
    return None

@app.route('/admin', methods=['GET', 'POST'])
@login_required  # Requires login
def admin_page():
    conn = get_db_connection()
    cur = conn.cursor()

    # Ограничение доступа для не-администраторов
    if current_user.role != 'admin':
        return redirect('/')

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'add_news':
            title = request.form['title']
            content = request.form['content']
            cur.execute('INSERT INTO news (title, content) VALUES (?, ?)', (title, content))
            conn.commit()

        elif action == 'edit_news':
            news_id = request.form['news_id']
            title = request.form['title']
            content = request.form['content']
            cur.execute('UPDATE news SET title=?, content=? WHERE id=?', (title, content, news_id))
            conn.commit()

        elif action == 'delete_link':
            link_id = request.form.get('link_id')
            if link_id:
                cur.execute('DELETE FROM user_links WHERE link_id = ?', (link_id,))
                conn.commit()

        elif action == 'process_application':
            app_id = request.form['app_id']
            processed = request.form['processed']
            admin_comment = request.form['admin_comment']
            cur.execute('UPDATE applications SET processed=?, admin_comment=? WHERE id=?', (processed, admin_comment, app_id))
            conn.commit()

        elif action == 'update_role':
            user_id = request.form['user_id']
            new_role = request.form['new_role']
            cur.execute('UPDATE users SET role = ? WHERE user_id = ?', (new_role, user_id))
            conn.commit()

        elif action == 'add_link':
            user_id = request.form['user_id']
            link_name = request.form['link_name']
            link_url = request.form['link_url']
            if user_id and link_name and link_url:
                cur.execute(
                    'INSERT INTO user_links (user_id, app_name, link) VALUES (?, ?, ?)',
                    (user_id, link_name, link_url)
                )
                conn.commit()

    # Получение данных для форм
    cur.execute('SELECT * FROM news')
    news_list = [dict(row) for row in cur.fetchall()]

    cur.execute('SELECT * FROM applications')
    applications = [dict(row) for row in cur.fetchall()]

    cur.execute('SELECT * FROM users')
    users = [dict(row) for row in cur.fetchall()]

    # Получение сервисов и сроков действия
    cur.execute('''
        SELECT s.*, GROUP_CONCAT(p.duration) AS durations
        FROM services s
        LEFT JOIN prices p ON s.id = p.service_id
        GROUP BY s.id
    ''')
    services = []
    for row in cur.fetchall():
        service = dict(row)
        if service['durations']:
            service['durations'] = [{'duration': int(d)} for d in service['durations'].split(',')]
        else:
            service['durations'] = []
        services.append(service)

    # Получение ссылок для всех пользователей
    user_links = {}
    for user in users:
        user_id = user['user_id']
        cur.execute('SELECT link, app_name FROM user_links WHERE user_id = ?', (user_id,))
        user_links[user_id] = [dict(row) for row in cur.fetchall()]

    # Получение подписок
    cur.execute('''
        SELECT
            s.subscription_id,
            u.full_name AS user_name,
            sv.name AS service_name,
            s.start_date,
            s.end_date,p.price,
            s.receipt_path
        FROM subscriptions s
        JOIN users u ON s.user_id = u.user_id
        JOIN services sv ON s.service_id = sv.id
        JOIN prices p ON s.service_id = p.service_id;
    ''')
    subscriptions = [dict(row) for row in cur.fetchall()]

    conn.close()

    return render_template(
        'admin.html',
        news_list=news_list,
        applications=applications,
        users=users,
        user_links=user_links,
        subscriptions=subscriptions,
        services=services
    )
@app.route('/get_user_links/<int:user_id>', methods=['GET'])
def get_user_links(user_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT id, app_name AS name, link AS url FROM user_links WHERE user_id = ?', (user_id,))
    links = [dict(row) for row in cur.fetchall()]
    conn.close()
    return jsonify(links)

@app.route('/add_link', methods=['POST'])
def add_link():
    user_id = request.form['user_id']
    link_name = request.form['link_name']
    link_url = request.form['link_url']
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('INSERT INTO user_links (user_id, app_name, link) VALUES (?, ?, ?)', (user_id, link_name, link_url))
    conn.commit()
    conn.close()
    return '', 201

@app.route('/delete_link/<int:link_id>', methods=['DELETE'])
def delete_link(link_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('DELETE FROM user_links WHERE id = ?', (link_id,))
    conn.commit()
    conn.close()
    return '', 204


@app.route('/send_notification', methods=['POST'])
def send_notification():
    action = request.form.get('action')
    if action == 'add_notification_with_attachment':
        user_id = request.form.get('user_id')
        message = request.form.get('message')
        file = request.files['attachment']

        if file and file.filename != '':
            # Сохраняем файл на сервере
            filename = file.filename
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)

            # Здесь можно реализовать отправку уведомления с данными (user_id, message, file_path)
            # Например, добавить запись в базу данных

            return redirect('/admin')
    return redirect('/admin')

@app.route('/approve_subscription', methods=['POST'])
@login_required
def approve_subscription():
    if current_user.role != 'admin':
        return redirect('/')

    subscription_id = request.form['subscription_id']
    conn = get_db_connection()
    cur = conn.cursor()

    # Подтверждение продления подписки
    cur.execute('''
        UPDATE subscriptions
        SET end_date = DATE(end_date, '+1 month')
        WHERE subscription_id = ?
    ''', (subscription_id,))
    conn.commit()
    conn.close()

    return redirect('/admin')

@app.route('/assign_subscription', methods=['POST'])
def assign_subscription():
    user_id = request.form.get('user_id')
    service_id = request.form.get('service_id')
    start_date = request.form.get('start_date')
    end_date = request.form.get('end_date')
    print(request.form)  # Вывод всех данных из формы


    print(f"user_id: {user_id}, service_id: {service_id}, start_date: {start_date}, end_date: {end_date}")

    if not user_id or not service_id or not start_date or not end_date:
        return "Missing required fields", 400

    # Проверка существования user_id и service_id в базе
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    user = cur.fetchone()
    if not user:
        return f"User with ID {user_id} does not exist", 400

    cur.execute('SELECT * FROM services WHERE id = ?', (service_id,))
    service = cur.fetchone()
    if not service:
        return f"Service with ID {service_id} does not exist", 400

    # Добавление подписки
    try:
        cur.execute('''
            INSERT INTO subscriptions (user_id, service_id, start_date, end_date, receipt_path)
            VALUES (?, ?, ?, ?, NULL)
        ''', (user_id, service_id, start_date, end_date))
        conn.commit()
    except Exception as e:
        print(f"Database error: {e}")
        return "Database error", 500
    finally:
        conn.close()

    return redirect('/admin')


import traceback

@app.route('/get_price')
def get_price():
    try:
        conn = sqlite3.connect(r'C:\Users\kotonai\Downloads\project\database\db.sqlite3')
        cursor = conn.cursor()
        service_id = int(request.args.get('service_id', 0))
        duration = int(request.args.get('period', 0))
        cursor.execute('''
            SELECT price FROM prices
            WHERE service_id = ? AND duration = ?
        ''', (service_id, duration))
        result = cursor.fetchone()

        if result:
            return jsonify({'success': True, 'price': float(result[0])})
        else:
            return jsonify({'success': False, 'message': 'Price not found'})
    except Exception as e:
        print(f"Ошибка: {e}")
    finally:
        conn.close()


@app.route('/profile')
@login_required
def profile_page():
    if current_user.role != 'user':
        return redirect('/')

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute('SELECT link, app_name FROM user_links WHERE user_id = ?', (current_user.id,))
    user_links = cur.fetchall()

    cur.execute('''
        SELECT message, sent_at
        FROM notifications
        WHERE user_id = ?
        ORDER BY sent_at DESC
    ''', (current_user.id,))
    notifications = [
        {
            "message": message,
            "sent_at": datetime.strptime(sent_at, '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d %H:%M:%S')
            if sent_at else None
        }
        for message, sent_at in cur.fetchall()
    ]

    cur.execute('''
        SELECT s.name, s.base_price, sub.start_date, sub.end_date
        FROM subscriptions sub
        JOIN services s ON sub.service_id = s.id
        WHERE sub.user_id = ?
    ''', (current_user.id,))
    subscriptions = [
        {
            "service_name": name,
            "price": base_price,
            "start_date": start_date,
            "end_date": end_date
        }
        for name, base_price, start_date, end_date in cur.fetchall()
    ]

    conn.close()
    return render_template('profile.html', user_links=user_links, notifications=notifications, subscriptions=subscriptions)


@app.route('/update_app_name', methods=['POST'])
@login_required
def update_app_name():
    data = request.get_json()
    link = data.get('link')
    new_app_name = data.get('newAppName')

    if not link or not new_app_name:
        return jsonify({'success': False, 'error': 'Некорректные данные'})

    conn = get_db_connection()
    cur = conn.cursor()

    # Убедимся, что пользователь владеет данной ссылкой
    cur.execute('SELECT link_id FROM user_links WHERE user_id = ? AND link = ?', (current_user.id, link))
    if not cur.fetchone():
        return jsonify({'success': False, 'error': 'Доступ запрещен'})

    # Обновляем название приложения
    cur.execute('UPDATE user_links SET app_name = ? WHERE user_id = ? AND link = ?', (new_app_name, current_user.id, link))
    conn.commit()

    return jsonify({'success': True})


@app.route('/solutions')
def solutions():
    return render_template('solutions.html')

@app.route('/submit_applications', methods=['POST'])
def submit_applications():
    data = request.get_json()
    if not data.get('name') or not data.get('phone'):
        return jsonify({'success': False, 'message': 'Имя и телефон обязательны!'}), 400

    conn = sqlite3.connect(r'C:\Users\kotonai\Downloads\project\database\db.sqlite3')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO applications (name, phone, comment)
        VALUES (?, ?, ?)
    ''', (data['name'], data['phone'], data['comment']))
    conn.commit()
    conn.close()

    return jsonify({'success': True, 'message': 'Заявка успешно добавлена!'})
if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0',port=5000)