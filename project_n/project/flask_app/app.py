from flask import Flask, request, render_template, redirect
import sqlite3

app = Flask(__name__)


def get_db_connection():
    conn = sqlite3.connect(r'C:\Users\Nurlan\Desktop\123\project\database\app.db')  # Указываем относительный путь к базе данных
    conn.row_factory = sqlite3.Row  # Для доступа к данным по имени столбца
    return conn

def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
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

@app.route('/')
def home():
    conn = get_db_connection()
    cur = conn.cursor()
    # Извлекаем только последние 2 новости
    cur.execute('SELECT title, date, content FROM news ORDER BY date DESC LIMIT 2;')
    data = cur.fetchall()
    conn.close()
    return render_template('index.html', data=data)

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

@app.route('/news')
def news():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT title, date, content FROM news ORDER BY date DESC;')
    data = cur.fetchall()
    conn.close()
    return render_template('news.html', data=data)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/dogovor')
def dogovor():
    return render_template('dogovor.html')

@app.route('/price')
def price():
    # Разовые услуги (примерная структура)
    single_services = [
        {
            'name': 'Сложность «D»',
            'price': '9 000',
            'description': 'Консультация, обучение до 1 часа, ограничение 1 раз в сутки. Работы свыше 1 часа оплачиваются по ставке Сложности «С».'
        },
        {
            'name': 'Сложность «C»',
            'price': '10 750',
            'description': 'Настройка, консультация, обучение до 2-х часов, ограничение 1 раз в сутки. Работы свыше 2-х часов оплачиваются по ставке Сложности «В».'
        },
        {
            'name': 'Сложность «B»',
            'price': '12 500',
            'description': 'Настройка, создание новых доработок, консультация по существующим доработкам и типовым базам.'
        },
        {
            'name': 'Сложность «A»',
            'price': '15 400',
            'description': 'Разработка, интеграция новых программ.'
        },
    ]

    # Пакеты услуг на месяц (пример)
    monthly_services = [
        {
            'name': 'Стандарт',
            'description': [
                '3 консультации по 20 минут',
                'Рассмотрение заявки в течение 4-х часов',
                'Обновление платформы и типовых конфигураций до 3-х баз'
            ],
            'prices': {
                '1 месяц': '13 000',
                '6 месяцев': '74 100',
                '12 месяцев': '130 000'
            }
        },
        {
            'name': 'Расширенный',
            'description': [
                '3 консультации по 20 минут',
                'Рассмотрение заявки в течение 4-х часов',
                'Обновление платформы и типовых конфигураций до 5-ти баз'
            ],
            'prices': {
                '1 месяц': '15 000',
                '6 месяцев': '85 500',
                '12 месяцев': '150 000'
            }
        }
    ]

    # Облако «ВСЕ ПРОСТО»
    vse_prosto = {
        'description': [
            'Тех. Поддержка',
            'Удаленный доступ',
            'Ведение до 5 баз (общий вес до 12 ГБ)',
            'Обновление баз',
            'Одно подключение',
            'Лицензия на 1 пользователя',
            'ИТС на 1 организацию',
            '3 консультации по 20 минут'
        ],
        'prices': {
            '1 месяц': '13 000',
            '6 месяцев': '65 000',
            '12 месяцев': '130 000'
        }
    }

    # Собрать свой тариф
    # Основной тариф "Эконом"
    ekonom = {
        'description': [
            'Тех. Поддержка',
            'Удаленный доступ',
            'Ведение до 5 баз (общий вес до 12 ГБ)',
            'Обновление баз',
            'Одно подключение'
        ],
        'prices': {
            '1 месяц': '4 800',
            '6 месяцев': '24 000',
            '12 месяцев': '48 000'
        }
    }

    # Доп. опции для "Собрать свой тариф"
    addons = [
        {
            'name': 'Доп. подключение к серверу',
            'description': ['Доп. лицензия для подключения нового пользователя'],
            'prices': {
                '1 месяц': '2 500',
                '6 месяцев': '12 500',
                '12 месяцев': '25 000'
            }
        },
        {
            'name': 'ИТС на 1 базу',
            'description': ['Возможность отправлять ЭСФ, ЭАВР, ЭСНТ'],
            'prices': {
                '1 месяц': '1 300',
                '6 месяцев': '6 500',
                '12 месяцев': '13 000'
            }
        },
        {
            'name': 'Архивирование',
            'description': ['Архив каждую неделю (понедельник и пятница)'],
            'prices': {
                '1 месяц': '650',
                '6 месяцев': '3 250',
                '12 месяцев': '6 500'
            }
        }
    ]

    return render_template(
        'price.html',
        single_services=single_services,
        monthly_services=monthly_services,
        vse_prosto=vse_prosto,
        ekonom=ekonom,
        addons=addons
    )

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0',port=5000)
