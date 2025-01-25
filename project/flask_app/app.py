from flask import Flask, request, render_template, redirect, url_for,flash,send_from_directory,abort,send_file
from flask_login import LoginManager
import sqlite3
import pandas as pd
from io import BytesIO
from flask_login import UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf.csrf import CSRFProtect
from flask import jsonify
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
import os
from dateutil.relativedelta import relativedelta
import logging


app = Flask(__name__)
app.config['SECRET_KEY'] = '#\xcbK\x8f\xa1,\x8b\x85H\x9b\xdd\xa2\xd9:\xcf2\xb3>\x15\xce\x12aBS\xff\xe4\xb0|\xa9x\xdeR'

# Настраиваем LoginManager
login_manager = LoginManager(app)
login_manager.init_app(app)

# Настраиваем папку для загрузки
UPLOAD_FOLDER = r'C:\Users\kotonai\Downloads\project\database\file'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/files/<path:filename>')
def download_file(filename):
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    if not os.path.exists(file_path):
        abort(404)  # Файл не найден
    return send_from_directory(UPLOAD_FOLDER, filename)

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

@app.route('/price')
def price():
    conn = get_db_connection()
    cur = conn.cursor()

    # Получить все услуги с ценами и сортировкой по duration
    cur.execute('''
        SELECT
            s.name AS service_name,
            p.price_type,
            p.price,
            s.description,
            s.category,
            p.duration
        FROM services s
        LEFT JOIN prices p ON s.id = p.service_id
        ORDER BY
            s.category,
            s.id,
            CASE
                WHEN p.duration = 1 THEN 1
                WHEN p.duration = 6 THEN 2
                WHEN p.duration = 12 THEN 3
                ELSE 4
            END
    ''')
    data = cur.fetchall()
    conn.close()

    # Группировка данных по категориям и услугам
    services = {}
    for service_name, price_type, price, description, category, duration in data:
        if category not in services:
            services[category] = {}
        if service_name not in services[category]:
            services[category][service_name] = []
        # Преобразование числового duration в текстовое представление
        duration_map = {
            1: 'месяц',
            6: 'полугодовой',
            12: 'год',
            0: 'пробный период',
            16: 'особая подписка'  # Адаптируйте при необходимости
        }
        display_duration = duration_map.get(duration, f"{duration} мес.")
        services[category][service_name].append({
            'price_type': price_type,
            'price': price,
            'description': description,
            'category': category,
            'duration': display_duration,
            'raw_duration': duration  # Для возможной сортировки в шаблоне
        })
    return render_template('price.html', services=services)

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
            s.end_date,
            p.price,
            s.receipt_path,
            sv.category
        FROM subscriptions s
        JOIN users u ON s.user_id = u.user_id
        JOIN services sv ON s.service_id = sv.id
        JOIN prices p ON s.price_id = p.id;
    ''')

    subscriptions = [
        {
            "id": subscription_id,
            "user_name": user_name,
            "service_name": service_name,
            "start_date": start_date,
            "end_date": end_date,
            "price": price,
            "category": category,
            "receipt_path": os.path.basename(receipt_path) if receipt_path else None
        }
        for subscription_id, user_name, service_name, start_date, end_date, price, receipt_path, category in cur.fetchall()
    ]
        # Получаем все услуги и их цены
    cur.execute('''
        SELECT s.id, s.name, s.base_price, p.price_type, p.price, p.duration
        FROM services s
        LEFT JOIN prices p ON s.id = p.service_id
    ''')
    rows = cur.fetchall()
    conn.close()

    # Группируем цены по услугам
    servicesa = {}
    for row in rows:
        service_id = row['id']
        if service_id not in servicesa:
            servicesa[service_id] = {
                'id': service_id,
                'name': row['name'],
                'base_price': row['base_price'],
                'prices': []
            }
        if row['price_type']:  # Если есть цена, добавляем её
            servicesa[service_id]['prices'].append({
                'price_type': row['price_type'],
                'price': row['price'],
                'duration': row['duration']
            })

    conn.close()

    return render_template(
        'admin.html',
        news_list=news_list,
        applications=applications,
        users=users,
        user_links=user_links,
        subscriptions=subscriptions,
        services=services,
        servicesa=list(servicesa.values())
    )


# Редактирование цен
@app.route('/admin/prices/edit', methods=['POST'])
def update_price():
    conn = get_db_connection()
    cur = conn.cursor()

    service_id = request.form['service_id']
    price_type = request.form['price_type']
    price = request.form['price']
    duration = request.form.get('duration', None)  # Длительность может быть пустой

    try:
        # Обновляем или добавляем цену
        cur.execute('''
            INSERT OR REPLACE INTO prices (service_id, price_type, price, duration)
            VALUES (?, ?, ?, ?)
        ''', (service_id, price_type, price, duration))
        
        conn.commit()
    except Exception as e:
        print(f"Ошибка: {e}")
        conn.rollback()
    finally:
        conn.close()

    return redirect('/admin')

# Загрузка Excel-файла
@app.route('/admin/prices/upload', methods=['POST'])
def upload_prices():
    if 'excel_file' not in request.files:
        return redirect('/admin')

    file = request.files['excel_file']
    if file.filename.endswith(('.xlsx', '.xls')):
        conn = get_db_connection()
        cur = conn.cursor()

        # Читаем Excel
        df_services = pd.read_excel(file, sheet_name='Services')
        df_prices = pd.read_excel(file, sheet_name='Prices')

        # Обновляем услуги
        for _, row in df_services.iterrows():
            cur.execute('''
                INSERT OR REPLACE INTO services (id, name, description, base_price, category)
                VALUES (?, ?, ?, ?, ?)
            ''', (row['id'], row['name'], row['description'], row['base_price'], row['category']))

        # Обновляем цены
        for _, row in df_prices.iterrows():
            cur.execute('''
                INSERT OR REPLACE INTO prices (id, service_id, price_type, price, duration)
                VALUES (?, ?, ?, ?, ?)
            ''', (row['id'], row['service_id'], row['price_type'], row['price'], row['duration']))

        conn.commit()
        conn.close()

    return redirect('/admin')

# Скачивание шаблона Excel
@app.route('/admin/prices/download')
def download_template():
    conn = get_db_connection()
    cur = conn.cursor()

    # Получаем данные
    services = cur.execute('SELECT * FROM services').fetchall()
    prices = cur.execute('SELECT * FROM prices').fetchall()
    conn.close()

    # Создаем DataFrame
    df_services = pd.DataFrame(services, columns=['id', 'name', 'description', 'base_price', 'category'])
    df_prices = pd.DataFrame(prices, columns=['id', 'service_id', 'price_type', 'price', 'duration'])

    # Создаем Excel в памяти
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_services.to_excel(writer, sheet_name='Services', index=False)
        df_prices.to_excel(writer, sheet_name='Prices', index=False)
    output.seek(0)

    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        download_name='prices_template.xlsx',
        as_attachment=True
    )

@app.route('/delete_subscription', methods=['POST'])
def delete_subscription():
    app.logger.info(f"POST data: {request.form}")
    subscription_id = request.form.get('subscription_id')
    app.logger.info(f"Received subscription_id: {subscription_id}")
    conn = get_db_connection()
    subscription = conn.execute('SELECT * FROM subscriptions WHERE subscription_id = ?', (subscription_id,)).fetchone()

    if not subscription:
        flash('Подписка не найдена', 'error')
        conn.close()
        return redirect('/admin')

    try:
        # Удаление файла чека, если он существует
        if subscription['receipt_path']:
            receipt_path = os.path.join(app.root_path, 'static', subscription['receipt_path'])
            if os.path.exists(receipt_path):
                os.remove(receipt_path)

        conn.execute('DELETE FROM subscriptions WHERE subscription_id = ?', (subscription_id,))
        conn.commit()
        flash('Подписка успешно удалена', 'success')
    except Exception as e:
        conn.rollback()
        flash('Ошибка при удалении подписки', 'error')
        app.logger.error(f"Ошибка при удалении подписки: {e}")
    finally:
        conn.close()

    return redirect('/admin')


# Продление подписки
@app.route('/renew_subscription', methods=['POST'])
def renew_subscription():
    subscription_id = request.form.get('subscription_id')
    conn = get_db_connection()
    subscription = conn.execute('SELECT * FROM subscriptions WHERE subscription_id = ?', (subscription_id,)).fetchone()

    if not subscription:
        flash('Подписка не найдена', 'error')
        conn.close()
        return redirect('/admin')

    try:
        # Получаем текущую дату окончания подписки
        current_end_date = datetime.strptime(subscription['end_date'], '%Y-%m-%d')

        # Если дата окончания в прошлом, продлеваем с текущей даты
        if current_end_date < datetime.now():
            new_end_date = datetime.now() + timedelta(days=30)
        else:
            # Иначе продлеваем с текущей даты окончания
            new_end_date = current_end_date + timedelta(days=30)

        # Обновляем дату окончания подписки
        conn.execute('UPDATE subscriptions SET end_date = ? WHERE subscription_id = ?', (new_end_date.strftime('%Y-%m-%d'), subscription_id))
        conn.commit()
        flash('Подписка успешно продлена', 'success')
    except Exception as e:
        conn.rollback()
        flash('Ошибка при продлении подписки', 'error')
        app.logger.error(f"Ошибка при продлении подписки: {e}")
    finally:
        conn.close()

    return redirect('/admin')

@app.route('/add_link', methods=['POST'])
def add_link():
    try:
        app.logger.debug("Received form data: %s", request.form)
        user_id = request.form.get('user_id')
        link_name = request.form.get('link_name')
        link_url = request.form.get('link_url')

        if not all([user_id, link_name, link_url]):
            return jsonify({"error": "Missing required fields"}), 400

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('''
            INSERT INTO user_links (user_id, app_name, link)
            VALUES (?, ?, ?)
        ''', (int(user_id), link_name, link_url))
        conn.commit()
        return jsonify({"success": True}), 201

    except sqlite3.Error as e:
        app.logger.error("Database error: %s", str(e))
        return jsonify({"error": "Database error"}), 500

    except Exception as e:
        app.logger.exception("Unexpected error")
        return jsonify({"error": "Internal server error"}), 500
    finally:
        if 'conn' in locals():
            conn.close()

@app.route('/delete_link/<int:link_id>', methods=['DELETE'])
def delete_link(link_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('DELETE FROM user_links WHERE link_id = ?', (link_id,))
    conn.commit()
    conn.close()
    return '', 204

@app.route('/get_user_links', methods=['GET'])
def get_user_links():
    user_id = request.args.get('userId')
    if not user_id:
        return jsonify({"success": False, "error": "Не указан userId"}), 400
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT * FROM user_links WHERE user_id = ?', (user_id,))
        links = cur.fetchall()
        conn.close()

        if not links:
            return jsonify({"success": False, "error": "Ссылки для пользователя не найдены"}), 404

        # Преобразуем результат в список словарей
        columns = [column[0] for column in cur.description]
        links_list = [dict(zip(columns, link)) for link in links]

        return jsonify({"success": True, "data": links_list}), 200

    except sqlite3.Error as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/get_link/<int:link_id>', methods=['GET'])
def get_link(link_id):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT link_id, app_name, link FROM user_links WHERE link_id = ?', (link_id,))
        link = cur.fetchone()
        conn.close()

        if link is None:
            return jsonify({"success": False, "error": "Ссылка не найдена"}), 404

        # Преобразуем строку в словарь
        link_dict = {"link_id": link[0], "app_name": link[1], "link": link[2]}
        return jsonify(link_dict), 200

    except sqlite3.Error as e:
        return jsonify({"success": False, "error": str(e)}), 500



@app.route('/update_link', methods=['POST'])
def update_link():
    data = request.get_json()
    print("Полученные данные:", data)  # Логируем данные

    # Проверка наличия обязательных полей
    if not data or 'link_id' not in data or 'app_name' not in data or 'link' not in data:
        print("Ошибка: отсутствуют обязательные поля")
        return jsonify({"success": False, "error": "Необходимы данные link_id, app_name и link"}), 400

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('''
            UPDATE user_links
            SET app_name = ?, link = ?
            WHERE link_id = ?
        ''', (data['app_name'], data['link'], data['link_id']))
        conn.commit()
        conn.close()

        if cur.rowcount == 0:
            print("Ошибка: ссылка с ID не найдена")
            return jsonify({"success": False, "error": "Ссылка с указанным ID не найдена"}), 404

        return jsonify({"success": True}), 200

    except sqlite3.Error as e:
        print("Ошибка базы данных:", str(e))
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/send_notification', methods=['POST'])
def send_notification():
    action = request.form.get('action')
    if action == 'add_notification_with_attachment':
        user_id = request.form.get('user_id')
        message = request.form.get('message')
        time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        file = request.files.get('attachment')

        if file and file.filename != '':
            try:
                # Создаем папку для загрузок, если она не существует
                if not os.path.exists(app.config['UPLOAD_FOLDER']):
                    os.makedirs(app.config['UPLOAD_FOLDER'])

                # Сохраняем файл на сервере
                filename = file.filename
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)

                # Сохраняем данные в базу данных
                conn = get_db_connection()
                cur = conn.cursor()
                cur.execute('''
                    INSERT INTO notifications (sent_at,user_id, message, receipt_path)
                    VALUES (?, ?, ?, ?)
                ''', (time,user_id, message, file_path))
                conn.commit()  # Фиксируем изменения
                conn.close()  # Закрываем соединение

                return redirect('/admin')

            except Exception as e:
                print(f"Ошибка: {e}")
                return "Произошла ошибка при обработке запроса", 500

    return redirect('/admin')

@app.route('/assign_subscription', methods=['POST'])
def assign_subscription():
    user_id = request.form.get('user_id')
    service_id = request.form.get('service_id')
    period = request.form.get('period')  # Получаем период как значение (0, 1, 6, 12)
    start_date = request.form.get('start_date')

    if not user_id or not service_id or not period or not start_date:
        return "Missing required fields", 400

    # Получение соответствующего price_id
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
        SELECT id, duration FROM prices
        WHERE service_id = ? AND duration = ?
    ''', (service_id, period))
    price_row = cur.fetchone()
    if not price_row:
        return "Invalid service or period", 400

    price_id, duration = price_row

    # Вычисляем дату окончания
    start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
    if duration == 0:  # Одноразовый
        end_date_obj = start_date_obj + timedelta(days=1)
    else:
        end_date_obj = start_date_obj + relativedelta(months=duration)

    end_date = end_date_obj.strftime('%Y-%m-%d')

    # Проверка уникальности подписки
    cur.execute('''
        SELECT * FROM subscriptions
        WHERE user_id = ? AND service_id = ? AND end_date >= DATE('now')
    ''', (user_id, service_id))
    if cur.fetchone():
        return "User already has an active subscription for this service", 400

    # Добавление подписки
    try:
        cur.execute('''
            INSERT INTO subscriptions (user_id, service_id, price_id, start_date, end_date, receipt_path,period)
            VALUES (?, ?, ?, ?, ?, NULL,?)
        ''', (user_id, service_id, price_id, start_date, end_date,period))
        conn.commit()
    except Exception as e:
        return f"Database error: {e}", 500
    finally:
        conn.close()

    return redirect('/admin')

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
    SELECT message, sent_at, receipt_path
    FROM notifications
    WHERE user_id = ?
    ORDER BY sent_at DESC
''', (current_user.id,))

    notifications = [
        {
            "message": message,
            "sent_at": datetime.strptime(sent_at, '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d %H:%M:%S')
            if sent_at else None,
            "receipt_path": os.path.basename(receipt_path)
        }
        for message, sent_at, receipt_path in cur.fetchall()
    ]

    cur.execute('''
        SELECT s.name, s.base_price, sub.start_date, sub.end_date, sub.period, sub.subscription_id
        FROM subscriptions sub
        JOIN services s ON sub.service_id = s.id
        WHERE sub.user_id = ?
    ''', (current_user.id,))
    subscriptions = [
        {
            "service_name": name,
            "price": base_price,
            "start_date": start_date,
            "end_date": end_date,
            "period": period,
            "id": id
        }
        for name, base_price, start_date, end_date, period, id in cur.fetchall()
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

logging.basicConfig(level=logging.DEBUG)

@app.route('/upload_receipt/<int:subscription_id>', methods=['POST'])
def upload_receipt(subscription_id):
    try:
        app.logger.debug(f"Запрос на загрузку файла для подписки ID: {subscription_id}")

        if 'receipt' not in request.files:
            return jsonify({'message': 'Файл не найден в запросе'}), 400

        file = request.files['receipt']
        if file.filename == '':
            return jsonify({'message': 'Файл не выбран'}), 400

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

            app.logger.debug(f"Пытаемся сохранить файл: {filepath}")

            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
            file.save(filepath)

            app.logger.debug(f"Файл успешно сохранён: {filepath}")

            conn = get_db_connection()
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE subscriptions
                SET receipt_path = ?
                WHERE subscription_id = ?
            """, (filepath, subscription_id))

            if cursor.rowcount == 0:
                raise ValueError('Подписка с указанным ID не найдена')

            conn.commit()
            conn.close()

            app.logger.debug("Запись в базе данных обновлена")

            return jsonify({'message': 'Чек успешно загружен!', 'file_path': filepath}), 200

        return jsonify({'message': 'Недопустимый тип файла'}), 400

    except Exception as e:
        app.logger.error(f"Ошибка: {str(e)}")
        return jsonify({'message': f'Ошибка сервера: {str(e)}'}), 500
if __name__ == '__main__':
    app.run(host='0.0.0.0',port=5000)