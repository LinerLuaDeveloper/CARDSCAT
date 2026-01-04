import sqlite3
import telebot
from telebot import types
import time
import random
import logging
from datetime import datetime
import re
import json
import os

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

bot = telebot.TeleBot('8205728685:AAEX0xtuHGthCb4ZYy0i18CqA8DGymkNtPs')

# Время запуска бота (для игнорирования старых сообщений)
BOT_START_TIME = time.time()

# Файлы для сохранения данных
CARDS_DB_FILE = 'cards_database.json'
HIDDEN_CARDS_FILE = 'hidden_cards.json'
SHOP_STATUS_FILE = 'shop_status.json'
CRAFT_RECIPES_FILE = 'craft_recipes.json'

# Сначала определяем переменные как глобальные
CARDS_DATABASE = {}
HIDDEN_CARDS = set()
SHOP_ENABLED = True  # По умолчанию магазин включен
CRAFT_RECIPES = {}  # Рецепты крафта

# Редкости карточек и их стоимости
RARITIES = {
    "🟤": {"name": "Обычная", "coins": 1, "chance": 30},
    "⚪️": {"name": "Необычная", "coins": 3, "chance": 25},
    "🟢": {"name": "Редкая", "coins": 5, "chance": 20},
    "🟠": {"name": "Супер редкая", "coins": 7, "chance": 10},
    "🟣": {"name": "Эпическая", "coins": 10, "chance": 8},
    "🟡": {"name": "Легендарная", "coins": 50, "chance": 4},
    "🔴": {"name": "Мифическая", "coins": 70, "chance": 2},
    "💎": {"name": "Алмазная", "coins": 100, "chance": 0.5},
    "👑": {"name": "Божественная", "coins": 500, "chance": 0.3},
    "❔": {"name": "Секретная", "coins": 1000, "chance": 0.2},
    "🖥️": {"name": "Админская", "coins": 1777, "chance": 0}
}

# Инициализация базы карточек по умолчанию
DEFAULT_CARDS = {
    "Инвертированный Симба": {
        "rarity": "⚪️",
        "coins": 3,
        "description": "Кот инвертированный в противоположные цвета.",
        "image": "https://sprutio.beget.com/image_cache/gagarin7/alexa3j5/3627c1357b3564d8ad82e3543d7c0513/inverssimba.jpg",
        "craft_only": False
    },
    "Grow а Симба, Steal a Алиса": {
        "rarity": "🟣",
        "coins": 10,
        "description": "Коты попали в роблокс игры!",
        "image": "https://sprutio.beget.com/image_cache/gagarin7/alexa3j5/0be979231af670f1c11e76996a1385ac/growandstealsimba.jpg",
        "craft_only": False
    },
    "Лайнер": {
        "rarity": "🖥️",
        "coins": 1777,
        "description": "Это лайнер. Ну да, лучшая карточка в боте, что такого? Вам просто повезло, ничего особенного.",
        "image": "https://sprutio.beget.com/image_cache/gagarin7/alexa3j5/028e0013f79f399c59713d06789c0a89/liner.jpg",
        "craft_only": False
    },
    "Симба на миссии": {
        "rarity": "👑",
        "coins": 500,
        "description": "Кот-агент 😎",
        "image": "https://sprutio.beget.com/image_cache/gagarin7/alexa3j5/9b6889f07b9329cee41340fb0664b766/simbainmission.jpg",
        "craft_only": False
    },
    "Симба грабитель": {
        "rarity": "⚪️",
        "coins": 3,
        "description": "Ии ультануло. Кот грабитель.",
        "image": "https://sprutio.beget.com/image_cache/gagarin7/alexa3j5/ecce48ba328c1250f640150053944a10/simbarobber.jpg",
        "craft_only": False
    },
    "Симба удивлён": {
        "rarity": "⚪️",
        "coins": 3,
        "description": "Просто удивлённый кот, скорее всего он увидел мотылька.",
        "image": "https://sprutio.beget.com/image_cache/gagarin7/alexa3j5/b3e302e21aeeb6adcec0245d9c13ed18/simbawow.jpg",
        "craft_only": False
    },
    "Симба злой король": {
        "rarity": "🔴",
        "coins": 70,
        "description": "Кот который выглядит жутковато..",
        "image": "https://sprutio.beget.com/image_cache/gagarin7/alexa3j5/81733e770f94b9e8a65ff5567341e673/simbaking.jpg",
        "craft_only": False
    },
    "Симбакула": {
        "rarity": "🟢",
        "coins": 5,
        "description": "Рыба?.. АКУЛА! А, это всё таки кот..",
        "image": "https://sprutio.beget.com/image_cache/gagarin7/alexa3j5/df2807cffe2f3cd124aadab2f6d76884/simbashark.jpg",
        "craft_only": False
    },
    "Симба с Алисой на окне": {
        "rarity": "🟠",
        "coins": 7,
        "description": "Две кошки вместе.",
        "image": "https://sprutio.beget.com/image_cache/gagarin7/alexa3j5/25330c0dee36510e4fc593b76dc9eb79/simbawithalisa.jph.jpg",
        "craft_only": False
    },
    "Симба лежит на земле": {
        "rarity": "🟣",
        "coins": 10,
        "description": "Кот который охотится на птиц в кормушке.",
        "image": "https://sprutio.beget.com/image_cache/gagarin7/alexa3j5/d353493d5bc7c6ae849b03c935dc6fd8/simbasitingrass.jpg",
        "craft_only": False
    },
    "Симба-клоун": {
        "rarity": "🔴",
        "coins": 100,
        "description": "Кот-клоун. Буквально каждый из нас похож на него.",
        "image": "https://sprutio.beget.com/image_cache/gagarin7/alexa3j5/39d1c6d31d9adace2338f12e74fd3364/clownsimba.jpg",
        "craft_only": False
    },
    "Симба полицейский": {
        "rarity": "🟡",
        "coins": 50,
        "description": "Кот-полицейский, настоящий страж порядка!",
        "image": "https://sprutio.beget.com/image_cache/gagarin7/alexa3j5/26132586be78a56dbb0cd51c4a5c3696/simbapolice.jpg",
        "craft_only": False
    },
    "Симба с рыбкой": {
        "rarity": "🟤",
        "coins": 1,
        "description": "Кот с пластиковой рыбкой.",
        "image": "https://sprutio.beget.com/image_cache/gagarin7/alexa3j5/c7568dfac2c49ca6335e493e2bb8a597/simbawithfish.jpg",
        "craft_only": False
    },
    "Алиса-убийца": {
        "rarity": "🟣",
        "coins": 10,
        "description": "Кошка с острым ножом.",
        "image": "https://sprutio.beget.com/image_cache/gagarin7/alexa3j5/7f8a704aa7184492f6a0ea57e2246410/alicekiller.jpg",
        "craft_only": False
    },
    "Злая и Добрая Алиса": {
        "rarity": "🔴",
        "coins": 70,
        "description": "Две светящиеся кошки. Вроде бы они одинаковые, а вроде и нет..",
        "image": "https://sprutio.beget.com/image_cache/gagarin7/alexa3j5/71b056bc6b7f24f4dbc7e436f63d511d/godandevilsimba.jpg",
        "craft_only": False
    },
    "Пиксельная Алиса": {
        "rarity": "🟠",
        "coins": 7,
        "description": "Кошка немножко пиксель.",
        "image": "https://sprutio.beget.com/image_cache/gagarin7/alexa3j5/fe260aa01b4a3fd3567ad30f9a84f65b/pixelalisa.jpg",
        "craft_only": False
    },
    "Алиса-красотка": {
        "rarity": "🟡",
        "coins": 50,
        "description": "Кошка-красотка. Целуйте экраны>:)",
        "image": "https://sprutio.beget.com/image_cache/gagarin7/alexa3j5/642ef4a209468d212bdb64c2d9ff630f/alisabeat.jpg",
        "craft_only": False
    }
}

# Загрузка сохраненных данных
def load_saved_data():
    global CARDS_DATABASE, HIDDEN_CARDS, SHOP_ENABLED, CRAFT_RECIPES
    
    # Загрузка карточек
    if os.path.exists(CARDS_DB_FILE):
        try:
            with open(CARDS_DB_FILE, 'r', encoding='utf-8') as f:
                loaded_cards = json.load(f)
                CARDS_DATABASE.update(loaded_cards)
            logger.info(f"Загружено {len(loaded_cards)} карточек из файла")
        except Exception as e:
            logger.error(f"Ошибка загрузки карточек: {e}")
            # Если ошибка, используем карточки по умолчанию
            CARDS_DATABASE.update(DEFAULT_CARDS)
    else:
        # Если файла нет, используем карточки по умолчанию
        CARDS_DATABASE.update(DEFAULT_CARDS)
    
    # Загрузка скрытых карточек
    if os.path.exists(HIDDEN_CARDS_FILE):
        try:
            with open(HIDDEN_CARDS_FILE, 'r', encoding='utf-8') as f:
                hidden_list = json.load(f)
                HIDDEN_CARDS.update(hidden_list)
            logger.info(f"Загружено {len(hidden_list)} скрытых карточек")
        except Exception as e:
            logger.error(f"Ошибка загрузки скрытых карточек: {e}")
    
    # Загрузка статуса магазина
    if os.path.exists(SHOP_STATUS_FILE):
        try:
            with open(SHOP_STATUS_FILE, 'r', encoding='utf-8') as f:
                shop_status = json.load(f)
                SHOP_ENABLED = shop_status.get('enabled', True)
            logger.info(f"Статус магазина загружен: {'включен' if SHOP_ENABLED else 'выключен'}")
        except Exception as e:
            logger.error(f"Ошибка загрузки статуса магазина: {e}")
    
    # Загрузка рецептов крафта
    if os.path.exists(CRAFT_RECIPES_FILE):
        try:
            with open(CRAFT_RECIPES_FILE, 'r', encoding='utf-8') as f:
                CRAFT_RECIPES.update(json.load(f))
            logger.info(f"Загружено {len(CRAFT_RECIPES)} рецептов крафта")
        except Exception as e:
            logger.error(f"Ошибка загрузки рецептов крафта: {e}")

# Сохранение данных
def save_cards_database():
    try:
        with open(CARDS_DB_FILE, 'w', encoding='utf-8') as f:
            json.dump(CARDS_DATABASE, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Ошибка сохранения карточек: {e}")

def save_hidden_cards():
    try:
        with open(HIDDEN_CARDS_FILE, 'w', encoding='utf-8') as f:
            json.dump(list(HIDDEN_CARDS), f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Ошибка сохранения скрытых карточек: {e}")

def save_shop_status():
    try:
        with open(SHOP_STATUS_FILE, 'w', encoding='utf-8') as f:
            json.dump({'enabled': SHOP_ENABLED}, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Ошибка сохранения статуса магазина: {e}")

def save_craft_recipes():
    try:
        with open(CRAFT_RECIPES_FILE, 'w', encoding='utf-8') as f:
            json.dump(CRAFT_RECIPES, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Ошибка сохранения рецептов крафта: {e}")

# Владельцы бота
OWNER_IDS = [7599616968, 5872295617, 8112013114]

# КД на кнопки (в секундах)
BUTTON_COOLDOWNS = {
    'get_card': 5,
    'profile': 3,
    'my_cards': 3,
    'shop': 3,
    'all_cards': 3,
    'craft': 3
}

# Словари для хранения состояний
CARD_ADD_STATES = {}
PROMO_CREATION_STATES = {}
CARD_EDIT_STATES = {}
MESSAGE_OWNERS = {}
ACTIVE_SELECTIONS = {}  # Для отслеживания активных выборов карточек
CARD_SELLING_STATES = {}  # Для отслеживания карточек, которые уже выставлены на продажу
USER_SELLING_STATES = {}  # Для отслеживания пользователей, которые находятся в процессе продажи
USER_PRICE_INPUT_STATES = {}  # Для отслеживания пользователей, которые вводят цену
USER_CRAFT_STATES = {}  # Для отслеживания пользователей в процессе крафта

import sqlite3
import time
from datetime import datetime

def init_db():
    conn = sqlite3.connect('cats.db')
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            coins INTEGER DEFAULT 0,
            total_cards INTEGER DEFAULT 0
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_cards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            rarity TEXT,
            card_name TEXT,
            obtained_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS market (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            seller_id INTEGER,
            card_id INTEGER,
            price INTEGER,
            listing_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (seller_id) REFERENCES users (user_id),
            FOREIGN KEY (card_id) REFERENCES user_cards (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cooldowns (
            user_id INTEGER PRIMARY KEY,
            last_card_time INTEGER,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS button_cooldowns (
            user_id INTEGER,
            button_type TEXT,
            last_press_time INTEGER,
            PRIMARY KEY (user_id, button_type)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS promocodes (
            code TEXT PRIMARY KEY,
            reward_type TEXT NOT NULL,
            reward_value TEXT NOT NULL,
            uses_left INTEGER DEFAULT 1,
            created_by INTEGER,
            created_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (created_by) REFERENCES users (user_id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS used_promocodes (
            user_id INTEGER,
            promo_code TEXT,
            used_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (user_id, promo_code),
            FOREIGN KEY (user_id) REFERENCES users (user_id),
            FOREIGN KEY (promo_code) REFERENCES promocodes (code)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bans (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            reason TEXT,
            banned_by INTEGER,
            banned_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (banned_by) REFERENCES users (user_id)
        )
    ''')

    conn.commit()
    conn.close()

def get_user(user_id, username):
    conn = sqlite3.connect('cats.db')
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    user = cursor.fetchone()

    if not user:
        cursor.execute('INSERT INTO users (user_id, username, coins, total_cards) VALUES (?, ?, 0, 0)',
                       (user_id, username))
        conn.commit()
        user = (user_id, username, 0, 0)

    conn.close()
    return user

def get_random_card():
    available_cards = [card for card in CARDS_DATABASE.keys() 
                      if card not in HIDDEN_CARDS and not CARDS_DATABASE[card].get('craft_only', False)]
    if not available_cards:
        return random.choice(list(CARDS_DATABASE.keys()))
    return random.choice(available_cards)

def is_owner(user_id):
    return user_id in OWNER_IDS

def is_user_banned(user_id):
    """Проверяет, забанен ли пользователь"""
    conn = sqlite3.connect('cats.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM bans WHERE user_id = ?', (user_id,))
    banned = cursor.fetchone()
    conn.close()
    return banned is not None

def get_ban_info(user_id):
    """Получает информацию о бане пользователя"""
    conn = sqlite3.connect('cats.db')
    cursor = conn.cursor()
    cursor.execute('SELECT username, reason, banned_by, banned_time FROM bans WHERE user_id = ?', (user_id,))
    ban_info = cursor.fetchone()
    conn.close()
    return ban_info

def check_button_cooldown(user_id, button_type):
    """Проверяет КД на кнопку"""
    current_time = time.time()
    
    conn = sqlite3.connect('cats.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT last_press_time FROM button_cooldowns WHERE user_id = ? AND button_type = ?', 
                   (user_id, button_type))
    result = cursor.fetchone()
    
    if result:
        last_press = result[0]
        cooldown_time = BUTTON_COOLDOWNS.get(button_type, 3)
        
        if current_time - last_press < cooldown_time:
            conn.close()
            return False
    
    cursor.execute('''
        INSERT OR REPLACE INTO button_cooldowns (user_id, button_type, last_press_time) 
        VALUES (?, ?, ?)
    ''', (user_id, button_type, current_time))
    
    conn.commit()
    conn.close()
    return True

def is_valid_url(url):
    """Проверяет, является ли строка валидным URL"""
    regex = re.compile(
        r'^(?:http|ftp)s?://'
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'
        r'localhost|'
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
        r'(?::\d+)?'
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return re.match(regex, url) is not None

def store_message_owner(message_id, user_id):
    """Сохраняет владельца сообщения с кнопками"""
    MESSAGE_OWNERS[message_id] = user_id

def check_message_owner(message_id, user_id):
    """Проверяет, принадлежит ли сообщение пользователю"""
    return MESSAGE_OWNERS.get(message_id) == user_id

def add_active_selection(user_id, card_id, selection_type):
    """Добавляет активный выбор карточки"""
    key = f"{user_id}_{selection_type}"
    ACTIVE_SELECTIONS[key] = card_id

def check_active_selection(user_id, card_id, selection_type):
    """Проверяет, выбрал ли пользователь уже эту карточку"""
    key = f"{user_id}_{selection_type}"
    return ACTIVE_SELECTIONS.get(key) == card_id

def remove_active_selection(user_id, selection_type):
    """Удаляет активный выбор"""
    key = f"{user_id}_{selection_type}"
    if key in ACTIVE_SELECTIONS:
        del ACTIVE_SELECTIONS[key]

def is_card_already_selling(user_id, card_id):
    """Проверяет, выставлена ли карточка уже на продажу"""
    conn = sqlite3.connect('cats.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM market WHERE card_id = ?', (card_id,))
    result = cursor.fetchone()
    conn.close()
    return result is not None

def add_card_selling_state(user_id, card_id):
    """Добавляет карточку в состояние продажи"""
    key = f"{user_id}_selling"
    if key not in CARD_SELLING_STATES:
        CARD_SELLING_STATES[key] = set()
    CARD_SELLING_STATES[key].add(card_id)

def remove_card_selling_state(user_id, card_id):
    """Удаляет карточку из состояния продажи"""
    key = f"{user_id}_selling"
    if key in CARD_SELLING_STATES and card_id in CARD_SELLING_STATES[key]:
        CARD_SELLING_STATES[key].remove(card_id)

def is_card_in_selling_state(user_id, card_id):
    """Проверяет, находится ли карточка в состоянии продажи"""
    key = f"{user_id}_selling"
    return key in CARD_SELLING_STATES and card_id in CARD_SELLING_STATES[key]

def add_user_selling_state(user_id, card_id):
    """Добавляет пользователя в состояние продажи"""
    USER_SELLING_STATES[user_id] = {
        'card_id': card_id,
        'start_time': time.time()
    }

def remove_user_selling_state(user_id):
    """Удаляет пользователя из состояния продажи"""
    if user_id in USER_SELLING_STATES:
        del USER_SELLING_STATES[user_id]

def is_user_in_selling_state(user_id):
    """Проверяет, находится ли пользователь в состоянии продажи"""
    return user_id in USER_SELLING_STATES

def get_user_selling_card(user_id):
    """Получает карточку, которую пользователь пытается продать"""
    if user_id in USER_SELLING_STATES:
        return USER_SELLING_STATES[user_id]['card_id']
    return None

def add_user_price_input_state(user_id, card_id):
    """Добавляет пользователя в состояние ввода цены"""
    USER_PRICE_INPUT_STATES[user_id] = {
        'card_id': card_id,
        'start_time': time.time()
    }

def remove_user_price_input_state(user_id):
    """Удаляет пользователя из состояния ввода цены"""
    if user_id in USER_PRICE_INPUT_STATES:
        del USER_PRICE_INPUT_STATES[user_id]

def is_user_in_price_input_state(user_id):
    """Проверяет, находится ли пользователь в состоянии ввода цены"""
    return user_id in USER_PRICE_INPUT_STATES

def get_user_price_input_card(user_id):
    """Получает карточку, для которой пользователь вводит цену"""
    if user_id in USER_PRICE_INPUT_STATES:
        return USER_PRICE_INPUT_STATES[user_id]['card_id']
    return None

def add_user_craft_state(user_id, target_card):
    """Добавляет пользователя в состояние крафта"""
    USER_CRAFT_STATES[user_id] = {
        'target_card': target_card,
        'start_time': time.time()
    }

def remove_user_craft_state(user_id):
    """Удаляет пользователя из состояния крафта"""
    if user_id in USER_CRAFT_STATES:
        del USER_CRAFT_STATES[user_id]

def is_user_in_craft_state(user_id):
    """Проверяет, находится ли пользователь в состоянии крафта"""
    return user_id in USER_CRAFT_STATES

def get_user_craft_target(user_id):
    """Получает карточку, которую пользователь пытается скрафтить"""
    if user_id in USER_CRAFT_STATES:
        return USER_CRAFT_STATES[user_id]['target_card']
    return None

# Декоратор для проверки бана
def check_ban(func):
    """Декоратор для проверки, забанен ли пользователь"""
    def wrapper(message):
        if message.date < BOT_START_TIME:
            return
            
        user_id = message.from_user.id
        
        if is_user_banned(user_id):
            ban_info = get_ban_info(user_id)
            if ban_info:
                username, reason, banned_by, banned_time = ban_info
                # Отправляем сообщение в ЛС пользователю
                try:
                    bot.send_message(user_id, 
                                   f"🚫 Вы забанены в боте!\n\n"
                                   f"📝 Причина: {reason}\n"
                                   f"⏰ Дата бана: {banned_time[:10]}\n\n"
                                   f"Если вы считаете, что это ошибка, свяжитесь с администратором.")
                except Exception as e:
                    logger.error(f"Не удалось отправить сообщение о бане пользователю {user_id}: {e}")
            return
            
        return func(message)
    return wrapper

# Декоратор для проверки бана в callback
def check_ban_callback(func):
    """Декоратор для проверки бана в callback"""
    def wrapper(call):
        user_id = call.from_user.id
        
        if is_user_banned(user_id):
            bot.answer_callback_query(call.id, "🚫 Вы забанены в боте!", show_alert=True)
            return
            
        return func(call)
    return wrapper



# ОСНОВНЫЕ КОМАНДЫ С ПРОВЕРКОЙ БАНА
@bot.message_handler(commands=['start'])
@check_ban
def start_command(message):
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name

    get_user(user_id, username)

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton('🎴 Получить карточку')
    btn2 = types.KeyboardButton('📊 Мой профиль')
    btn3 = types.KeyboardButton('📋 Мои карточки')
    btn4 = types.KeyboardButton('🛒 Магазин')
    btn5 = types.KeyboardButton('📚 Все карточки')
    btn6 = types.KeyboardButton('🔨 Крафт')
    markup.add(btn1, btn2, btn3, btn4)
    markup.add(btn5, btn6)

    welcome_text = f"""🐱 Добро пожаловать в мир карточек с котами, {username}!

✨ Доступные команды:
• 🎴 Получить карточку
• 📊 Мой профиль  
• 📋 Мои карточки
• 🛒 Магазин
• 📚 Все карточки
• 🔨 Крафт

🎁 Для получения бонусов зайдите в нашего бота @CardsCatsBot

💡 *Магазин работает только в личных сообщениях с ботом!*"""

    bot.send_message(message.chat.id, welcome_text, reply_markup=markup, parse_mode='Markdown')
    
@bot.message_handler(func=lambda message: message.text == '🎴 Получить карточку')
@check_ban
def get_card(message):
    user_id = message.from_user.id
    
    if not check_button_cooldown(user_id, 'get_card'):
        bot.send_message(message.chat.id, "⏳ Подождите немного перед следующим получением карточки!")
        return
    
    username = message.from_user.username or message.from_user.first_name
    get_user(user_id, username)
    
    conn = sqlite3.connect('cats.db')
    cursor = conn.cursor()
    cursor.execute('SELECT last_card_time FROM cooldowns WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    
    current_time = int(time.time())
    cooldown_seconds = 2 * 3600
    
    if result and (current_time - result[0]) < cooldown_seconds:
        time_left = cooldown_seconds - (current_time - result[0])
        hours = time_left // 3600
        minutes = (time_left % 3600) // 60
        bot.send_message(message.chat.id, f"⏰ Следующую карточку можно будет получить через: {hours}ч {minutes}м")
        conn.close()
        return
    
    card_name = get_random_card()
    card_data = CARDS_DATABASE[card_name]
    
    cursor.execute('UPDATE users SET coins = coins + ?, total_cards = total_cards + 1 WHERE user_id = ?',
                   (card_data["coins"], user_id))
    cursor.execute('INSERT OR REPLACE INTO cooldowns (user_id, last_card_time) VALUES (?, ?)',
                   (user_id, current_time))
    cursor.execute('INSERT INTO user_cards (user_id, rarity, card_name) VALUES (?, ?, ?)',
                   (user_id, card_data["rarity"], card_name))
    
    conn.commit()
    conn.close()
    
    card_text = f"""Вам выпала карточка!

🖼 Карточка: "{card_name}"
⭐️ Редкость: {card_data['rarity']} {RARITIES[card_data['rarity']]['name']}
💰 Монеты: +{card_data['coins']} монет 
📝 Описание: {card_data['description']}"""

    try:
        bot.send_photo(message.chat.id, card_data['image'], caption=card_text)
    except Exception as e:
        logger.error(f"Error sending photo: {e}")
        bot.send_message(message.chat.id, card_text)

@bot.message_handler(func=lambda message: message.text == '📊 Мой профиль')
@check_ban
def show_stats(message):
    user_id = message.from_user.id
    
    if not check_button_cooldown(user_id, 'profile'):
        bot.send_message(message.chat.id, "⏳ Подождите немного перед следующим просмотром профиля!")
        return
    
    conn = sqlite3.connect('cats.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT coins, total_cards FROM users WHERE user_id = ?', (user_id,))
    user_stats = cursor.fetchone()
    
    if not user_stats:
        bot.send_message(message.chat.id, "❌ Вы ещё не начали собирать карточки!")
        conn.close()
        return

    coins, total_cards = user_stats

    cursor.execute('''
        SELECT rarity, COUNT(*) as count 
        FROM user_cards 
        WHERE user_id = ? 
        GROUP BY rarity 
        ORDER BY count DESC
    ''', (user_id,))
    cards_by_rarity = cursor.fetchall()
    conn.close()

    stats_text = f"""📊 Ваша статистика:

💰 Монеты: {coins} монет
🎴 Всего карточек: {total_cards} шт.

📈 Коллекция по редкостям:"""

    for rarity, count in cards_by_rarity:
        rarity_name = RARITIES[rarity]["name"]
        stats_text += f"\n{rarity} {rarity_name}: {count} шт."

    bot.send_message(message.chat.id, stats_text)

@bot.message_handler(func=lambda message: message.text == '📋 Мои карточки')
@check_ban
def show_cards(message):
    user_id = message.from_user.id
    
    if not check_button_cooldown(user_id, 'my_cards'):
        bot.send_message(message.chat.id, "⏳ Подождите немного перед следующим просмотром карточек!")
        return
    
    conn = sqlite3.connect('cats.db')
    cursor = conn.cursor()

    cursor.execute('''
        SELECT rarity, card_name, obtained_date 
        FROM user_cards 
        WHERE user_id = ? 
        ORDER BY obtained_date DESC 
        LIMIT 20
    ''', (user_id,))
    cards = cursor.fetchall()
    conn.close()

    if not cards:
        bot.send_message(message.chat.id, "❌ У вас пока нет карточек!")
        return

    cards_text = "📋 Ваши последние карточки:\n\n"

    for i, (rarity, card_name, date) in enumerate(cards, 1):
        rarity_name = RARITIES[rarity]["name"]
        cards_text += f"{i}. {rarity} {card_name} ({rarity_name})\n"

    bot.send_message(message.chat.id, cards_text)

@bot.message_handler(func=lambda message: message.text == '🛒 Магазин')
@check_ban
def shop_menu(message):
    user_id = message.from_user.id
    
    # Проверяем, что это личные сообщения с ботом
    if message.chat.type != 'private':
        bot.send_message(message.chat.id, "❌ Магазин работает только в личных сообщениях с ботом! Напишите мне в ЛС.")
        return
    
    if not check_button_cooldown(user_id, 'shop'):
        bot.send_message(message.chat.id, "⏳ Подождите немного перед следующим действием в магазине!")
        return
    
    # Проверяем, включен ли магазин
    if not SHOP_ENABLED:
        bot.send_message(message.chat.id, "❌ Магазин временно отключен администратором!")
        return
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton('💰 Купить карточки')
    btn2 = types.KeyboardButton('💎 Продать карточки')
    btn3 = types.KeyboardButton('📋 Мои объявления')
    btn4 = types.KeyboardButton('🎴 Получить карточку')
    btn5 = types.KeyboardButton('📊 Мой профиль')
    markup.add(btn1, btn2, btn3)
    markup.add(btn4, btn5)

    shop_text = """🛒 Добро пожаловать в магазин карточек!

💰 **Купить карточки** - просмотреть карточки других игроков
💎 **Продать карточки** - выставить свои карточки на продажу
📋 **Мои объявления** - управление вашими продажами

⏰ *Внимание: процесс продажи отменяется через 20 секунд бездействия*"""

    bot.send_message(message.chat.id, shop_text, reply_markup=markup, parse_mode='Markdown')

@bot.message_handler(func=lambda message: message.text == '📚 Все карточки')
@check_ban
def all_cards_menu(message):
    user_id = message.from_user.id
    
    if not check_button_cooldown(user_id, 'all_cards'):
        bot.send_message(message.chat.id, "⏳ Подождите немного перед следующим просмотром!")
        return
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("📖 Просмотр всех карточек", callback_data="view_all_cards"))
    markup.add(types.InlineKeyboardButton("📊 Список моих карточек", callback_data="view_my_collection"))
    
    bot.send_message(message.chat.id, 
                    "📚 Выберите режим просмотра карточек:",
                    reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == '🔨 Крафт')
@check_ban
def craft_menu(message):
    user_id = message.from_user.id
    
    if not check_button_cooldown(user_id, 'craft'):
        bot.send_message(message.chat.id, "⏳ Подождите немного перед следующим действием!")
        return
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("📖 Просмотр рецептов крафта", callback_data="view_craft_recipes"))
    markup.add(types.InlineKeyboardButton("🔨 Создать карточку", callback_data="start_craft"))
    
    bot.send_message(message.chat.id,
                    "🔨 Мастерская крафта:\n\n"
                    "Здесь вы можете создавать уникальные карточки, объединяя другие карточки!",
                    reply_markup=markup)

# УЛУЧШЕННЫЕ ФУНКЦИИ МАГАЗИНА С ТАЙМАУТОМ 20 СЕКУНД
@bot.message_handler(func=lambda message: message.text == '💎 Продать карточки')
@check_ban
def sell_cards_menu(message):
    user_id = message.from_user.id
    
    # Проверяем, что это личные сообщения с ботом
    if message.chat.type != 'private':
        bot.send_message(message.chat.id, "❌ Магазин работает только в личных сообщениях с ботом! Напишите мне в ЛС.")
        return
    
    # Проверяем, включен ли магазин
    if not SHOP_ENABLED:
        bot.send_message(message.chat.id, "❌ Магазин временно отключен администратором!")
        return
    
    # Проверяем, не находится ли пользователь уже в процессе продажи
    if is_user_in_selling_state(user_id):
        bot.send_message(message.chat.id, "⏳ Вы уже находитесь в процессе продажи карточки! Завершите текущую продажу.")
        return
    
    if not check_button_cooldown(user_id, 'shop'):
        bot.send_message(message.chat.id, "⏳ Подождите немного перед следующим действием!")
        return
    
    conn = sqlite3.connect('cats.db')
    cursor = conn.cursor()

    cursor.execute('''
        SELECT uc.id, uc.card_name, uc.rarity 
        FROM user_cards uc 
        LEFT JOIN market m ON uc.id = m.card_id 
        WHERE uc.user_id = ? AND m.card_id IS NULL
        ORDER BY uc.obtained_date DESC
        LIMIT 20
    ''', (user_id,))

    cards = cursor.fetchall()
    conn.close()

    if not cards:
        bot.send_message(message.chat.id, "❌ У вас нет карточек для продажи!")
        return

    markup = types.InlineKeyboardMarkup()

    for card_id, card_name, rarity in cards:
        rarity_name = RARITIES[rarity]["name"]
        btn_text = f"{rarity} {card_name}"
        callback_data = f"sell_{card_id}"
        markup.add(types.InlineKeyboardButton(btn_text, callback_data=callback_data))

    markup.add(types.InlineKeyboardButton("❌ Отмена", callback_data="cancel_sell_menu"))

    sent_message = bot.send_message(message.chat.id, 
                                   "💎 Выберите карточку для продажи:\n\n⏰ *Процесс продажи автоматически отменится через 20 секунд бездействия*", 
                                   reply_markup=markup,
                                   parse_mode='Markdown')
    store_message_owner(sent_message.message_id, user_id)

# ОБРАБОТЧИК КНОПОК ДЛЯ ПРОСМОТРА КАРТОЧЕК И КРАФТА
@bot.callback_query_handler(func=lambda call: call.data.startswith(('view_', 'craft_', 'select_craft_card_')))
@check_ban_callback
def handle_view_callback(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id

    if not check_button_cooldown(user_id, 'all_cards'):
        bot.answer_callback_query(call.id, "⏳ Подождите немного перед следующим действием!", show_alert=True)
        return

    if call.data == 'view_all_cards':
        show_all_cards_page(call.message, user_id, 0)
        
    elif call.data == 'view_my_collection':
        show_user_collection_page(call.message, user_id, 0)
        
    elif call.data == 'view_craft_recipes':
        show_craft_recipes(call.message, user_id)
        
    elif call.data == 'start_craft':
        start_craft_selection(call.message, user_id)
        
    elif call.data.startswith('select_craft_card_'):
        card_name = call.data.split('_', 3)[3]
        process_craft_selection(call.message, user_id, card_name)
        
    elif call.data.startswith('page_all_'):
        page = int(call.data.split('_')[2])
        show_all_cards_page(call.message, user_id, page)
        
    elif call.data.startswith('page_my_'):
        page = int(call.data.split('_')[2])
        show_user_collection_page(call.message, user_id, page)
        
    elif call.data.startswith('craft_recipe_'):
        card_name = call.data.split('_', 2)[2]
        show_recipe_details(call.message, user_id, card_name)

    bot.answer_callback_query(call.id)

# ФУНКЦИИ ДЛЯ ПРОСМОТРА КАРТОЧЕК
def show_all_cards_page(message, user_id, page):
    cards_per_page = 10
    all_cards = list(CARDS_DATABASE.keys())
    total_pages = (len(all_cards) + cards_per_page - 1) // cards_per_page
    
    start_idx = page * cards_per_page
    end_idx = start_idx + cards_per_page
    page_cards = all_cards[start_idx:end_idx]
    
    conn = sqlite3.connect('cats.db')
    cursor = conn.cursor()
    
    text = f"📚 Все карточки (Страница {page + 1}/{total_pages}):\n\n"
    
    for i, card_name in enumerate(page_cards, start_idx + 1):
        card_data = CARDS_DATABASE[card_name]
        
        # Проверяем, есть ли карточка у пользователя
        cursor.execute('SELECT id FROM user_cards WHERE user_id = ? AND card_name = ?', (user_id, card_name))
        has_card = cursor.fetchone() is not None
        
        status = "✅" if has_card else "❌"
        craft_only = "🔨" if card_data.get('craft_only', False) else ""
        
        text += f"{status} {craft_only} {i}. {card_data['rarity']} {card_name}\n"
    
    conn.close()
    
    markup = types.InlineKeyboardMarkup()
    
    # Кнопки навигации
    nav_buttons = []
    if page > 0:
        nav_buttons.append(types.InlineKeyboardButton("⬅️ Назад", callback_data=f"page_all_{page-1}"))
    if page < total_pages - 1:
        nav_buttons.append(types.InlineKeyboardButton("Вперед ➡️", callback_data=f"page_all_{page+1}"))
    
    if nav_buttons:
        markup.row(*nav_buttons)
    
    try:
        bot.edit_message_text(text, message.chat.id, message.message_id, reply_markup=markup)
    except:
        bot.send_message(message.chat.id, text, reply_markup=markup)

def show_user_collection_page(message, user_id, page):
    cards_per_page = 10
    
    conn = sqlite3.connect('cats.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(DISTINCT card_name) FROM user_cards WHERE user_id = ?', (user_id,))
    total_user_cards = cursor.fetchone()[0]
    total_pages = (total_user_cards + cards_per_page - 1) // cards_per_page
    
    cursor.execute('''
        SELECT card_name, COUNT(*) as count 
        FROM user_cards 
        WHERE user_id = ? 
        GROUP BY card_name 
        ORDER BY card_name
        LIMIT ? OFFSET ?
    ''', (user_id, cards_per_page, page * cards_per_page))
    
    user_cards = cursor.fetchall()
    conn.close()
    
    text = f"📊 Моя коллекция (Страница {page + 1}/{total_pages}):\n\n"
    
    for card_name, count in user_cards:
        if card_name in CARDS_DATABASE:
            card_data = CARDS_DATABASE[card_name]
            craft_only = "🔨" if card_data.get('craft_only', False) else ""
            text += f"✅ {craft_only} {card_data['rarity']} {card_name} ×{count}\n"
        else:
            text += f"✅ {card_name} ×{count}\n"
    
    markup = types.InlineKeyboardMarkup()
    
    # Кнопки навигации
    nav_buttons = []
    if page > 0:
        nav_buttons.append(types.InlineKeyboardButton("⬅️ Назад", callback_data=f"page_my_{page-1}"))
    if page < total_pages - 1:
        nav_buttons.append(types.InlineKeyboardButton("Вперед ➡️", callback_data=f"page_my_{page+1}"))
    
    if nav_buttons:
        markup.row(*nav_buttons)
    
    try:
        bot.edit_message_text(text, message.chat.id, message.message_id, reply_markup=markup)
    except:
        bot.send_message(message.chat.id, text, reply_markup=markup)

# ФУНКЦИИ ДЛЯ КРАФТА
def show_craft_recipes(message, user_id):
    if not CRAFT_RECIPES:
        bot.send_message(message.chat.id, "❌ Пока нет доступных рецептов крафта!")
        return
    
    text = "🔨 Доступные рецепты крафта:\n\n"
    
    for result_card, recipe in CRAFT_RECIPES.items():
        if result_card in CARDS_DATABASE:
            card_data = CARDS_DATABASE[result_card]
            text += f"{card_data['rarity']} {result_card}:\n"
            
            for ingredient, amount in recipe['ingredients'].items():
                text += f"  - {ingredient} ×{amount}\n"
            text += "\n"
    
    markup = types.InlineKeyboardMarkup()
    for result_card in list(CRAFT_RECIPES.keys())[:10]:  # Ограничиваем количество кнопок
        if result_card in CARDS_DATABASE:
            card_data = CARDS_DATABASE[result_card]
            markup.add(types.InlineKeyboardButton(
                f"{card_data['rarity']} {result_card}", 
                callback_data=f"craft_recipe_{result_card}"
            ))
    
    sent_message = bot.send_message(message.chat.id, text, reply_markup=markup)
    store_message_owner(sent_message.message_id, user_id)

def show_recipe_details(message, user_id, card_name):
    if card_name not in CRAFT_RECIPES:
        bot.send_message(message.chat.id, "❌ Рецепт не найден!")
        return
    
    recipe = CRAFT_RECIPES[card_name]
    card_data = CARDS_DATABASE[card_name]
    
    text = f"🔨 Рецепт крафта:\n\n"
    text += f"🎯 Результат: {card_data['rarity']} {card_name}\n\n"
    text += "📦 Ингредиенты:\n"
    
    conn = sqlite3.connect('cats.db')
    cursor = conn.cursor()
    
    can_craft = True
    for ingredient, amount in recipe['ingredients'].items():
        cursor.execute('SELECT COUNT(*) FROM user_cards WHERE user_id = ? AND card_name = ?', 
                      (user_id, ingredient))
        user_has = cursor.fetchone()[0]
        status = "✅" if user_has >= amount else "❌"
        if user_has < amount:
            can_craft = False
        text += f"{status} {ingredient} ×{amount} (у вас: {user_has})\n"
    
    conn.close()
    
    markup = types.InlineKeyboardMarkup()
    if can_craft:
        markup.add(types.InlineKeyboardButton("🔨 Скрафтить", callback_data=f"select_craft_card_{card_name}"))
    markup.add(types.InlineKeyboardButton("⬅️ Назад", callback_data="view_craft_recipes"))
    
    try:
        bot.edit_message_text(text, message.chat.id, message.message_id, reply_markup=markup)
    except:
        bot.send_message(message.chat.id, text, reply_markup=markup)

def start_craft_selection(message, user_id):
    if not CRAFT_RECIPES:
        bot.send_message(message.chat.id, "❌ Пока нет доступных рецептов крафта!")
        return
    
    markup = types.InlineKeyboardMarkup()
    craftable_cards = []
    
    conn = sqlite3.connect('cats.db')
    cursor = conn.cursor()
    
    for result_card, recipe in CRAFT_RECIPES.items():
        if result_card in CARDS_DATABASE:
            can_craft = True
            for ingredient, amount in recipe['ingredients'].items():
                cursor.execute('SELECT COUNT(*) FROM user_cards WHERE user_id = ? AND card_name = ?', 
                              (user_id, ingredient))
                user_has = cursor.fetchone()[0]
                if user_has < amount:
                    can_craft = False
                    break
            
            if can_craft:
                craftable_cards.append(result_card)
    
    conn.close()
    
    if not craftable_cards:
        bot.send_message(message.chat.id, "❌ У вас нет необходимых карточек для крафта!")
        return
    
    for card_name in craftable_cards[:10]:  # Ограничиваем количество кнопок
        card_data = CARDS_DATABASE[card_name]
        markup.add(types.InlineKeyboardButton(
            f"{card_data['rarity']} {card_name}", 
            callback_data=f"select_craft_card_{card_name}"
        ))
    
    markup.add(types.InlineKeyboardButton("⬅️ Назад", callback_data="view_craft_recipes"))
    
    text = "🔨 Выберите карточку для крафта:\n\n*Доступные для крафта карточки:*"
    
    try:
        bot.edit_message_text(text, message.chat.id, message.message_id, reply_markup=markup)
    except:
        bot.send_message(message.chat.id, text, reply_markup=markup)

def process_craft_selection(message, user_id, card_name):
    if card_name not in CRAFT_RECIPES:
        bot.send_message(message.chat.id, "❌ Рецепт не найден!")
        return
    
    recipe = CRAFT_RECIPES[card_name]
    card_data = CARDS_DATABASE[card_name]
    
    conn = sqlite3.connect('cats.db')
    cursor = conn.cursor()
    
    # Проверяем, что у пользователя все еще есть необходимые карточки
    can_craft = True
    for ingredient, amount in recipe['ingredients'].items():
        cursor.execute('SELECT COUNT(*) FROM user_cards WHERE user_id = ? AND card_name = ?', 
                      (user_id, ingredient))
        user_has = cursor.fetchone()[0]
        if user_has < amount:
            can_craft = False
            break
    
    if not can_craft:
        bot.send_message(message.chat.id, "❌ У вас больше нет необходимых карточек для крафта!")
        conn.close()
        return
    
    # Удаляем карточки-ингредиенты
    for ingredient, amount in recipe['ingredients'].items():
        cursor.execute('''
            DELETE FROM user_cards 
            WHERE id IN (
                SELECT id FROM user_cards 
                WHERE user_id = ? AND card_name = ? 
                LIMIT ?
            )
        ''', (user_id, ingredient, amount))
    
    # Добавляем новую карточку
    cursor.execute('INSERT INTO user_cards (user_id, rarity, card_name) VALUES (?, ?, ?)',
                  (user_id, card_data["rarity"], card_name))
    cursor.execute('UPDATE users SET coins = coins + ?, total_cards = total_cards - ? + 1 WHERE user_id = ?',
                  (card_data["coins"], sum(recipe['ingredients'].values()), user_id))
    
    conn.commit()
    conn.close()
    
    success_text = f"""✅ Карточка успешно создана!

🎯 Результат: {card_data['rarity']} {card_name}
💰 Монеты: +{card_data['coins']} монет
📝 Описание: {card_data['description']}"""

    try:
        bot.send_photo(message.chat.id, card_data['image'], caption=success_text)
    except:
        bot.send_message(message.chat.id, success_text)
    
    # Возвращаемся к списку рецептов
    show_craft_recipes(message, user_id)
    

# НОВЫЕ КОМАНДЫ ДЛЯ ВЛАДЕЛЬЦЕВ - УПРАВЛЕНИЕ МАГАЗИНОМ
@bot.message_handler(commands=['offshop'])
def off_shop_command(message):
    if message.date < BOT_START_TIME:
        return
        
    user_id = message.from_user.id
    
    if not is_owner(user_id):
        bot.send_message(message.chat.id, "❌ У вас нет прав для использования этой команды!")
        return
    
    global SHOP_ENABLED
    if not SHOP_ENABLED:
        bot.send_message(message.chat.id, "❌ Магазин уже отключен!")
        return
    
    SHOP_ENABLED = False
    save_shop_status()
    
    bot.send_message(message.chat.id, "✅ Магазин отключен! Пользователи не могут покупать/продавать карточки.")

@bot.message_handler(commands=['onshop'])
def on_shop_command(message):
    if message.date < BOT_START_TIME:
        return
        
    user_id = message.from_user.id
    
    if not is_owner(user_id):
        bot.send_message(message.chat.id, "❌ У вас нет прав для использования этой команды!")
        return
    
    global SHOP_ENABLED
    if SHOP_ENABLED:
        bot.send_message(message.chat.id, "❌ Магазин уже включен!")
        return
    
    SHOP_ENABLED = True
    save_shop_status()
    
    bot.send_message(message.chat.id, "✅ Магазин включен! Пользователи снова могут покупать/продавать карточки.")

@bot.message_handler(commands=['shopstatus'])
def shop_status_command(message):
    if message.date < BOT_START_TIME:
        return
        
    user_id = message.from_user.id
    
    if not is_owner(user_id):
        bot.send_message(message.chat.id, "❌ У вас нет прав для использования этой команды!")
        return
    
    status = "🟢 ВКЛЮЧЕН" if SHOP_ENABLED else "🔴 ВЫКЛЮЧЕН"
    bot.send_message(message.chat.id, f"📊 Статус магазина: {status}")

# НОВЫЕ КОМАНДЫ ДЛЯ ВЛАДЕЛЬЦЕВ
@bot.message_handler(commands=['banbot'])
def ban_user_command(message):
    if message.date < BOT_START_TIME:
        return
        
    user_id = message.from_user.id
    
    if not is_owner(user_id):
        bot.send_message(message.chat.id, "❌ У вас нет прав для использования этой команды!")
        return
    
    try:
        parts = message.text.split(' ', 2)
        if len(parts) < 2:
            bot.send_message(message.chat.id, "❌ Используйте: /banbot @username [причина]")
            return
            
        username = parts[1].replace('@', '')
        reason = parts[2] if len(parts) > 2 else "Не указана"
        
        conn = sqlite3.connect('cats.db')
        cursor = conn.cursor()
        cursor.execute('SELECT user_id FROM users WHERE username = ?', (username,))
        target_user = cursor.fetchone()
        
        if not target_user:
            bot.send_message(message.chat.id, f"❌ Пользователь @{username} не найден!")
            conn.close()
            return
            
        target_user_id = target_user[0]
        
        # Проверяем, не забанен ли уже пользователь
        if is_user_banned(target_user_id):
            bot.send_message(message.chat.id, f"❌ Пользователь @{username} уже забанен!")
            conn.close()
            return
        
        # Добавляем в бан
        cursor.execute('INSERT INTO bans (user_id, username, reason, banned_by) VALUES (?, ?, ?, ?)',
                      (target_user_id, username, reason, user_id))
        
        conn.commit()
        conn.close()
        
        bot.send_message(message.chat.id, f"✅ Пользователь @{username} забанен в боте!\n📝 Причина: {reason}")
        
        try:
            bot.send_message(target_user_id, f"🚫 Вы были забанены в боте!\n📝 Причина: {reason}\n\nЕсли вы считаете, что это ошибка, свяжитесь с администратором.")
        except:
            pass
            
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Ошибка: {str(e)}")

@bot.message_handler(commands=['unbanbot'])
def unban_user_command(message):
    if message.date < BOT_START_TIME:
        return
        
    user_id = message.from_user.id
    
    if not is_owner(user_id):
        bot.send_message(message.chat.id, "❌ У вас нет прав для использования этой команды!")
        return
    
    try:
        parts = message.text.split()
        if len(parts) != 2:
            bot.send_message(message.chat.id, "❌ Используйте: /unbanbot @username")
            return
            
        username = parts[1].replace('@', '')
        
        conn = sqlite3.connect('cats.db')
        cursor = conn.cursor()
        cursor.execute('SELECT user_id FROM bans WHERE username = ?', (username,))
        banned_user = cursor.fetchone()
        
        if not banned_user:
            bot.send_message(message.chat.id, f"❌ Пользователь @{username} не найден в списке забаненных!")
            conn.close()
            return
            
        target_user_id = banned_user[0]
        
        # Удаляем из бана
        cursor.execute('DELETE FROM bans WHERE user_id = ?', (target_user_id,))
        
        conn.commit()
        conn.close()
        
        bot.send_message(message.chat.id, f"✅ Пользователь @{username} разбанен в боте!")
        
        try:
            bot.send_message(target_user_id, "🎉 Вы были разбанены в боте! Теперь вы снова можете использовать все функции.")
        except:
            pass
            
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Ошибка: {str(e)}")

# ОБНОВЛЕННАЯ КОМАНДА ADD_CARD С ВОПРОСОМ О КРАФТЕ
@bot.message_handler(commands=['addcard'])
def add_card_command(message):
    if message.date < BOT_START_TIME:
        return
        
    user_id = message.from_user.id
    
    if not is_owner(user_id):
        bot.send_message(message.chat.id, "❌ У вас нет прав для использования этой команды!")
        return
    
    CARD_ADD_STATES[user_id] = {"state": "waiting_card_image"}
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("📸 Отправить фото", callback_data="addcard_photo"))
    markup.add(types.InlineKeyboardButton("🔗 Ввести URL", callback_data="addcard_url"))
    
    bot.send_message(message.chat.id, 
                    "🖼 Как вы хотите добавить изображение для новой карточки?",
                    reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('addcard_'))
def process_add_card_method(call):
    user_id = call.from_user.id
    
    if not is_owner(user_id):
        bot.send_message(call.message.chat.id, "❌ У вас нет прав!")
        return
    
    method = call.data.split('_')[1]
    
    if method == "photo":
        CARD_ADD_STATES[user_id] = {"state": "waiting_card_photo"}
        bot.send_message(call.message.chat.id, "📸 Отправьте фото для новой карточки:")
        
    elif method == "url":
        CARD_ADD_STATES[user_id] = {"state": "waiting_card_url"}
        bot.send_message(call.message.chat.id, "🔗 Введите URL изображения для новой карточки:")
    
    bot.answer_callback_query(call.id)

@bot.message_handler(content_types=['photo'], 
                    func=lambda message: CARD_ADD_STATES.get(message.from_user.id, {}).get("state") == "waiting_card_photo")
def process_card_photo(message):
    if message.date < BOT_START_TIME:
        return
        
    user_id = message.from_user.id
    
    try:
        file_id = message.photo[-1].file_id
        file_info = bot.get_file(file_id)
        file_url = f"https://api.telegram.org/file/bot{bot.token}/{file_info.file_path}"
        
        CARD_ADD_STATES[user_id] = {
            "state": "waiting_card_name", 
            "photo_url": file_url
        }
        
        bot.send_message(message.chat.id, "📝 Теперь введите название карточки:")
        
    except Exception as e:
        logger.error(f"Error processing photo: {e}")
        bot.send_message(message.chat.id, "❌ Ошибка при обработке фото!")
        if user_id in CARD_ADD_STATES:
            del CARD_ADD_STATES[user_id]

@bot.message_handler(func=lambda message: CARD_ADD_STATES.get(message.from_user.id, {}).get("state") == "waiting_card_url")
def process_card_url(message):
    if message.date < BOT_START_TIME:
        return
        
    user_id = message.from_user.id
    url = message.text.strip()
    
    if not is_valid_url(url):
        bot.send_message(message.chat.id, "❌ Неверный URL! Убедитесь, что ссылка начинается с http:// или https://")
        return
    
    CARD_ADD_STATES[user_id] = {
        "state": "waiting_card_name", 
        "photo_url": url
    }
    
    bot.send_message(message.chat.id, "✅ URL принят! Теперь введите название карточки:")

@bot.message_handler(func=lambda message: CARD_ADD_STATES.get(message.from_user.id, {}).get("state") == "waiting_card_name")
def process_card_name(message):
    if message.date < BOT_START_TIME:
        return
        
    user_id = message.from_user.id
    state_data = CARD_ADD_STATES[user_id]
    card_name = message.text.strip()
    
    CARD_ADD_STATES[user_id] = {
        "state": "waiting_card_rarity",
        "photo_url": state_data["photo_url"],
        "card_name": card_name
    }
    
    markup = types.InlineKeyboardMarkup()
    for rarity in RARITIES.keys():
        markup.add(types.InlineKeyboardButton(
            f"{rarity} {RARITIES[rarity]['name']}", 
            callback_data=f"admin_rarity_{rarity}"
        ))
    
    bot.send_message(message.chat.id, 
                    "⭐️ Выберите редкость карточки:", 
                    reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('admin_rarity_'))
def process_admin_rarity(call):
    user_id = call.from_user.id
    rarity = call.data.split('_')[2]
    
    if user_id not in CARD_ADD_STATES or "state" not in CARD_ADD_STATES[user_id]:
        bot.send_message(call.message.chat.id, "❌ Сессия истекла, начните заново!")
        return
    
    state_data = CARD_ADD_STATES[user_id]
    card_name = state_data["card_name"]
    photo_url = state_data["photo_url"]
    
    CARD_ADD_STATES[user_id] = {
        "state": "waiting_card_coins",
        "photo_url": photo_url,
        "card_name": card_name,
        "rarity": rarity
    }
    
    bot.send_message(call.message.chat.id,
                    f"💰 Введите количество монет за карточку (по умолчанию для {rarity} {RARITIES[rarity]['name']}: {RARITIES[rarity]['coins']}):")
    
    bot.answer_callback_query(call.id)

@bot.message_handler(func=lambda message: CARD_ADD_STATES.get(message.from_user.id, {}).get("state") == "waiting_card_coins")
def process_card_coins(message):
    if message.date < BOT_START_TIME:
        return
        
    user_id = message.from_user.id
    state_data = CARD_ADD_STATES[user_id]
    
    try:
        coins = int(message.text.strip())
        if coins <= 0:
            bot.send_message(message.chat.id, "❌ Количество монет должно быть положительным!")
            return
        
        CARD_ADD_STATES[user_id] = {
            "state": "waiting_card_description",
            "photo_url": state_data["photo_url"],
            "card_name": state_data["card_name"],
            "rarity": state_data["rarity"],
            "coins": coins
        }
        
        bot.send_message(message.chat.id, "📝 Введите описание карточки:")
        
    except ValueError:
        bot.send_message(message.chat.id, "❌ Пожалуйста, введите корректное число!")

@bot.message_handler(func=lambda message: CARD_ADD_STATES.get(message.from_user.id, {}).get("state") == "waiting_card_description")
def process_card_description(message):
    if message.date < BOT_START_TIME:
        return
        
    user_id = message.from_user.id
    state_data = CARD_ADD_STATES[user_id]
    
    description = message.text.strip()
    
    CARD_ADD_STATES[user_id] = {
        "state": "waiting_craft_choice",
        "photo_url": state_data["photo_url"],
        "card_name": state_data["card_name"],
        "rarity": state_data["rarity"],
        "coins": state_data["coins"],
        "description": description
    }
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("✅ Да, добавить в крафт", callback_data="add_to_craft_yes"))
    markup.add(types.InlineKeyboardButton("❌ Нет, обычная карточка", callback_data="add_to_craft_no"))
    
    bot.send_message(message.chat.id,
                    "🔨 Добавить эту карточку в систему крафта?\n\n"
                    "Если да, то карточка будет доступна только через крафт и не будет выпадать обычным способом.",
                    reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('add_to_craft_'))
def process_craft_choice(call):
    user_id = call.from_user.id
    
    if not is_owner(user_id):
        bot.answer_callback_query(call.id, "❌ У вас нет прав!", show_alert=True)
        return
    
    if user_id not in CARD_ADD_STATES:
        bot.send_message(call.message.chat.id, "❌ Сессия истекла!")
        return
    
    state_data = CARD_ADD_STATES[user_id]
    choice = call.data.split('_')[3]
    
    craft_only = (choice == "yes")
    
    # Добавляем карточку в базу с сохранением
    card_name = state_data["card_name"]
    CARDS_DATABASE[card_name] = {
        "rarity": state_data["rarity"],
        "coins": state_data["coins"],
        "description": state_data["description"],
        "image": state_data["photo_url"],
        "craft_only": craft_only
    }
    
    # Сохраняем в файл
    save_cards_database()
    
    try:
        craft_status = "🔨 ТОЛЬКО КРАФТ" if craft_only else "🎴 ОБЫЧНАЯ"
        preview_text = f"""✅ Карточка успешно добавлена!

📝 Название: {card_name}
📝 Описание: {state_data['description']}
⭐️ Редкость: {state_data['rarity']} {RARITIES[state_data['rarity']]['name']}
💰 Стоимость: {state_data['coins']} монет
📋 Тип: {craft_status}"""
        
        bot.send_photo(call.message.chat.id, state_data["photo_url"], caption=preview_text)
        
        if craft_only:
            bot.send_message(call.message.chat.id,
                           "🔨 Теперь настройте рецепт крафта для этой карточки с помощью команды /addrecipe")
    
    except Exception as e:
        logger.error(f"Error sending photo preview: {e}")
        bot.send_message(call.message.chat.id, 
                       f"✅ Карточка '{card_name}' добавлена!\n"
                       f"📝 Описание: {state_data['description']}\n"
                       f"⭐️ Редкость: {state_data['rarity']} {RARITIES[state_data['rarity']]['name']}\n"
                       f"💰 Стоимость: {state_data['coins']} монет\n"
                       f"📋 Тип: {'🔨 ТОЛЬКО КРАФТ' if craft_only else '🎴 ОБЫЧНАЯ'}\n\n"
                       f"⚠️ Не удалось отправить превью изображения")
    
    del CARD_ADD_STATES[user_id]
    bot.answer_callback_query(call.id)

# КОМАНДЫ ДЛЯ УПРАВЛЕНИЯ КРАФТОМ
@bot.message_handler(commands=['addrecipe'])
def add_recipe_command(message):
    if message.date < BOT_START_TIME:
        return
        
    user_id = message.from_user.id
    
    if not is_owner(user_id):
        bot.send_message(message.chat.id, "❌ У вас нет прав для использования этой команды!")
        return
    
    # Показываем только карточки, которые помечены как craft_only
    craft_cards = [card for card, data in CARDS_DATABASE.items() if data.get('craft_only', False)]
    
    if not craft_cards:
        bot.send_message(message.chat.id, "❌ Нет карточек, доступных только через крафт!")
        return
    
    markup = types.InlineKeyboardMarkup()
    for card_name in craft_cards:
        rarity = CARDS_DATABASE[card_name]["rarity"]
        # Проверяем, есть ли уже рецепт для этой карточки
        has_recipe = "✅" if card_name in CRAFT_RECIPES else "❌"
        markup.add(types.InlineKeyboardButton(
            f"{has_recipe} {rarity} {card_name}", 
            callback_data=f"addrecipe_{card_name}"
        ))
    
    sent_message = bot.send_message(message.chat.id, 
                    "🔨 Выберите карточку для настройки рецепта крафта:",
                    reply_markup=markup)
    
    store_message_owner(sent_message.message_id, user_id)

@bot.callback_query_handler(func=lambda call: call.data.startswith('addrecipe_'))
def process_recipe_selection(call):
    user_id = call.from_user.id
    
    if not check_message_owner(call.message.message_id, user_id):
        bot.answer_callback_query(call.id, "❌ Это не ваше меню!", show_alert=True)
        return
    
    if not is_owner(user_id):
        bot.answer_callback_query(call.id, "❌ У вас нет прав!", show_alert=True)
        return
    
    card_name = call.data.split('_', 1)[1]
    
    # Сохраняем выбранную карточку для рецепта
    if 'recipe_states' not in globals():
        global recipe_states
        recipe_states = {}
    
    recipe_states[user_id] = {
        'target_card': card_name,
        'ingredients': {},
        'state': 'waiting_ingredient'
    }
    
    markup = types.InlineKeyboardMarkup()
    
    # Показываем все доступные карточки как возможные ингредиенты
    available_cards = list(CARDS_DATABASE.keys())
    cards_per_row = 2
    
    for i in range(0, len(available_cards), cards_per_row):
        row_cards = available_cards[i:i + cards_per_row]
        row_buttons = []
        for card in row_cards:
            rarity = CARDS_DATABASE[card]["rarity"]
            btn_text = f"{rarity} {card[:15]}..." if len(card) > 15 else f"{rarity} {card}"
            row_buttons.append(types.InlineKeyboardButton(btn_text, callback_data=f"addingredient_{card}"))
        markup.row(*row_buttons)
    
    markup.add(types.InlineKeyboardButton("✅ Завершить настройку рецепта", callback_data="finish_recipe"))
    
    bot.send_message(call.message.chat.id,
                    f"🔨 Настройка рецепта для: {CARDS_DATABASE[card_name]['rarity']} {card_name}\n\n"
                    f"Выберите карточки-ингредиенты для крафта:",
                    reply_markup=markup)
    
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data.startswith('addingredient_'))
def process_ingredient_selection(call):
    user_id = call.from_user.id
    
    if not check_message_owner(call.message.message_id, user_id):
        bot.answer_callback_query(call.id, "❌ Это не ваше меню!", show_alert=True)
        return
    
    if user_id not in recipe_states:
        bot.send_message(call.message.chat.id, "❌ Сессия истекла!")
        return
    
    ingredient_card = call.data.split('_', 1)[1]
    
    # Сохраняем текущий ингредиент
    recipe_states[user_id]['current_ingredient'] = ingredient_card
    recipe_states[user_id]['state'] = 'waiting_quantity'
    
    bot.send_message(call.message.chat.id,
                    f"🔢 Введите количество карточек '{ingredient_card}' для рецепта:")
    
    bot.answer_callback_query(call.id)

@bot.message_handler(func=lambda message: recipe_states.get(message.from_user.id, {}).get('state') == 'waiting_quantity')
def process_ingredient_quantity(message):
    if message.date < BOT_START_TIME:
        return
        
    user_id = message.from_user.id
    
    if user_id not in recipe_states:
        bot.send_message(message.chat.id, "❌ Сессия истекла!")
        return
    
    try:
        quantity = int(message.text.strip())
        if quantity <= 0:
            bot.send_message(message.chat.id, "❌ Количество должно быть положительным!")
            return
        
        state = recipe_states[user_id]
        ingredient_card = state['current_ingredient']
        state['ingredients'][ingredient_card] = quantity
        
        # Показываем текущий прогресс
        progress_text = f"🔨 Текущий рецепт для: {CARDS_DATABASE[state['target_card']]['rarity']} {state['target_card']}\n\n"
        progress_text += "📦 Ингредиенты:\n"
        
        for ing, qty in state['ingredients'].items():
            progress_text += f"  - {ing} ×{qty}\n"
        
        markup = types.InlineKeyboardMarkup()
        available_cards = list(CARDS_DATABASE.keys())
        cards_per_row = 2
        
        for i in range(0, len(available_cards), cards_per_row):
            row_cards = available_cards[i:i + cards_per_row]
            row_buttons = []
            for card in row_cards:
                rarity = CARDS_DATABASE[card]["rarity"]
                btn_text = f"{rarity} {card[:15]}..." if len(card) > 15 else f"{rarity} {card}"
                row_buttons.append(types.InlineKeyboardButton(btn_text, callback_data=f"addingredient_{card}"))
            markup.row(*row_buttons)
        
        markup.add(types.InlineKeyboardButton("✅ Завершить настройку рецепта", callback_data="finish_recipe"))
        
        bot.send_message(message.chat.id, progress_text, reply_markup=markup)
        
        # Возвращаемся в состояние выбора ингредиентов
        recipe_states[user_id]['state'] = 'waiting_ingredient'
        
    except ValueError:
        bot.send_message(message.chat.id, "❌ Пожалуйста, введите корректное число!")

@bot.callback_query_handler(func=lambda call: call.data == 'finish_recipe')
def finish_recipe_setup(call):
    user_id = call.from_user.id
    
    if not check_message_owner(call.message.message_id, user_id):
        bot.answer_callback_query(call.id, "❌ Это не ваше меню!", show_alert=True)
        return
    
    if user_id not in recipe_states:
        bot.send_message(call.message.chat.id, "❌ Сессия истекла!")
        return
    
    state = recipe_states[user_id]
    
    if not state['ingredients']:
        bot.send_message(call.message.chat.id, "❌ Рецепт не может быть пустым!")
        return
    
    # Сохраняем рецепт
    CRAFT_RECIPES[state['target_card']] = {
        'ingredients': state['ingredients']
    }
    
    save_craft_recipes()
    
    # Показываем итоговый рецепт
    result_text = f"""✅ Рецепт крафта сохранен!

🎯 Результат: {CARDS_DATABASE[state['target_card']]['rarity']} {state['target_card']}

📦 Ингредиенты:"""
    
    for ingredient, quantity in state['ingredients'].items():
        result_text += f"\n  - {ingredient} ×{quantity}"
    
    bot.send_message(call.message.chat.id, result_text)
    
    # Очищаем состояние
    del recipe_states[user_id]
    bot.answer_callback_query(call.id)

@bot.message_handler(commands=['deleterecipe'])
def delete_recipe_command(message):
    if message.date < BOT_START_TIME:
        return
        
    user_id = message.from_user.id
    
    if not is_owner(user_id):
        bot.send_message(message.chat.id, "❌ У вас нет прав для использования этой команды!")
        return
    
    if not CRAFT_RECIPES:
        bot.send_message(message.chat.id, "❌ Нет сохраненных рецептов!")
        return
    
    markup = types.InlineKeyboardMarkup()
    for card_name in CRAFT_RECIPES.keys():
        if card_name in CARDS_DATABASE:
            rarity = CARDS_DATABASE[card_name]["rarity"]
            markup.add(types.InlineKeyboardButton(
                f"{rarity} {card_name}", 
                callback_data=f"deleterecipe_{card_name}"
            ))
    
    sent_message = bot.send_message(message.chat.id, 
                    "🗑 Выберите рецепт для удаления:",
                    reply_markup=markup)
    
    store_message_owner(sent_message.message_id, user_id)

@bot.callback_query_handler(func=lambda call: call.data.startswith('deleterecipe_'))
def process_delete_recipe(call):
    user_id = call.from_user.id
    
    if not check_message_owner(call.message.message_id, user_id):
        bot.answer_callback_query(call.id, "❌ Это не ваше меню!", show_alert=True)
        return
    
    if not is_owner(user_id):
        bot.answer_callback_query(call.id, "❌ У вас нет прав!", show_alert=True)
        return
    
    card_name = call.data.split('_', 1)[1]
    
    if card_name in CRAFT_RECIPES:
        del CRAFT_RECIPES[card_name]
        save_craft_recipes()
        bot.send_message(call.message.chat.id, f"✅ Рецепт для '{card_name}' удален!")
    else:
        bot.send_message(call.message.chat.id, f"❌ Рецепт для '{card_name}' не найден!")
    
    bot.answer_callback_query(call.id)

@bot.message_handler(commands=['recipes'])
def list_recipes_command(message):
    if message.date < BOT_START_TIME:
        return
        
    user_id = message.from_user.id
    
    if not is_owner(user_id):
        bot.send_message(message.chat.id, "❌ У вас нет прав для использования этой команды!")
        return
    
    if not CRAFT_RECIPES:
        bot.send_message(message.chat.id, "❌ Нет сохраненных рецептов!")
        return
    
    text = "📋 Список всех рецептов крафта:\n\n"
    
    for result_card, recipe in CRAFT_RECIPES.items():
        if result_card in CARDS_DATABASE:
            card_data = CARDS_DATABASE[result_card]
            text += f"{card_data['rarity']} {result_card}:\n"
            
            for ingredient, amount in recipe['ingredients'].items():
                text += f"  - {ingredient} ×{amount}\n"
            text += "\n"
    
    bot.send_message(message.chat.id, text)
    

# УЛУЧШЕННЫЙ ОБРАБОТЧИК КНОПОК МАГАЗИНА С ТАЙМАУТОМ 20 СЕКУНД
@bot.callback_query_handler(func=lambda call: call.data.startswith(('sell_', 'buy_', 'remove_', 'confirm_', 'cancel_', 'cancel_sell')))
@check_ban_callback
def handle_shop_callback(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id

    # Проверяем, включен ли магазин для всех операций кроме удаления объявлений
    if not call.data.startswith('remove_') and not SHOP_ENABLED:
        bot.answer_callback_query(call.id, "❌ Магазин временно отключен администратором!", show_alert=True)
        return

    if not check_message_owner(call.message.message_id, user_id):
        bot.answer_callback_query(call.id, "❌ Это не ваше меню!", show_alert=True)
        return

    if not check_button_cooldown(user_id, 'shop'):
        bot.answer_callback_query(call.id, "⏳ Подождите немного перед следующим действием!", show_alert=True)
        return

    if call.data.startswith('sell_'):
        card_id = int(call.data.split('_')[1])
        
        # Проверяем, не выбрана ли уже эта карточка
        if check_active_selection(user_id, card_id, 'sell'):
            bot.answer_callback_query(call.id, "❌ Вы уже выбрали эту карточку! Выберите другую.", show_alert=True)
            return
            
        # ПРОВЕРКА: Не выставлена ли карточка уже на продажу
        if is_card_already_selling(user_id, card_id):
            bot.answer_callback_query(call.id, "❌ Вы уже продаёте эту карточку!", show_alert=True)
            return
            
        conn = sqlite3.connect('cats.db')
        cursor = conn.cursor()
        cursor.execute('SELECT user_id FROM user_cards WHERE id = ?', (card_id,))
        card_owner = cursor.fetchone()
        conn.close()
        
        if not card_owner or card_owner[0] != user_id:
            bot.answer_callback_query(call.id, "❌ Эта карточка вам не принадлежит!", show_alert=True)
            return
        
        # Добавляем в активные выборы
        add_active_selection(user_id, card_id, 'sell')
        # Добавляем в состояние продажи
        add_card_selling_state(user_id, card_id)
        # Добавляем пользователя в состояние продажи
        add_user_selling_state(user_id, card_id)
        # Добавляем пользователя в состояние ввода цены
        add_user_price_input_state(user_id, card_id)
        
        # Удаляем сообщение с выбором карточек
        try:
            bot.delete_message(chat_id, call.message.message_id)
        except:
            pass
            
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("❌ Отменить продажу", callback_data="cancel_sell_process"))
        
        msg = bot.send_message(chat_id, 
                              "💵 Введите цену продажи (в монетах):\n\n⏰ *Процесс продажи автоматически отменится через 20 секунд бездействия*", 
                              reply_markup=markup,
                              parse_mode='Markdown')
        bot.register_next_step_handler(msg, process_sell_price, card_id, user_id)

    elif call.data == 'cancel_sell_menu':
        # Отмена в меню выбора карточки
        bot.edit_message_text("❌ Процесс продажи отменен.", chat_id, call.message.message_id)
        remove_active_selection(user_id, 'sell')
        
    elif call.data == 'cancel_sell_process':
        # Отмена в процессе ввода цены
        bot.send_message(chat_id, "❌ Процесс продажи отменен.")
        remove_active_selection(user_id, 'sell')
        remove_card_selling_state(user_id, get_user_selling_card(user_id))
        remove_user_selling_state(user_id)
        remove_user_price_input_state(user_id)
        
    elif call.data.startswith('buy_'):
        market_id = int(call.data.split('_')[1])
        
        # Проверяем, не выбрана ли уже эта карточка для покупки
        if check_active_selection(user_id, market_id, 'buy'):
            bot.answer_callback_query(call.id, "❌ Вы уже выбирали эту карточку! Выберите другую.", show_alert=True)
            return
            
        # Добавляем в активные выборы
        add_active_selection(user_id, market_id, 'buy')
        
        buy_card_confirmation(chat_id, market_id, user_id, call.message.message_id)

    elif call.data.startswith('remove_'):
        market_id = int(call.data.split('_')[1])
        
        conn = sqlite3.connect('cats.db')
        cursor = conn.cursor()
        cursor.execute('SELECT seller_id, card_id FROM market WHERE id = ?', (market_id,))
        listing_info = cursor.fetchone()
        conn.close()
        
        if not listing_info or listing_info[0] != user_id:
            bot.answer_callback_query(call.id, "❌ Это объявление вам не принадлежит!", show_alert=True)
            return
            
        seller_id, card_id = listing_info
        remove_from_market(market_id, user_id)
        # Удаляем из состояния продажи
        remove_card_selling_state(user_id, card_id)
        bot.edit_message_text("✅ Объявление удалено!", chat_id, call.message.message_id)

    elif call.data.startswith('confirm_buy_'):
        market_id = int(call.data.split('_')[2])
        process_buy_card(chat_id, market_id, user_id, call.message.message_id)

    elif call.data == 'cancel_buy':
        # Удаляем из активных выборов при отмене
        remove_active_selection(user_id, 'buy')
        bot.edit_message_text("❌ Покупка отменена.", chat_id, call.message.message_id)

    bot.answer_callback_query(call.id)

# УЛУЧШЕННАЯ ФУНКЦИЯ ОБРАБОТКИ ЦЕНЫ С ТАЙМАУТОМ 20 СЕКУНД
def process_sell_price(message, card_id, user_id):
    if message.date < BOT_START_TIME:
        return
        
    # ПРОВЕРКА: Только тот пользователь, который начал продажу, может вводить цену
    if message.from_user.id != user_id:
        bot.send_message(message.chat.id, "❌ Это не ваш процесс продажи!")
        return
        
    # Проверяем бан
    if is_user_banned(user_id):
        bot.send_message(message.chat.id, "🚫 Вы забанены в боте!")
        cleanup_selling_states(user_id, card_id)
        return
        
    # Проверяем, включен ли магазин
    if not SHOP_ENABLED:
        bot.send_message(message.chat.id, "❌ Магазин временно отключен администратором!")
        cleanup_selling_states(user_id, card_id)
        return
        
    # Проверяем, что пользователь все еще находится в состоянии ввода цены для этой карточки
    if not is_user_in_price_input_state(user_id) or get_user_price_input_card(user_id) != card_id:
        bot.send_message(message.chat.id, "❌ Сессия продажи истекла. Начните заново.")
        cleanup_selling_states(user_id, card_id)
        return
        
    # Проверяем таймаут (20 секунд)
    if user_id in USER_PRICE_INPUT_STATES:
        start_time = USER_PRICE_INPUT_STATES[user_id]['start_time']
        if time.time() - start_time > 20:
            bot.send_message(message.chat.id, "❌ Время на ввод цены истекло. Начните продажу заново.")
            cleanup_selling_states(user_id, card_id)
            return
    
    try:
        # Проверяем, что сообщение содержит текст (цену), а не медиа
        if not message.text:
            bot.send_message(message.chat.id, "❌ Пожалуйста, введите цену числом, а не отправляйте медиафайлы!")
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("❌ Отменить продажу", callback_data="cancel_sell_process"))
            msg = bot.send_message(message.chat.id, 
                                  "💵 Введите цену продажи (в монетах):\n\n⏰ *Процесс продажи автоматически отменится через 20 секунд бездействия*", 
                                  reply_markup=markup,
                                  parse_mode='Markdown')
            bot.register_next_step_handler(msg, process_sell_price, card_id, user_id)
            return
            
        price = int(message.text)
        if price <= 0:
            bot.send_message(message.chat.id, "❌ Цена должна быть положительным числом! Попробуйте снова:")
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("❌ Отменить продажу", callback_data="cancel_sell_process"))
            msg = bot.send_message(message.chat.id, 
                                  "💵 Введите цену продажи (в монетах):\n\n⏰ *Процесс продажи автоматически отменится через 20 секунд бездействия*", 
                                  reply_markup=markup,
                                  parse_mode='Markdown')
            bot.register_next_step_handler(msg, process_sell_price, card_id, user_id)
            return

        conn = sqlite3.connect('cats.db')
        cursor = conn.cursor()
        cursor.execute('SELECT card_name, rarity FROM user_cards WHERE id = ?', (card_id,))
        card_info = cursor.fetchone()
        conn.close()

        if card_info:
            card_name, rarity = card_info
            add_card_to_market(user_id, card_id, price)
            # Очищаем состояния после успешной продажи
            cleanup_selling_states(user_id, card_id)
            
            bot.send_message(message.chat.id,
                             f"✅ Карточка выставлена на продажу!\n\n"
                             f"🖼 {rarity} {card_name}\n"
                             f"💰 Цена: {price} монет")

    except ValueError:
        bot.send_message(message.chat.id, "❌ Пожалуйста, введите корректное число! Попробуйте снова:")
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("❌ Отменить продажу", callback_data="cancel_sell_process"))
        msg = bot.send_message(message.chat.id, 
                              "💵 Введите цену продажи (в монетах):\n\n⏰ *Процесс продажи автоматически отменится через 20 секунд бездействия*", 
                              reply_markup=markup,
                              parse_mode='Markdown')
        bot.register_next_step_handler(msg, process_sell_price, card_id, user_id)

# ФУНКЦИЯ ДЛЯ ОЧИСТКИ СОСТОЯНИЙ ПРОДАЖИ
def cleanup_selling_states(user_id, card_id):
    """Очищает все состояния, связанные с продажей карточки"""
    remove_active_selection(user_id, 'sell')
    remove_card_selling_state(user_id, card_id)
    remove_user_selling_state(user_id)
    remove_user_price_input_state(user_id)

def buy_card_confirmation(chat_id, market_id, buyer_id, message_id):
    conn = sqlite3.connect('cats.db')
    cursor = conn.cursor()

    cursor.execute('''
        SELECT uc.card_name, uc.rarity, m.price, u.username, u.user_id 
        FROM market m
        JOIN user_cards uc ON m.card_id = uc.id
        JOIN users u ON m.seller_id = u.user_id
        WHERE m.id = ?
    ''', (market_id,))

    card_info = cursor.fetchone()
    conn.close()

    if not card_info:
        bot.send_message(chat_id, "❌ Карточка уже продана или удалена!")
        remove_active_selection(buyer_id, 'buy')
        return

    card_name, rarity, price, seller_name, seller_id = card_info

    if buyer_id == seller_id:
        bot.send_message(chat_id, "❌ Нельзя купить свою же карточку!")
        remove_active_selection(buyer_id, 'buy')
        return

    conn = sqlite3.connect('cats.db')
    cursor = conn.cursor()
    cursor.execute('SELECT coins FROM users WHERE user_id = ?', (buyer_id,))
    buyer_balance = cursor.fetchone()
    conn.close()

    if not buyer_balance or buyer_balance[0] < price:
        bot.send_message(chat_id, f"❌ Недостаточно монет для покупки! Нужно: {price} монет")
        remove_active_selection(buyer_id, 'buy')
        return

    markup = types.InlineKeyboardMarkup()
    markup.row(
        types.InlineKeyboardButton("✅ Купить", callback_data=f"confirm_buy_{market_id}"),
        types.InlineKeyboardButton("❌ Отмена", callback_data="cancel_buy")
    )

    sent_message = bot.send_message(chat_id,
                     f"🛒 Подтверждение покупки:\n\n"
                     f"🖼 Карточка: {rarity} {card_name}\n"
                     f"💰 Цена: {price} монет\n"
                     f"👤 Продавец: @{seller_name}\n"
                     f"💳 Ваш баланс: {buyer_balance[0]} монет",
                     reply_markup=markup)
    
    store_message_owner(sent_message.message_id, buyer_id)

def process_buy_card(chat_id, market_id, buyer_id, message_id):
    sale_info, result_message = buy_card(market_id, buyer_id)

    if sale_info:
        card_id, seller_id, price, card_name, rarity = sale_info
        success_text = f"✅ Покупка успешно завершена!\n\n🖼 Карточка: {rarity} {card_name}\n💰 Цена: {price} монет"
        bot.edit_message_text(success_text, chat_id, message_id)

        try:
            seller_text = f"💰 Ваша карточка продана!\n\n🖼 Карточка: {rarity} {card_name}\n💰 Получено: {price} монет"
            bot.send_message(seller_id, seller_text)
        except:
            pass
    else:
        bot.edit_message_text(f"❌ {result_message}", chat_id, message_id)
    
    # Удаляем из активных выборов после завершения покупки
    remove_active_selection(buyer_id, 'buy')

# ФУНКЦИИ ДЛЯ МАГАЗИНА
def add_card_to_market(seller_id, card_id, price):
    conn = sqlite3.connect('cats.db')
    cursor = conn.cursor()

    cursor.execute('INSERT INTO market (seller_id, card_id, price) VALUES (?, ?, ?)',
                   (seller_id, card_id, price))
    conn.commit()
    conn.close()

def remove_from_market(market_id, user_id):
    conn = sqlite3.connect('cats.db')
    cursor = conn.cursor()

    cursor.execute('DELETE FROM market WHERE id = ? AND seller_id = ?', (market_id, user_id))
    conn.commit()
    conn.close()

def buy_card(market_id, buyer_id):
    conn = sqlite3.connect('cats.db')
    cursor = conn.cursor()

    try:
        cursor.execute('''
            SELECT m.card_id, m.seller_id, m.price, uc.card_name, uc.rarity 
            FROM market m
            JOIN user_cards uc ON m.card_id = uc.id
            WHERE m.id = ?
        ''', (market_id,))
        sale_info = cursor.fetchone()

        if not sale_info:
            return None, "Карточка не найдена в магазине"

        card_id, seller_id, price, card_name, rarity = sale_info

        cursor.execute('SELECT coins FROM users WHERE user_id = ?', (buyer_id,))
        buyer_coins = cursor.fetchone()

        if not buyer_coins or buyer_coins[0] < price:
            return None, "Недостаточно монет для покупки"

        if buyer_id == seller_id:
            return None, "Нельзя купить свою же карточку"

        cursor.execute('UPDATE users SET coins = coins - ? WHERE user_id = ?', (price, buyer_id))
        cursor.execute('UPDATE users SET coins = coins + ? WHERE user_id = ?', (price, seller_id))
        cursor.execute('UPDATE user_cards SET user_id = ? WHERE id = ?', (buyer_id, card_id))
        cursor.execute('DELETE FROM market WHERE id = ?', (market_id,))

        # Удаляем из состояния продажи после успешной продажи
        remove_card_selling_state(seller_id, card_id)

        conn.commit()
        return sale_info, "Успешная покупка"

    except Exception as e:
        conn.rollback()
        return None, f"Ошибка при покупке: {str(e)}"
    finally:
        conn.close()

import sqlite3
import telebot
from telebot import types
import time
import random
import logging
from datetime import datetime
import re
import json
import os

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

bot = telebot.TeleBot('8205728685:AAEX0xtuHGthCb4ZYy0i18CqA8DGymkNtPs')

# Время запуска бота (для игнорирования старых сообщений)
BOT_START_TIME = time.time()

# Файлы для сохранения данных
CARDS_DB_FILE = 'cards_database.json'
HIDDEN_CARDS_FILE = 'hidden_cards.json'
SHOP_STATUS_FILE = 'shop_status.json'
CRAFT_RECIPES_FILE = 'craft_recipes.json'

# Сначала определяем переменные как глобальные
CARDS_DATABASE = {}
HIDDEN_CARDS = set()
SHOP_ENABLED = True  # По умолчанию магазин включен
CRAFT_RECIPES = {}  # Рецепты крафта

# Редкости карточек и их стоимости
RARITIES = {
    "🟤": {"name": "Обычная", "coins": 1, "chance": 30},
    "⚪️": {"name": "Необычная", "coins": 3, "chance": 25},
    "🟢": {"name": "Редкая", "coins": 5, "chance": 20},
    "🟠": {"name": "Супер редкая", "coins": 7, "chance": 10},
    "🟣": {"name": "Эпическая", "coins": 10, "chance": 8},
    "🟡": {"name": "Легендарная", "coins": 50, "chance": 4},
    "🔴": {"name": "Мифическая", "coins": 70, "chance": 2},
    "💎": {"name": "Алмазная", "coins": 100, "chance": 0.5},
    "👑": {"name": "Божественная", "coins": 500, "chance": 0.3},
    "❔": {"name": "Секретная", "coins": 1000, "chance": 0.2},
    "🖥️": {"name": "Админская", "coins": 1777, "chance": 0}
}

# Инициализация базы карточек по умолчанию
DEFAULT_CARDS = {
    "Инвертированный Симба": {
        "rarity": "⚪️",
        "coins": 3,
        "description": "Кот инвертированный в противоположные цвета.",
        "image": "https://sprutio.beget.com/image_cache/gagarin7/alexa3j5/3627c1357b3564d8ad82e3543d7c0513/inverssimba.jpg",
        "craft_only": False
    },
    "Grow а Симба, Steal a Алиса": {
        "rarity": "🟣",
        "coins": 10,
        "description": "Коты попали в роблокс игры!",
        "image": "https://sprutio.beget.com/image_cache/gagarin7/alexa3j5/0be979231af670f1c11e76996a1385ac/growandstealsimba.jpg",
        "craft_only": False
    },
    "Лайнер": {
        "rarity": "🖥️",
        "coins": 1777,
        "description": "Это лайнер. Ну да, лучшая карточка в боте, что такого? Вам просто повезло, ничего особенного.",
        "image": "https://sprutio.beget.com/image_cache/gagarin7/alexa3j5/028e0013f79f399c59713d06789c0a89/liner.jpg",
        "craft_only": False
    },
    "Симба на миссии": {
        "rarity": "👑",
        "coins": 500,
        "description": "Кот-агент 😎",
        "image": "https://sprutio.beget.com/image_cache/gagarin7/alexa3j5/9b6889f07b9329cee41340fb0664b766/simbainmission.jpg",
        "craft_only": False
    },
    "Симба грабитель": {
        "rarity": "⚪️",
        "coins": 3,
        "description": "Ии ультануло. Кот грабитель.",
        "image": "https://sprutio.beget.com/image_cache/gagarin7/alexa3j5/ecce48ba328c1250f640150053944a10/simbarobber.jpg",
        "craft_only": False
    },
    "Симба удивлён": {
        "rarity": "⚪️",
        "coins": 3,
        "description": "Просто удивлённый кот, скорее всего он увидел мотылька.",
        "image": "https://sprutio.beget.com/image_cache/gagarin7/alexa3j5/b3e302e21aeeb6adcec0245d9c13ed18/simbawow.jpg",
        "craft_only": False
    },
    "Симба злой король": {
        "rarity": "🔴",
        "coins": 70,
        "description": "Кот который выглядит жутковато..",
        "image": "https://sprutio.beget.com/image_cache/gagarin7/alexa3j5/81733e770f94b9e8a65ff5567341e673/simbaking.jpg",
        "craft_only": False
    },
    "Симбакула": {
        "rarity": "🟢",
        "coins": 5,
        "description": "Рыба?.. АКУЛА! А, это всё таки кот..",
        "image": "https://sprutio.beget.com/image_cache/gagarin7/alexa3j5/df2807cffe2f3cd124aadab2f6d76884/simbashark.jpg",
        "craft_only": False
    },
    "Симба с Алисой на окне": {
        "rarity": "🟠",
        "coins": 7,
        "description": "Две кошки вместе.",
        "image": "https://sprutio.beget.com/image_cache/gagarin7/alexa3j5/25330c0dee36510e4fc593b76dc9eb79/simbawithalisa.jph.jpg",
        "craft_only": False
    },
    "Симба лежит на земле": {
        "rarity": "🟣",
        "coins": 10,
        "description": "Кот который охотится на птиц в кормушке.",
        "image": "https://sprutio.beget.com/image_cache/gagarin7/alexa3j5/d353493d5bc7c6ae849b03c935dc6fd8/simbasitingrass.jpg",
        "craft_only": False
    },
    "Симба-клоун": {
        "rarity": "🔴",
        "coins": 100,
        "description": "Кот-клоун. Буквально каждый из нас похож на него.",
        "image": "https://sprutio.beget.com/image_cache/gagarin7/alexa3j5/39d1c6d31d9adace2338f12e74fd3364/clownsimba.jpg",
        "craft_only": False
    },
    "Симба полицейский": {
        "rarity": "🟡",
        "coins": 50,
        "description": "Кот-полицейский, настоящий страж порядка!",
        "image": "https://sprutio.beget.com/image_cache/gagarin7/alexa3j5/26132586be78a56dbb0cd51c4a5c3696/simbapolice.jpg",
        "craft_only": False
    },
    "Симба с рыбкой": {
        "rarity": "🟤",
        "coins": 1,
        "description": "Кот с пластиковой рыбкой.",
        "image": "https://sprutio.beget.com/image_cache/gagarin7/alexa3j5/c7568dfac2c49ca6335e493e2bb8a597/simbawithfish.jpg",
        "craft_only": False
    },
    "Алиса-убийца": {
        "rarity": "🟣",
        "coins": 10,
        "description": "Кошка с острым ножом.",
        "image": "https://sprutio.beget.com/image_cache/gagarin7/alexa3j5/7f8a704aa7184492f6a0ea57e2246410/alicekiller.jpg",
        "craft_only": False
    },
    "Злая и Добрая Алиса": {
        "rarity": "🔴",
        "coins": 70,
        "description": "Две светящиеся кошки. Вроде бы они одинаковые, а вроде и нет..",
        "image": "https://sprutio.beget.com/image_cache/gagarin7/alexa3j5/71b056bc6b7f24f4dbc7e436f63d511d/godandevilsimba.jpg",
        "craft_only": False
    },
    "Пиксельная Алиса": {
        "rarity": "🟠",
        "coins": 7,
        "description": "Кошка немножко пиксель.",
        "image": "https://sprutio.beget.com/image_cache/gagarin7/alexa3j5/fe260aa01b4a3fd3567ad30f9a84f65b/pixelalisa.jpg",
        "craft_only": False
    },
    "Алиса-красотка": {
        "rarity": "🟡",
        "coins": 50,
        "description": "Кошка-красотка. Целуйте экраны>:)",
        "image": "https://sprutio.beget.com/image_cache/gagarin7/alexa3j5/642ef4a209468d212bdb64c2d9ff630f/alisabeat.jpg",
        "craft_only": False
    }
}

# Загрузка сохраненных данных
def load_saved_data():
    global CARDS_DATABASE, HIDDEN_CARDS, SHOP_ENABLED, CRAFT_RECIPES
    
    # Загрузка карточек
    if os.path.exists(CARDS_DB_FILE):
        try:
            with open(CARDS_DB_FILE, 'r', encoding='utf-8') as f:
                loaded_cards = json.load(f)
                CARDS_DATABASE.update(loaded_cards)
            logger.info(f"Загружено {len(loaded_cards)} карточек из файла")
        except Exception as e:
            logger.error(f"Ошибка загрузки карточек: {e}")
            # Если ошибка, используем карточки по умолчанию
            CARDS_DATABASE.update(DEFAULT_CARDS)
    else:
        # Если файла нет, используем карточки по умолчанию
        CARDS_DATABASE.update(DEFAULT_CARDS)
    
    # Загрузка скрытых карточек
    if os.path.exists(HIDDEN_CARDS_FILE):
        try:
            with open(HIDDEN_CARDS_FILE, 'r', encoding='utf-8') as f:
                hidden_list = json.load(f)
                HIDDEN_CARDS.update(hidden_list)
            logger.info(f"Загружено {len(hidden_list)} скрытых карточек")
        except Exception as e:
            logger.error(f"Ошибка загрузки скрытых карточек: {e}")
    
    # Загрузка статуса магазина
    if os.path.exists(SHOP_STATUS_FILE):
        try:
            with open(SHOP_STATUS_FILE, 'r', encoding='utf-8') as f:
                shop_status = json.load(f)
                SHOP_ENABLED = shop_status.get('enabled', True)
            logger.info(f"Статус магазина загружен: {'включен' if SHOP_ENABLED else 'выключен'}")
        except Exception as e:
            logger.error(f"Ошибка загрузки статуса магазина: {e}")
    
    # Загрузка рецептов крафта
    if os.path.exists(CRAFT_RECIPES_FILE):
        try:
            with open(CRAFT_RECIPES_FILE, 'r', encoding='utf-8') as f:
                CRAFT_RECIPES.update(json.load(f))
            logger.info(f"Загружено {len(CRAFT_RECIPES)} рецептов крафта")
        except Exception as e:
            logger.error(f"Ошибка загрузки рецептов крафта: {e}")

# Сохранение данных
def save_cards_database():
    try:
        with open(CARDS_DB_FILE, 'w', encoding='utf-8') as f:
            json.dump(CARDS_DATABASE, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Ошибка сохранения карточек: {e}")

def save_hidden_cards():
    try:
        with open(HIDDEN_CARDS_FILE, 'w', encoding='utf-8') as f:
            json.dump(list(HIDDEN_CARDS), f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Ошибка сохранения скрытых карточек: {e}")

def save_shop_status():
    try:
        with open(SHOP_STATUS_FILE, 'w', encoding='utf-8') as f:
            json.dump({'enabled': SHOP_ENABLED}, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Ошибка сохранения статуса магазина: {e}")

def save_craft_recipes():
    try:
        with open(CRAFT_RECIPES_FILE, 'w', encoding='utf-8') as f:
            json.dump(CRAFT_RECIPES, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Ошибка сохранения рецептов крафта: {e}")

# Владельцы бота
OWNER_IDS = [7599616968, 5872295617, 8112013114]

# КД на кнопки (в секундах)
BUTTON_COOLDOWNS = {
    'get_card': 5,
    'profile': 3,
    'my_cards': 3,
    'shop': 3,
    'all_cards': 3,
    'craft': 3
}

# Словари для хранения состояний
CARD_ADD_STATES = {}
PROMO_CREATION_STATES = {}
CARD_EDIT_STATES = {}
MESSAGE_OWNERS = {}
ACTIVE_SELECTIONS = {}  # Для отслеживания активных выборов карточек
CARD_SELLING_STATES = {}  # Для отслеживания карточек, которые уже выставлены на продажу
USER_SELLING_STATES = {}  # Для отслеживания пользователей, которые находятся в процессе продажи
USER_PRICE_INPUT_STATES = {}  # Для отслеживания пользователей, которые вводят цену
USER_CRAFT_STATES = {}  # Для отслеживания пользователей в процессе крафта
recipe_states = {}  # Для состояний создания рецептов

def init_db():
    conn = sqlite3.connect('cats.db')
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            coins INTEGER DEFAULT 0,
            total_cards INTEGER DEFAULT 0
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_cards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            rarity TEXT,
            card_name TEXT,
            obtained_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS market (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            seller_id INTEGER,
            card_id INTEGER,
            price INTEGER,
            listing_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (seller_id) REFERENCES users (user_id),
            FOREIGN KEY (card_id) REFERENCES user_cards (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cooldowns (
            user_id INTEGER PRIMARY KEY,
            last_card_time INTEGER,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS button_cooldowns (
            user_id INTEGER,
            button_type TEXT,
            last_press_time INTEGER,
            PRIMARY KEY (user_id, button_type)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS promocodes (
            code TEXT PRIMARY KEY,
            reward_type TEXT NOT NULL,
            reward_value TEXT NOT NULL,
            uses_left INTEGER DEFAULT 1,
            created_by INTEGER,
            created_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (created_by) REFERENCES users (user_id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS used_promocodes (
            user_id INTEGER,
            promo_code TEXT,
            used_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (user_id, promo_code),
            FOREIGN KEY (user_id) REFERENCES users (user_id),
            FOREIGN KEY (promo_code) REFERENCES promocodes (code)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bans (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            reason TEXT,
            banned_by INTEGER,
            banned_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (banned_by) REFERENCES users (user_id)
        )
    ''')

    conn.commit()
    conn.close()

def get_user(user_id, username):
    conn = sqlite3.connect('cats.db')
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    user = cursor.fetchone()

    if not user:
        cursor.execute('INSERT INTO users (user_id, username, coins, total_cards) VALUES (?, ?, 0, 0)',
                       (user_id, username))
        conn.commit()
        user = (user_id, username, 0, 0)

    conn.close()
    return user

def get_random_card():
    available_cards = [card for card in CARDS_DATABASE.keys() 
                      if card not in HIDDEN_CARDS and not CARDS_DATABASE[card].get('craft_only', False)]
    if not available_cards:
        return random.choice(list(CARDS_DATABASE.keys()))
    return random.choice(available_cards)

def is_owner(user_id):
    return user_id in OWNER_IDS

def is_user_banned(user_id):
    """Проверяет, забанен ли пользователь"""
    conn = sqlite3.connect('cats.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM bans WHERE user_id = ?', (user_id,))
    banned = cursor.fetchone()
    conn.close()
    return banned is not None

def get_ban_info(user_id):
    """Получает информацию о бане пользователя"""
    conn = sqlite3.connect('cats.db')
    cursor = conn.cursor()
    cursor.execute('SELECT username, reason, banned_by, banned_time FROM bans WHERE user_id = ?', (user_id,))
    ban_info = cursor.fetchone()
    conn.close()
    return ban_info

def check_button_cooldown(user_id, button_type):
    """Проверяет КД на кнопку"""
    current_time = time.time()
    
    conn = sqlite3.connect('cats.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT last_press_time FROM button_cooldowns WHERE user_id = ? AND button_type = ?', 
                   (user_id, button_type))
    result = cursor.fetchone()
    
    if result:
        last_press = result[0]
        cooldown_time = BUTTON_COOLDOWNS.get(button_type, 3)
        
        if current_time - last_press < cooldown_time:
            conn.close()
            return False
    
    cursor.execute('''
        INSERT OR REPLACE INTO button_cooldowns (user_id, button_type, last_press_time) 
        VALUES (?, ?, ?)
    ''', (user_id, button_type, current_time))
    
    conn.commit()
    conn.close()
    return True

def is_valid_url(url):
    """Проверяет, является ли строка валидным URL"""
    regex = re.compile(
        r'^(?:http|ftp)s?://'
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'
        r'localhost|'
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
        r'(?::\d+)?'
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return re.match(regex, url) is not None

def store_message_owner(message_id, user_id):
    """Сохраняет владельца сообщения с кнопками"""
    MESSAGE_OWNERS[message_id] = user_id

def check_message_owner(message_id, user_id):
    """Проверяет, принадлежит ли сообщение пользователю"""
    return MESSAGE_OWNERS.get(message_id) == user_id

def add_active_selection(user_id, card_id, selection_type):
    """Добавляет активный выбор карточки"""
    key = f"{user_id}_{selection_type}"
    ACTIVE_SELECTIONS[key] = card_id

def check_active_selection(user_id, card_id, selection_type):
    """Проверяет, выбрал ли пользователь уже эту карточку"""
    key = f"{user_id}_{selection_type}"
    return ACTIVE_SELECTIONS.get(key) == card_id

def remove_active_selection(user_id, selection_type):
    """Удаляет активный выбор"""
    key = f"{user_id}_{selection_type}"
    if key in ACTIVE_SELECTIONS:
        del ACTIVE_SELECTIONS[key]

def is_card_already_selling(user_id, card_id):
    """Проверяет, выставлена ли карточка уже на продажу"""
    conn = sqlite3.connect('cats.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM market WHERE card_id = ?', (card_id,))
    result = cursor.fetchone()
    conn.close()
    return result is not None

def add_card_selling_state(user_id, card_id):
    """Добавляет карточку в состояние продажи"""
    key = f"{user_id}_selling"
    if key not in CARD_SELLING_STATES:
        CARD_SELLING_STATES[key] = set()
    CARD_SELLING_STATES[key].add(card_id)

def remove_card_selling_state(user_id, card_id):
    """Удаляет карточку из состояния продажи"""
    key = f"{user_id}_selling"
    if key in CARD_SELLING_STATES and card_id in CARD_SELLING_STATES[key]:
        CARD_SELLING_STATES[key].remove(card_id)

def is_card_in_selling_state(user_id, card_id):
    """Проверяет, находится ли карточка в состоянии продажи"""
    key = f"{user_id}_selling"
    return key in CARD_SELLING_STATES and card_id in CARD_SELLING_STATES[key]

def add_user_selling_state(user_id, card_id):
    """Добавляет пользователя в состояние продажи"""
    USER_SELLING_STATES[user_id] = {
        'card_id': card_id,
        'start_time': time.time()
    }

def remove_user_selling_state(user_id):
    """Удаляет пользователя из состояния продажи"""
    if user_id in USER_SELLING_STATES:
        del USER_SELLING_STATES[user_id]

def is_user_in_selling_state(user_id):
    """Проверяет, находится ли пользователь в состоянии продажи"""
    return user_id in USER_SELLING_STATES

def get_user_selling_card(user_id):
    """Получает карточку, которую пользователь пытается продать"""
    if user_id in USER_SELLING_STATES:
        return USER_SELLING_STATES[user_id]['card_id']
    return None

def add_user_price_input_state(user_id, card_id):
    """Добавляет пользователя в состояние ввода цены"""
    USER_PRICE_INPUT_STATES[user_id] = {
        'card_id': card_id,
        'start_time': time.time()
    }

def remove_user_price_input_state(user_id):
    """Удаляет пользователя из состояния ввода цены"""
    if user_id in USER_PRICE_INPUT_STATES:
        del USER_PRICE_INPUT_STATES[user_id]

def is_user_in_price_input_state(user_id):
    """Проверяет, находится ли пользователь в состоянии ввода цены"""
    return user_id in USER_PRICE_INPUT_STATES

def get_user_price_input_card(user_id):
    """Получает карточку, для которой пользователь вводит цену"""
    if user_id in USER_PRICE_INPUT_STATES:
        return USER_PRICE_INPUT_STATES[user_id]['card_id']
    return None

def add_user_craft_state(user_id, target_card):
    """Добавляет пользователя в состояние крафта"""
    USER_CRAFT_STATES[user_id] = {
        'target_card': target_card,
        'start_time': time.time()
    }

def remove_user_craft_state(user_id):
    """Удаляет пользователя из состояния крафта"""
    if user_id in USER_CRAFT_STATES:
        del USER_CRAFT_STATES[user_id]

def is_user_in_craft_state(user_id):
    """Проверяет, находится ли пользователь в состоянии крафта"""
    return user_id in USER_CRAFT_STATES

def get_user_craft_target(user_id):
    """Получает карточку, которую пользователь пытается скрафтить"""
    if user_id in USER_CRAFT_STATES:
        return USER_CRAFT_STATES[user_id]['target_card']
    return None

# Декоратор для проверки бана
def check_ban(func):
    """Декоратор для проверки, забанен ли пользователь"""
    def wrapper(message):
        if message.date < BOT_START_TIME:
            return
            
        user_id = message.from_user.id
        
        if is_user_banned(user_id):
            ban_info = get_ban_info(user_id)
            if ban_info:
                username, reason, banned_by, banned_time = ban_info
                # Отправляем сообщение в ЛС пользователю
                try:
                    bot.send_message(user_id, 
                                   f"🚫 Вы забанены в боте!\n\n"
                                   f"📝 Причина: {reason}\n"
                                   f"⏰ Дата бана: {banned_time[:10]}\n\n"
                                   f"Если вы считаете, что это ошибка, свяжитесь с администратором.")
                except Exception as e:
                    logger.error(f"Не удалось отправить сообщение о бане пользователю {user_id}: {e}")
            return
            
        return func(message)
    return wrapper

# Декоратор для проверки бана в callback
def check_ban_callback(func):
    """Декоратор для проверки бана в callback"""
    def wrapper(call):
        user_id = call.from_user.id
        
        if is_user_banned(user_id):
            bot.answer_callback_query(call.id, "🚫 Вы забанены в боте!", show_alert=True)
            return
            
        return func(call)
    return wrapper

# НОВЫЕ КОМАНДЫ ДЛЯ ВЛАДЕЛЬЦЕВ - УПРАВЛЕНИЕ МАГАЗИНОМ
@bot.message_handler(commands=['offshop'])
def off_shop_command(message):
    if message.date < BOT_START_TIME:
        return
        
    user_id = message.from_user.id
    
    if not is_owner(user_id):
        bot.send_message(message.chat.id, "❌ У вас нет прав для использования этой команды!")
        return
    
    global SHOP_ENABLED
    if not SHOP_ENABLED:
        bot.send_message(message.chat.id, "❌ Магазин уже отключен!")
        return
    
    SHOP_ENABLED = False
    save_shop_status()
    
    bot.send_message(message.chat.id, "✅ Магазин отключен! Пользователи не могут покупать/продавать карточки.")

@bot.message_handler(commands=['onshop'])
def on_shop_command(message):
    if message.date < BOT_START_TIME:
        return
        
    user_id = message.from_user.id
    
    if not is_owner(user_id):
        bot.send_message(message.chat.id, "❌ У вас нет прав для использования этой команды!")
        return
    
    global SHOP_ENABLED
    if SHOP_ENABLED:
        bot.send_message(message.chat.id, "❌ Магазин уже включен!")
        return
    
    SHOP_ENABLED = True
    save_shop_status()
    
    bot.send_message(message.chat.id, "✅ Магазин включен! Пользователи снова могут покупать/продавать карточки.")

@bot.message_handler(commands=['shopstatus'])
def shop_status_command(message):
    if message.date < BOT_START_TIME:
        return
        
    user_id = message.from_user.id
    
    if not is_owner(user_id):
        bot.send_message(message.chat.id, "❌ У вас нет прав для использования этой команды!")
        return
    
    status = "🟢 ВКЛЮЧЕН" if SHOP_ENABLED else "🔴 ВЫКЛЮЧЕН"
    bot.send_message(message.chat.id, f"📊 Статус магазина: {status}")

# НОВЫЕ КОМАНДЫ ДЛЯ ВЛАДЕЛЬЦЕВ
@bot.message_handler(commands=['banbot'])
def ban_user_command(message):
    if message.date < BOT_START_TIME:
        return
        
    user_id = message.from_user.id
    
    if not is_owner(user_id):
        bot.send_message(message.chat.id, "❌ У вас нет прав для использования этой команды!")
        return
    
    try:
        parts = message.text.split(' ', 2)
        if len(parts) < 2:
            bot.send_message(message.chat.id, "❌ Используйте: /banbot @username [причина]")
            return
            
        username = parts[1].replace('@', '')
        reason = parts[2] if len(parts) > 2 else "Не указана"
        
        conn = sqlite3.connect('cats.db')
        cursor = conn.cursor()
        cursor.execute('SELECT user_id FROM users WHERE username = ?', (username,))
        target_user = cursor.fetchone()
        
        if not target_user:
            bot.send_message(message.chat.id, f"❌ Пользователь @{username} не найден!")
            conn.close()
            return
            
        target_user_id = target_user[0]
        
        # Проверяем, не забанен ли уже пользователь
        if is_user_banned(target_user_id):
            bot.send_message(message.chat.id, f"❌ Пользователь @{username} уже забанен!")
            conn.close()
            return
        
        # Добавляем в бан
        cursor.execute('INSERT INTO bans (user_id, username, reason, banned_by) VALUES (?, ?, ?, ?)',
                      (target_user_id, username, reason, user_id))
        
        conn.commit()
        conn.close()
        
        bot.send_message(message.chat.id, f"✅ Пользователь @{username} забанен в боте!\n📝 Причина: {reason}")
        
        try:
            bot.send_message(target_user_id, f"🚫 Вы были забанены в боте!\n📝 Причина: {reason}\n\nЕсли вы считаете, что это ошибка, свяжитесь с администратором.")
        except:
            pass
            
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Ошибка: {str(e)}")

@bot.message_handler(commands=['unbanbot'])
def unban_user_command(message):
    if message.date < BOT_START_TIME:
        return
        
    user_id = message.from_user.id
    
    if not is_owner(user_id):
        bot.send_message(message.chat.id, "❌ У вас нет прав для использования этой команды!")
        return
    
    try:
        parts = message.text.split()
        if len(parts) != 2:
            bot.send_message(message.chat.id, "❌ Используйте: /unbanbot @username")
            return
            
        username = parts[1].replace('@', '')
        
        conn = sqlite3.connect('cats.db')
        cursor = conn.cursor()
        cursor.execute('SELECT user_id FROM bans WHERE username = ?', (username,))
        banned_user = cursor.fetchone()
        
        if not banned_user:
            bot.send_message(message.chat.id, f"❌ Пользователь @{username} не найден в списке забаненных!")
            conn.close()
            return
            
        target_user_id = banned_user[0]
        
        # Удаляем из бана
        cursor.execute('DELETE FROM bans WHERE user_id = ?', (target_user_id,))
        
        conn.commit()
        conn.close()
        
        bot.send_message(message.chat.id, f"✅ Пользователь @{username} разбанен в боте!")
        
        try:
            bot.send_message(target_user_id, "🎉 Вы были разбанены в боте! Теперь вы снова можете использовать все функции.")
        except:
            pass
            
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Ошибка: {str(e)}")

@bot.message_handler(commands=['clearinventory'])
def clear_inventory_command(message):
    if message.date < BOT_START_TIME:
        return
        
    user_id = message.from_user.id
    
    if not is_owner(user_id):
        bot.send_message(message.chat.id, "❌ У вас нет прав для использования этой команды!")
        return
    
    try:
        parts = message.text.split()
        if len(parts) != 2:
            bot.send_message(message.chat.id, "❌ Используйте: /clearinventory @username")
            return
            
        username = parts[1].replace('@', '')
        
        conn = sqlite3.connect('cats.db')
        cursor = conn.cursor()
        cursor.execute('SELECT user_id FROM users WHERE username = ?', (username,))
        target_user = cursor.fetchone()
        
        if not target_user:
            bot.send_message(message.chat.id, f"❌ Пользователь @{username} не найден!")
            conn.close()
            return
            
        target_user_id = target_user[0]
        
        cursor.execute('DELETE FROM user_cards WHERE user_id = ?', (target_user_id,))
        cursor.execute('DELETE FROM market WHERE seller_id = ?', (target_user_id,))
        cursor.execute('UPDATE users SET total_cards = 0 WHERE user_id = ?', (target_user_id,))
        
        conn.commit()
        conn.close()
        
        bot.send_message(message.chat.id, f"✅ Инвентарь пользователя @{username} полностью очищен!")
        
        try:
            bot.send_message(target_user_id, "🗑️ Ваш инвентарь был очищен администратором!")
        except:
            pass
            
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Ошибка: {str(e)}")

@bot.message_handler(commands=['removecoins'])
def remove_coins_command(message):
    if message.date < BOT_START_TIME:
        return
        
    user_id = message.from_user.id
    
    if not is_owner(user_id):
        bot.send_message(message.chat.id, "❌ У вас нет прав для использования этой команды!")
        return
    
    try:
        parts = message.text.split()
        if len(parts) != 3:
            bot.send_message(message.chat.id, "❌ Используйте: /removecoins @username количество")
            return
            
        username = parts[1].replace('@', '')
        coins = int(parts[2])
        
        if coins <= 0:
            bot.send_message(message.chat.id, "❌ Количество монет должно быть положительным!")
            return
            
        conn = sqlite3.connect('cats.db')
        cursor = conn.cursor()
        cursor.execute('SELECT user_id, coins FROM users WHERE username = ?', (username,))
        target_user = cursor.fetchone()
        
        if not target_user:
            bot.send_message(message.chat.id, f"❌ Пользователь @{username} не найден!")
            conn.close()
            return
            
        target_user_id, current_coins = target_user
        
        if current_coins < coins:
            coins = current_coins
        
        cursor.execute('UPDATE users SET coins = coins - ? WHERE user_id = ?', (coins, target_user_id))
        conn.commit()
        conn.close()
        
        bot.send_message(message.chat.id, f"✅ Убрано {coins} монет у пользователя @{username}")
        
        try:
            bot.send_message(target_user_id, f"💰 У вас изъято {coins} монет администратором!")
        except:
            pass
            
    except ValueError:
        bot.send_message(message.chat.id, "❌ Укажите корректное количество монет!")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Ошибка: {str(e)}")

@bot.message_handler(commands=['removecard'])
def remove_card_command(message):
    if message.date < BOT_START_TIME:
        return
        
    user_id = message.from_user.id
    
    if not is_owner(user_id):
        bot.send_message(message.chat.id, "❌ У вас нет прав для использования этой команды!")
        return
    
    try:
        parts = message.text.split(' ', 3)
        if len(parts) < 3:
            bot.send_message(message.chat.id, '❌ Используйте: /removecard @username "Название карты" [количество=1]')
            return
            
        username = parts[1].replace('@', '')
        card_name = parts[2].strip()
        count = 1
        
        if len(parts) == 4:
            try:
                count = int(parts[3])
                if count <= 0:
                    bot.send_message(message.chat.id, "❌ Количество должно быть положительным!")
                    return
            except ValueError:
                bot.send_message(message.chat.id, "❌ Укажите корректное количество!")
                return
        
        if card_name not in CARDS_DATABASE:
            bot.send_message(message.chat.id, f"❌ Карточка '{card_name}' не найдена!")
            return
            
        conn = sqlite3.connect('cats.db')
        cursor = conn.cursor()
        cursor.execute('SELECT user_id FROM users WHERE username = ?', (username,))
        target_user = cursor.fetchone()
        
        if not target_user:
            bot.send_message(message.chat.id, f"❌ Пользователь @{username} не найден!")
            conn.close()
            return
            
        target_user_id = target_user[0]
        
        cursor.execute('''
            SELECT id FROM user_cards 
            WHERE user_id = ? AND card_name = ? 
            LIMIT ?
        ''', (target_user_id, card_name, count))
        
        cards_to_remove = cursor.fetchall()
        
        if not cards_to_remove:
            bot.send_message(message.chat.id, f"❌ У пользователя @{username} нет карточки '{card_name}'!")
            conn.close()
            return
        
        removed_count = 0
        for card_id_tuple in cards_to_remove:
            card_id = card_id_tuple[0]
            
            cursor.execute('DELETE FROM user_cards WHERE id = ?', (card_id,))
            cursor.execute('DELETE FROM market WHERE card_id = ?', (card_id,))
            removed_count += 1
        
        cursor.execute('UPDATE users SET total_cards = total_cards - ? WHERE user_id = ?', 
                      (removed_count, target_user_id))
        
        conn.commit()
        conn.close()
        
        if removed_count == 1:
            bot.send_message(message.chat.id, f"✅ Карточка '{card_name}' удалена у пользователя @{username}")
        else:
            bot.send_message(message.chat.id, f"✅ Удалено {removed_count} карточек '{card_name}' у пользователя @{username}")
        
        try:
            if removed_count == 1:
                bot.send_message(target_user_id, f"🗑️ Карточка '{card_name}' была удалена из вашего инвентаря администратором!")
            else:
                bot.send_message(target_user_id, f"🗑️ {removed_count} карточек '{card_name}' были удалены из вашего инвентаря администратором!")
        except:
            pass
            
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Ошибка: {str(e)}")

# ОБНОВЛЕННАЯ КОМАНДА ADD_CARD С ВОПРОСОМ О КРАФТЕ
@bot.message_handler(commands=['addcard'])
def add_card_command(message):
    if message.date < BOT_START_TIME:
        return
        
    user_id = message.from_user.id
    
    if not is_owner(user_id):
        bot.send_message(message.chat.id, "❌ У вас нет прав для использования этой команды!")
        return
    
    CARD_ADD_STATES[user_id] = {"state": "waiting_card_image"}
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("📸 Отправить фото", callback_data="addcard_photo"))
    markup.add(types.InlineKeyboardButton("🔗 Ввести URL", callback_data="addcard_url"))
    
    bot.send_message(message.chat.id, 
                    "🖼 Как вы хотите добавить изображение для новой карточки?",
                    reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('addcard_'))
def process_add_card_method(call):
    user_id = call.from_user.id
    
    if not is_owner(user_id):
        bot.send_message(call.message.chat.id, "❌ У вас нет прав!")
        return
    
    method = call.data.split('_')[1]
    
    if method == "photo":
        CARD_ADD_STATES[user_id] = {"state": "waiting_card_photo"}
        bot.send_message(call.message.chat.id, "📸 Отправьте фото для новой карточки:")
        
    elif method == "url":
        CARD_ADD_STATES[user_id] = {"state": "waiting_card_url"}
        bot.send_message(call.message.chat.id, "🔗 Введите URL изображения для новой карточки:")
    
    bot.answer_callback_query(call.id)

@bot.message_handler(content_types=['photo'], 
                    func=lambda message: CARD_ADD_STATES.get(message.from_user.id, {}).get("state") == "waiting_card_photo")
def process_card_photo(message):
    if message.date < BOT_START_TIME:
        return
        
    user_id = message.from_user.id
    
    try:
        file_id = message.photo[-1].file_id
        file_info = bot.get_file(file_id)
        file_url = f"https://api.telegram.org/file/bot{bot.token}/{file_info.file_path}"
        
        CARD_ADD_STATES[user_id] = {
            "state": "waiting_card_name", 
            "photo_url": file_url
        }
        
        bot.send_message(message.chat.id, "📝 Теперь введите название карточки:")
        
    except Exception as e:
        logger.error(f"Error processing photo: {e}")
        bot.send_message(message.chat.id, "❌ Ошибка при обработке фото!")
        if user_id in CARD_ADD_STATES:
            del CARD_ADD_STATES[user_id]

@bot.message_handler(func=lambda message: CARD_ADD_STATES.get(message.from_user.id, {}).get("state") == "waiting_card_url")
def process_card_url(message):
    if message.date < BOT_START_TIME:
        return
        
    user_id = message.from_user.id
    url = message.text.strip()
    
    if not is_valid_url(url):
        bot.send_message(message.chat.id, "❌ Неверный URL! Убедитесь, что ссылка начинается с http:// или https://")
        return
    
    CARD_ADD_STATES[user_id] = {
        "state": "waiting_card_name", 
        "photo_url": url
    }
    
    bot.send_message(message.chat.id, "✅ URL принят! Теперь введите название карточки:")

@bot.message_handler(func=lambda message: CARD_ADD_STATES.get(message.from_user.id, {}).get("state") == "waiting_card_name")
def process_card_name(message):
    if message.date < BOT_START_TIME:
        return
        
    user_id = message.from_user.id
    state_data = CARD_ADD_STATES[user_id]
    card_name = message.text.strip()
    
    CARD_ADD_STATES[user_id] = {
        "state": "waiting_card_rarity",
        "photo_url": state_data["photo_url"],
        "card_name": card_name
    }
    
    markup = types.InlineKeyboardMarkup()
    for rarity in RARITIES.keys():
        markup.add(types.InlineKeyboardButton(
            f"{rarity} {RARITIES[rarity]['name']}", 
            callback_data=f"admin_rarity_{rarity}"
        ))
    
    bot.send_message(message.chat.id, 
                    "⭐️ Выберите редкость карточки:", 
                    reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('admin_rarity_'))
def process_admin_rarity(call):
    user_id = call.from_user.id
    rarity = call.data.split('_')[2]
    
    if user_id not in CARD_ADD_STATES or "state" not in CARD_ADD_STATES[user_id]:
        bot.send_message(call.message.chat.id, "❌ Сессия истекла, начните заново!")
        return
    
    state_data = CARD_ADD_STATES[user_id]
    card_name = state_data["card_name"]
    photo_url = state_data["photo_url"]
    
    CARD_ADD_STATES[user_id] = {
        "state": "waiting_card_coins",
        "photo_url": photo_url,
        "card_name": card_name,
        "rarity": rarity
    }
    
    bot.send_message(call.message.chat.id,
                    f"💰 Введите количество монет за карточку (по умолчанию для {rarity} {RARITIES[rarity]['name']}: {RARITIES[rarity]['coins']}):")
    
    bot.answer_callback_query(call.id)

@bot.message_handler(func=lambda message: CARD_ADD_STATES.get(message.from_user.id, {}).get("state") == "waiting_card_coins")
def process_card_coins(message):
    if message.date < BOT_START_TIME:
        return
        
    user_id = message.from_user.id
    state_data = CARD_ADD_STATES[user_id]
    
    try:
        coins = int(message.text.strip())
        if coins <= 0:
            bot.send_message(message.chat.id, "❌ Количество монет должно быть положительным!")
            return
        
        CARD_ADD_STATES[user_id] = {
            "state": "waiting_card_description",
            "photo_url": state_data["photo_url"],
            "card_name": state_data["card_name"],
            "rarity": state_data["rarity"],
            "coins": coins
        }
        
        bot.send_message(message.chat.id, "📝 Введите описание карточки:")
        
    except ValueError:
        bot.send_message(message.chat.id, "❌ Пожалуйста, введите корректное число!")

@bot.message_handler(func=lambda message: CARD_ADD_STATES.get(message.from_user.id, {}).get("state") == "waiting_card_description")
def process_card_description(message):
    if message.date < BOT_START_TIME:
        return
        
    user_id = message.from_user.id
    state_data = CARD_ADD_STATES[user_id]
    
    description = message.text.strip()
    
    CARD_ADD_STATES[user_id] = {
        "state": "waiting_craft_choice",
        "photo_url": state_data["photo_url"],
        "card_name": state_data["card_name"],
        "rarity": state_data["rarity"],
        "coins": state_data["coins"],
        "description": description
    }
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("✅ Да, добавить в крафт", callback_data="add_to_craft_yes"))
    markup.add(types.InlineKeyboardButton("❌ Нет, обычная карточка", callback_data="add_to_craft_no"))
    
    bot.send_message(message.chat.id,
                    "🔨 Добавить эту карточку в систему крафта?\n\n"
                    "Если да, то карточка будет доступна только через крафт и не будет выпадать обычным способом.",
                    reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('add_to_craft_'))
def process_craft_choice(call):
    user_id = call.from_user.id
    
    if not is_owner(user_id):
        bot.answer_callback_query(call.id, "❌ У вас нет прав!", show_alert=True)
        return
    
    if user_id not in CARD_ADD_STATES:
        bot.send_message(call.message.chat.id, "❌ Сессия истекла!")
        return
    
    state_data = CARD_ADD_STATES[user_id]
    choice = call.data.split('_')[3]
    
    craft_only = (choice == "yes")
    
    # Добавляем карточку в базу с сохранением
    card_name = state_data["card_name"]
    CARDS_DATABASE[card_name] = {
        "rarity": state_data["rarity"],
        "coins": state_data["coins"],
        "description": state_data["description"],
        "image": state_data["photo_url"],
        "craft_only": craft_only
    }
    
    # Сохраняем в файл
    save_cards_database()
    
    try:
        craft_status = "🔨 ТОЛЬКО КРАФТ" if craft_only else "🎴 ОБЫЧНАЯ"
        preview_text = f"""✅ Карточка успешно добавлена!

📝 Название: {card_name}
📝 Описание: {state_data['description']}
⭐️ Редкость: {state_data['rarity']} {RARITIES[state_data['rarity']]['name']}
💰 Стоимость: {state_data['coins']} монет
📋 Тип: {craft_status}"""
        
        bot.send_photo(call.message.chat.id, state_data["photo_url"], caption=preview_text)
        
        if craft_only:
            bot.send_message(call.message.chat.id,
                           "🔨 Теперь настройте рецепт крафта для этой карточки с помощью команды /addrecipe")
    
    except Exception as e:
        logger.error(f"Error sending photo preview: {e}")
        bot.send_message(call.message.chat.id, 
                       f"✅ Карточка '{card_name}' добавлена!\n"
                       f"📝 Описание: {state_data['description']}\n"
                       f"⭐️ Редкость: {state_data['rarity']} {RARITIES[state_data['rarity']]['name']}\n"
                       f"💰 Стоимость: {state_data['coins']} монет\n"
                       f"📋 Тип: {'🔨 ТОЛЬКО КРАФТ' if craft_only else '🎴 ОБЫЧНАЯ'}\n\n"
                       f"⚠️ Не удалось отправить превью изображения")
    
    del CARD_ADD_STATES[user_id]
    bot.answer_callback_query(call.id)

# КОМАНДЫ ДЛЯ УПРАВЛЕНИЯ КРАФТОМ
@bot.message_handler(commands=['addrecipe'])
def add_recipe_command(message):
    if message.date < BOT_START_TIME:
        return
        
    user_id = message.from_user.id
    
    if not is_owner(user_id):
        bot.send_message(message.chat.id, "❌ У вас нет прав для использования этой команды!")
        return
    
    # Показываем только карточки, которые помечены как craft_only
    craft_cards = [card for card, data in CARDS_DATABASE.items() if data.get('craft_only', False)]
    
    if not craft_cards:
        bot.send_message(message.chat.id, "❌ Нет карточек, доступных только через крафт!")
        return
    
    markup = types.InlineKeyboardMarkup()
    for card_name in craft_cards:
        rarity = CARDS_DATABASE[card_name]["rarity"]
        # Проверяем, есть ли уже рецепт для этой карточки
        has_recipe = "✅" if card_name in CRAFT_RECIPES else "❌"
        markup.add(types.InlineKeyboardButton(
            f"{has_recipe} {rarity} {card_name}", 
            callback_data=f"addrecipe_{card_name}"
        ))
    
    sent_message = bot.send_message(message.chat.id, 
                    "🔨 Выберите карточку для настройки рецепта крафта:",
                    reply_markup=markup)
    
    store_message_owner(sent_message.message_id, user_id)

@bot.callback_query_handler(func=lambda call: call.data.startswith('addrecipe_'))
def process_recipe_selection(call):
    user_id = call.from_user.id
    
    if not check_message_owner(call.message.message_id, user_id):
        bot.answer_callback_query(call.id, "❌ Это не ваше меню!", show_alert=True)
        return
    
    if not is_owner(user_id):
        bot.answer_callback_query(call.id, "❌ У вас нет прав!", show_alert=True)
        return
    
    card_name = call.data.split('_', 1)[1]
    
    # Сохраняем выбранную карточку для рецепта
    recipe_states[user_id] = {
        'target_card': card_name,
        'ingredients': {},
        'state': 'waiting_ingredient'
    }
    
    markup = types.InlineKeyboardMarkup()
    
    # Показываем все доступные карточки как возможные ингредиенты
    available_cards = list(CARDS_DATABASE.keys())
    cards_per_row = 2
    
    for i in range(0, len(available_cards), cards_per_row):
        row_cards = available_cards[i:i + cards_per_row]
        row_buttons = []
        for card in row_cards:
            rarity = CARDS_DATABASE[card]["rarity"]
            btn_text = f"{rarity} {card[:15]}..." if len(card) > 15 else f"{rarity} {card}"
            row_buttons.append(types.InlineKeyboardButton(btn_text, callback_data=f"addingredient_{card}"))
        markup.row(*row_buttons)
    
    markup.add(types.InlineKeyboardButton("✅ Завершить настройку рецепта", callback_data="finish_recipe"))
    
    bot.send_message(call.message.chat.id,
                    f"🔨 Настройка рецепта для: {CARDS_DATABASE[card_name]['rarity']} {card_name}\n\n"
                    f"Выберите карточки-ингредиенты для крафта:",
                    reply_markup=markup)
    
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data.startswith('addingredient_'))
def process_ingredient_selection(call):
    user_id = call.from_user.id
    
    if not check_message_owner(call.message.message_id, user_id):
        bot.answer_callback_query(call.id, "❌ Это не ваше меню!", show_alert=True)
        return
    
    if user_id not in recipe_states:
        bot.send_message(call.message.chat.id, "❌ Сессия истекла!")
        return
    
    ingredient_card = call.data.split('_', 1)[1]
    
    # Сохраняем текущий ингредиент
    recipe_states[user_id]['current_ingredient'] = ingredient_card
    recipe_states[user_id]['state'] = 'waiting_quantity'
    
    bot.send_message(call.message.chat.id,
                    f"🔢 Введите количество карточек '{ingredient_card}' для рецепта:")
    
    bot.answer_callback_query(call.id)

@bot.message_handler(func=lambda message: recipe_states.get(message.from_user.id, {}).get('state') == 'waiting_quantity')
def process_ingredient_quantity(message):
    if message.date < BOT_START_TIME:
        return
        
    user_id = message.from_user.id
    
    if user_id not in recipe_states:
        bot.send_message(message.chat.id, "❌ Сессия истекла!")
        return
    
    try:
        quantity = int(message.text.strip())
        if quantity <= 0:
            bot.send_message(message.chat.id, "❌ Количество должно быть положительным!")
            return
        
        state = recipe_states[user_id]
        ingredient_card = state['current_ingredient']
        state['ingredients'][ingredient_card] = quantity
        
        # Показываем текущий прогресс
        progress_text = f"🔨 Текущий рецепт для: {CARDS_DATABASE[state['target_card']]['rarity']} {state['target_card']}\n\n"
        progress_text += "📦 Ингредиенты:\n"
        
        for ing, qty in state['ingredients'].items():
            progress_text += f"  - {ing} ×{qty}\n"
        
        markup = types.InlineKeyboardMarkup()
        available_cards = list(CARDS_DATABASE.keys())
        cards_per_row = 2
        
        for i in range(0, len(available_cards), cards_per_row):
            row_cards = available_cards[i:i + cards_per_row]
            row_buttons = []
            for card in row_cards:
                rarity = CARDS_DATABASE[card]["rarity"]
                btn_text = f"{rarity} {card[:15]}..." if len(card) > 15 else f"{rarity} {card}"
                row_buttons.append(types.InlineKeyboardButton(btn_text, callback_data=f"addingredient_{card}"))
            markup.row(*row_buttons)
        
        markup.add(types.InlineKeyboardButton("✅ Завершить настройку рецепта", callback_data="finish_recipe"))
        
        bot.send_message(message.chat.id, progress_text, reply_markup=markup)
        
        # Возвращаемся в состояние выбора ингредиентов
        recipe_states[user_id]['state'] = 'waiting_ingredient'
        
    except ValueError:
        bot.send_message(message.chat.id, "❌ Пожалуйста, введите корректное число!")

@bot.callback_query_handler(func=lambda call: call.data == 'finish_recipe')
def finish_recipe_setup(call):
    user_id = call.from_user.id
    
    if not check_message_owner(call.message.message_id, user_id):
        bot.answer_callback_query(call.id, "❌ Это не ваше меню!", show_alert=True)
        return
    
    if user_id not in recipe_states:
        bot.send_message(call.message.chat.id, "❌ Сессия истекла!")
        return
    
    state = recipe_states[user_id]
    
    if not state['ingredients']:
        bot.send_message(call.message.chat.id, "❌ Рецепт не может быть пустым!")
        return
    
    # Сохраняем рецепт
    CRAFT_RECIPES[state['target_card']] = {
        'ingredients': state['ingredients']
    }
    
    save_craft_recipes()
    
    # Показываем итоговый рецепт
    result_text = f"""✅ Рецепт крафта сохранен!

🎯 Результат: {CARDS_DATABASE[state['target_card']]['rarity']} {state['target_card']}

📦 Ингредиенты:"""
    
    for ingredient, quantity in state['ingredients'].items():
        result_text += f"\n  - {ingredient} ×{quantity}"
    
    bot.send_message(call.message.chat.id, result_text)
    
    # Очищаем состояние
    del recipe_states[user_id]
    bot.answer_callback_query(call.id)

@bot.message_handler(commands=['deleterecipe'])
def delete_recipe_command(message):
    if message.date < BOT_START_TIME:
        return
        
    user_id = message.from_user.id
    
    if not is_owner(user_id):
        bot.send_message(message.chat.id, "❌ У вас нет прав для использования этой команды!")
        return
    
    if not CRAFT_RECIPES:
        bot.send_message(message.chat.id, "❌ Нет сохраненных рецептов!")
        return
    
    markup = types.InlineKeyboardMarkup()
    for card_name in CRAFT_RECIPES.keys():
        if card_name in CARDS_DATABASE:
            rarity = CARDS_DATABASE[card_name]["rarity"]
            markup.add(types.InlineKeyboardButton(
                f"{rarity} {card_name}", 
                callback_data=f"deleterecipe_{card_name}"
            ))
    
    sent_message = bot.send_message(message.chat.id, 
                    "🗑 Выберите рецепт для удаления:",
                    reply_markup=markup)
    
    store_message_owner(sent_message.message_id, user_id)

@bot.callback_query_handler(func=lambda call: call.data.startswith('deleterecipe_'))
def process_delete_recipe(call):
    user_id = call.from_user.id
    
    if not check_message_owner(call.message.message_id, user_id):
        bot.answer_callback_query(call.id, "❌ Это не ваше меню!", show_alert=True)
        return
    
    if not is_owner(user_id):
        bot.answer_callback_query(call.id, "❌ У вас нет прав!", show_alert=True)
        return
    
    card_name = call.data.split('_', 1)[1]
    
    if card_name in CRAFT_RECIPES:
        del CRAFT_RECIPES[card_name]
        save_craft_recipes()
        bot.send_message(call.message.chat.id, f"✅ Рецепт для '{card_name}' удален!")
    else:
        bot.send_message(call.message.chat.id, f"❌ Рецепт для '{card_name}' не найден!")
    
    bot.answer_callback_query(call.id)

@bot.message_handler(commands=['recipes'])
def list_recipes_command(message):
    if message.date < BOT_START_TIME:
        return
        
    user_id = message.from_user.id
    
    if not is_owner(user_id):
        bot.send_message(message.chat.id, "❌ У вас нет прав для использования этой команды!")
        return
    
    if not CRAFT_RECIPES:
        bot.send_message(message.chat.id, "❌ Нет сохраненных рецептов!")
        return
    
    text = "📋 Список всех рецептов крафта:\n\n"
    
    for result_card, recipe in CRAFT_RECIPES.items():
        if result_card in CARDS_DATABASE:
            card_data = CARDS_DATABASE[result_card]
            text += f"{card_data['rarity']} {result_card}:\n"
            
            for ingredient, amount in recipe['ingredients'].items():
                text += f"  - {ingredient} ×{amount}\n"
            text += "\n"
    
    bot.send_message(message.chat.id, text)

# ОСТАЛЬНЫЕ КОМАНДЫ ВЛАДЕЛЬЦЕВ С СОХРАНЕНИЕМ
@bot.message_handler(commands=['deletecard'])
def delete_card_command(message):
    if message.date < BOT_START_TIME:
        return
        
    user_id = message.from_user.id
    
    if not is_owner(user_id):
        bot.send_message(message.chat.id, "❌ У вас нет прав!")
        return
    
    markup = types.InlineKeyboardMarkup()
    for card_name in CARDS_DATABASE.keys():
        rarity = CARDS_DATABASE[card_name]["rarity"]
        markup.add(types.InlineKeyboardButton(
            f"{rarity} {card_name}", 
            callback_data=f"deletecard_{card_name}"
        ))
    
    sent_message = bot.send_message(message.chat.id, 
                    "🗑 Выберите карточку для удаления:", 
                    reply_markup=markup)
    
    store_message_owner(sent_message.message_id, user_id)

@bot.callback_query_handler(func=lambda call: call.data.startswith('deletecard_'))
def process_delete_card(call):
    user_id = call.from_user.id
    
    if not check_message_owner(call.message.message_id, user_id):
        bot.answer_callback_query(call.id, "❌ Это не ваше меню!", show_alert=True)
        return
    
    if not is_owner(user_id):
        bot.answer_callback_query(call.id, "❌ У вас нет прав!", show_alert=True)
        return
    
    card_name = call.data.split('_', 1)[1]
    
    if card_name in CARDS_DATABASE:
        del CARDS_DATABASE[card_name]
        if card_name in HIDDEN_CARDS:
            HIDDEN_CARDS.remove(card_name)
        if card_name in CRAFT_RECIPES:
            del CRAFT_RECIPES[card_name]
            save_craft_recipes()
        
        save_cards_database()
        save_hidden_cards()
        
        bot.send_message(call.message.chat.id, f"✅ Карточка '{card_name}' удалена!")
    else:
        bot.send_message(call.message.chat.id, f"❌ Карточка '{card_name}' не найдена!")
    
    bot.answer_callback_query(call.id)

@bot.message_handler(commands=['hide_card'])
def hide_card_command(message):
    if message.date < BOT_START_TIME:
        return
        
    user_id = message.from_user.id
    
    if not is_owner(user_id):
        bot.send_message(message.chat.id, "❌ У вас нет прав!")
        return
    
    try:
        parts = message.text.split(' ', 1)
        if len(parts) != 2:
            bot.send_message(message.chat.id, '❌ Используйте: /hide_card "Название карты"')
            return
            
        card_name = parts[1].strip()
        
        if card_name not in CARDS_DATABASE:
            bot.send_message(message.chat.id, f"❌ Карточка '{card_name}' не найдена!")
            return
            
        HIDDEN_CARDS.add(card_name)
        save_hidden_cards()
        bot.send_message(message.chat.id, f"✅ Карточка '{card_name}' скрыта из выпадения!")
        
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Ошибка: {str(e)}")

@bot.message_handler(commands=['unhide_card'])
def unhide_card_command(message):
    if message.date < BOT_START_TIME:
        return
        
    user_id = message.from_user.id
    
    if not is_owner(user_id):
        bot.send_message(message.chat.id, "❌ У вас нет прав!")
        return
    
    try:
        parts = message.text.split(' ', 1)
        if len(parts) != 2:
            bot.send_message(message.chat.id, '❌ Используйте: /unhide_card "Название карты"')
            return
            
        card_name = parts[1].strip()
        
        if card_name not in CARDS_DATABASE:
            bot.send_message(message.chat.id, f"❌ Карточка '{card_name}' не найдена!")
            return
            
        if card_name in HIDDEN_CARDS:
            HIDDEN_CARDS.remove(card_name)
            save_hidden_cards()
            bot.send_message(message.chat.id, f"✅ Карточка '{card_name}' возвращена в выпадение!")
        else:
            bot.send_message(message.chat.id, f"ℹ️ Карточка '{card_name}' и так не была скрыта!")
        
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Ошибка: {str(e)}")

@bot.message_handler(commands=['cards_list'])
def cards_list_command(message):
    if message.date < BOT_START_TIME:
        return
        
    user_id = message.from_user.id
    
    if not is_owner(user_id):
        bot.send_message(message.chat.id, "❌ У вас нет прав!")
        return
    
    cards_text = "📋 Список всех карточек:\n\n"
    for i, card_name in enumerate(CARDS_DATABASE.keys(), 1):
        rarity = CARDS_DATABASE[card_name]["rarity"]
        hidden = "🚫" if card_name in HIDDEN_CARDS else "✅"
        craft_only = "🔨" if CARDS_DATABASE[card_name].get('craft_only', False) else "🎴"
        cards_text += f"{i}. {rarity} {card_name} {hidden} {craft_only}\n"
        
        if i % 20 == 0:
            bot.send_message(message.chat.id, cards_text)
            cards_text = ""
    
    if cards_text:
        bot.send_message(message.chat.id, cards_text)

@bot.message_handler(commands=['give_coins'])
def give_coins_command(message):
    if message.date < BOT_START_TIME:
        return
        
    user_id = message.from_user.id
    
    if not is_owner(user_id):
        bot.send_message(message.chat.id, "❌ У вас нет прав!")
        return
    
    try:
        parts = message.text.split()
        if len(parts) != 3:
            bot.send_message(message.chat.id, "❌ Используйте: /give_coins @username количество")
            return
            
        username = parts[1].replace('@', '')
        coins = int(parts[2])
        
        if coins <= 0:
            bot.send_message(message.chat.id, "❌ Количество монет должно быть положительным!")
            return
            
        conn = sqlite3.connect('cats.db')
        cursor = conn.cursor()
        cursor.execute('SELECT user_id FROM users WHERE username = ?', (username,))
        target_user = cursor.fetchone()
        
        if not target_user:
            bot.send_message(message.chat.id, f"❌ Пользователь @{username} не найден!")
            conn.close()
            return
            
        target_user_id = target_user[0]
        
        cursor.execute('UPDATE users SET coins = coins + ? WHERE user_id = ?', (coins, target_user_id))
        conn.commit()
        conn.close()
        
        bot.send_message(message.chat.id, f"✅ Выдано {coins} монет пользователю @{username}")
        
        try:
            bot.send_message(target_user_id, f"🎁 Вам выдано {coins} монет от администратора!")
        except:
            pass
            
    except ValueError:
        bot.send_message(message.chat.id, "❌ Укажите корректное количество монет!")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Ошибка: {str(e)}")

@bot.message_handler(commands=['give_card'])
def give_card_command(message):
    if message.date < BOT_START_TIME:
        return
        
    user_id = message.from_user.id
    
    if not is_owner(user_id):
        bot.send_message(message.chat.id, "❌ У вас нет прав!")
        return
    
    try:
        parts = message.text.split(' ', 2)
        if len(parts) != 3:
            bot.send_message(message.chat.id, '❌ Используйте: /give_card @username "Название карты"')
            return
            
        username = parts[1].replace('@', '')
        card_name = parts[2].strip()
        
        if card_name not in CARDS_DATABASE:
            bot.send_message(message.chat.id, f"❌ Карточка '{card_name}' не найдена!")
            return
            
        conn = sqlite3.connect('cats.db')
        cursor = conn.cursor()
        cursor.execute('SELECT user_id FROM users WHERE username = ?', (username,))
        target_user = cursor.fetchone()
        
        if not target_user:
            bot.send_message(message.chat.id, f"❌ Пользователь @{username} не найден!")
            conn.close()
            return
            
        target_user_id = target_user[0]
        card_data = CARDS_DATABASE[card_name]
        
        cursor.execute('INSERT INTO user_cards (user_id, rarity, card_name) VALUES (?, ?, ?)',
                      (target_user_id, card_data["rarity"], card_name))
        cursor.execute('UPDATE users SET coins = coins + ?, total_cards = total_cards + 1 WHERE user_id = ?',
                      (card_data["coins"], target_user_id))
        
        conn.commit()
        conn.close()
        
        bot.send_message(message.chat.id, f"✅ Карточка '{card_name}' выдана пользователю @{username}")
        
        try:
            card_text = f"""🎁 Вам выдана карточка администратором!

🖼 Карточка: "{card_name}"
⭐️ Редкость: {card_data['rarity']} {RARITIES[card_data['rarity']]['name']}
💰 Монеты: +{card_data['coins']} монет"""
            
            bot.send_photo(target_user_id, card_data['image'], caption=card_text)
        except:
            bot.send_message(target_user_id, f"🎁 Вам выдана карточка: {card_name}")
            
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Ошибка: {str(e)}")

@bot.message_handler(commands=['reset_cooldown'])
def reset_cooldown_command(message):
    if message.date < BOT_START_TIME:
        return
        
    user_id = message.from_user.id
    
    if not is_owner(user_id):
        bot.send_message(message.chat.id, "❌ У вас нет прав!")
        return
    
    try:
        parts = message.text.split()
        if len(parts) != 2:
            bot.send_message(message.chat.id, "❌ Используйте: /reset_cooldown @username")
            return
            
        username = parts[1].replace('@', '')
        
        conn = sqlite3.connect('cats.db')
        cursor = conn.cursor()
        cursor.execute('SELECT user_id FROM users WHERE username = ?', (username,))
        target_user = cursor.fetchone()
        
        if not target_user:
            bot.send_message(message.chat.id, f"❌ Пользователь @{username} не найден!")
            conn.close()
            return
            
        target_user_id = target_user[0]
        
        cursor.execute('DELETE FROM cooldowns WHERE user_id = ?', (target_user_id,))
        cursor.execute('DELETE FROM button_cooldowns WHERE user_id = ?', (target_user_id,))
        conn.commit()
        conn.close()
        
        bot.send_message(message.chat.id, f"✅ Кулдаун сброшен для @{username}")
        
        try:
            bot.send_message(target_user_id, "⏰ Ваш кулдаун был сброшен администратором! Можете получить новую карточку.")
        except:
            pass
            
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Ошибка: {str(e)}")

# ОСТАЛЬНЫЕ КОМАНДЫ ДЛЯ ВЛАДЕЛЬЦЕВ
@bot.message_handler(commands=['stats'])
def stats_command(message):
    if message.date < BOT_START_TIME:
        return
        
    user_id = message.from_user.id
    
    if not is_owner(user_id):
        bot.send_message(message.chat.id, "❌ У вас нет прав!")
        return
    
    conn = sqlite3.connect('cats.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) FROM users')
    total_users = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM user_cards')
    total_cards = cursor.fetchone()[0]
    
    cursor.execute('SELECT SUM(coins) FROM users')
    total_coins = cursor.fetchone()[0] or 0
    
    cursor.execute('SELECT COUNT(*) FROM market')
    active_listings = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM bans')
    banned_users = cursor.fetchone()[0]
    
    conn.close()
    
    stats_text = f"""📊 Статистика бота:

👥 Всего пользователей: {total_users}
🎴 Всего карточек: {total_cards}
💰 Всего монет в системе: {total_coins}
🛒 Активных объявлений: {active_listings}
📋 Карточек в базе: {len(CARDS_DATABASE)}
🚫 Скрытых карточек: {len(HIDDEN_CARDS)}
🔨 Карточек только для крафта: {len([c for c in CARDS_DATABASE.values() if c.get('craft_only', False)])}
📋 Рецептов крафта: {len(CRAFT_RECIPES)}
🚷 Забаненных пользователей: {banned_users}"""

    bot.send_message(message.chat.id, stats_text)

@bot.message_handler(commands=['broadcast'])
def broadcast_command(message):
    if message.date < BOT_START_TIME:
        return
        
    user_id = message.from_user.id
    
    if not is_owner(user_id):
        bot.send_message(message.chat.id, "❌ У вас нет прав!")
        return
    
    try:
        parts = message.text.split(' ', 1)
        if len(parts) != 2:
            bot.send_message(message.chat.id, "❌ Используйте: /broadcast текст_сообщения")
            return
            
        broadcast_text = parts[1]
        
        conn = sqlite3.connect('cats.db')
        cursor = conn.cursor()
        cursor.execute('SELECT user_id FROM users')
        users = cursor.fetchall()
        conn.close()
        
        sent_count = 0
        failed_count = 0
        
        for (user_id,) in users:
            try:
                bot.send_message(user_id, f"📢 Объявление от администратора:\n\n{broadcast_text}")
                sent_count += 1
                time.sleep(0.1)
            except:
                failed_count += 1
        
        bot.send_message(message.chat.id, 
                        f"✅ Рассылка завершена!\n"
                        f"📤 Отправлено: {sent_count}\n"
                        f"❌ Не удалось: {failed_count}")
        
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Ошибка при рассылке: {str(e)}")

# ОСТАЛЬНЫЕ КОМАНДЫ ВЛАДЕЛЬЦЕВ (промокоды)
@bot.message_handler(commands=['promolist'])
def promo_list_command(message):
    if message.date < BOT_START_TIME:
        return
        
    user_id = message.from_user.id
    
    if not is_owner(user_id):
        bot.send_message(message.chat.id, "❌ У вас нет прав!")
        return
    
    conn = sqlite3.connect('cats.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT code, reward_type, reward_value, uses_left, created_time 
        FROM promocodes 
        ORDER BY created_time DESC
    ''')
    promos = cursor.fetchall()
    conn.close()
    
    if not promos:
        bot.send_message(message.chat.id, "❌ Нет созданных промокодов!")
        return
    
    promos_text = "📋 Список промокодов:\n\n"
    
    for code, reward_type, reward_value, uses_left, created_time in promos:
        reward_display = f"{reward_value} монет" if reward_type == "coins" else reward_value
        uses_display = "∞" if uses_left == 0 else str(uses_left)
        promos_text += f"🎫 {code}\n"
        promos_text += f"🎁 {reward_display}\n"
        promos_text += f"🔄 Осталось: {uses_display}\n"
        promos_text += f"📅 Создан: {created_time[:10]}\n\n"
    
    bot.send_message(message.chat.id, promos_text)

@bot.message_handler(commands=['deletepromo'])
def delete_promo_command(message):
    if message.date < BOT_START_TIME:
        return
        
    user_id = message.from_user.id
    
    if not is_owner(user_id):
        bot.send_message(message.chat.id, "❌ У вас нет прав!")
        return
    
    try:
        parts = message.text.split()
        if len(parts) != 2:
            bot.send_message(message.chat.id, "❌ Используйте: /deletepromo КОД")
            return
            
        promo_code = parts[1].upper()
        
        conn = sqlite3.connect('cats.db')
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM promocodes WHERE code = ?', (promo_code,))
        cursor.execute('DELETE FROM used_promocodes WHERE promo_code = ?', (promo_code,))
        
        deleted_count = cursor.rowcount
        conn.commit()
        conn.close()
        
        if deleted_count > 0:
            bot.send_message(message.chat.id, f"✅ Промокод '{promo_code}' удален!")
        else:
            bot.send_message(message.chat.id, f"❌ Промокод '{promo_code}' не найден!")
            
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Ошибка: {str(e)}")

# КОМАНДЫ ВЛАДЕЛЬЦЕВ - ПРОМОКОДЫ
@bot.message_handler(commands=['createpromo'])
def create_promo_command(message):
    if message.date < BOT_START_TIME:
        return
        
    user_id = message.from_user.id
    
    if not is_owner(user_id):
        bot.send_message(message.chat.id, "❌ У вас нет прав для использования этой команды!")
        return
    
    PROMO_CREATION_STATES[user_id] = {"state": "waiting_promo_code"}
    bot.send_message(message.chat.id, 
                    "🎫 Введите код промокода (только латинские буквы и цифры):")

@bot.message_handler(func=lambda message: PROMO_CREATION_STATES.get(message.from_user.id, {}).get("state") == "waiting_promo_code")
def process_promo_code(message):
    if message.date < BOT_START_TIME:
        return
        
    user_id = message.from_user.id
    promo_code = message.text.strip().upper()
    
    if not promo_code.isalnum():
        bot.send_message(message.chat.id, "❌ Код промокода должен содержать только латинские буквы и цифры!")
        return
    
    conn = sqlite3.connect('cats.db')
    cursor = conn.cursor()
    cursor.execute('SELECT code FROM promocodes WHERE code = ?', (promo_code,))
    existing_promo = cursor.fetchone()
    conn.close()
    
    if existing_promo:
        bot.send_message(message.chat.id, f"❌ Промокод '{promo_code}' уже существует!")
        return
    
    PROMO_CREATION_STATES[user_id] = {
        "state": "waiting_reward_type",
        "promo_code": promo_code
    }
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("💰 Монеты", callback_data="promo_coins"))
    markup.add(types.InlineKeyboardButton("🎴 Карточка", callback_data="promo_card"))
    
    sent_message = bot.send_message(message.chat.id, 
                    f"🎁 Выберите тип награды для промокода '{promo_code}':", 
                    reply_markup=markup)
    
    store_message_owner(sent_message.message_id, user_id)

@bot.callback_query_handler(func=lambda call: call.data.startswith('promo_'))
def process_promo_reward_type(call):
    user_id = call.from_user.id
    
    if not check_message_owner(call.message.message_id, user_id):
        bot.answer_callback_query(call.id, "❌ Это не ваше меню!", show_alert=True)
        return
    
    if user_id not in PROMO_CREATION_STATES or "state" not in PROMO_CREATION_STATES[user_id]:
        bot.send_message(call.message.chat.id, "❌ Сессия истекла, начните заново!")
        return
    
    reward_type = call.data.split('_')[1]
    state_data = PROMO_CREATION_STATES[user_id]
    
    if reward_type == "coins":
        PROMO_CREATION_STATES[user_id] = {
            "state": "waiting_coins_amount",
            "promo_code": state_data["promo_code"],
            "reward_type": "coins"
        }
        bot.send_message(call.message.chat.id, "💰 Введите количество монет:")
        
    elif reward_type == "card":
        PROMO_CREATION_STATES[user_id] = {
            "state": "waiting_card_name",
            "promo_code": state_data["promo_code"],
            "reward_type": "card"
        }
        
        markup = types.InlineKeyboardMarkup()
        for card_name in CARDS_DATABASE.keys():
            rarity = CARDS_DATABASE[card_name]["rarity"]
            markup.add(types.InlineKeyboardButton(
                f"{rarity} {card_name}", 
                callback_data=f"promocard_{card_name}"
            ))
        
        sent_message = bot.send_message(call.message.chat.id, 
                        "🎴 Выберите карточку для награды:", 
                        reply_markup=markup)
        
        store_message_owner(sent_message.message_id, user_id)
    
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data.startswith('promocard_'))
def process_promo_card_selection(call):
    user_id = call.from_user.id
    
    if not check_message_owner(call.message.message_id, user_id):
        bot.answer_callback_query(call.id, "❌ Это не ваше меню!", show_alert=True)
        return
    
    if user_id not in PROMO_CREATION_STATES or "state" not in PROMO_CREATION_STATES[user_id]:
        bot.send_message(call.message.chat.id, "❌ Сессия истекла, начните заново!")
        return
    
    card_name = call.data.split('_', 1)[1]
    state_data = PROMO_CREATION_STATES[user_id]
    
    PROMO_CREATION_STATES[user_id] = {
        "state": "waiting_promo_uses",
        "promo_code": state_data["promo_code"],
        "reward_type": "card",
        "reward_value": card_name
    }
    
    bot.send_message(call.message.chat.id, 
                    f"🔄 Введите количество использований промокода (0 = бесконечно):\n"
                    f"Карточка: {card_name}")
    
    bot.answer_callback_query(call.id)

@bot.message_handler(func=lambda message: PROMO_CREATION_STATES.get(message.from_user.id, {}).get("state") == "waiting_coins_amount")
def process_promo_coins_amount(message):
    if message.date < BOT_START_TIME:
        return
        
    user_id = message.from_user.id
    state_data = PROMO_CREATION_STATES[user_id]
    
    try:
        coins_amount = int(message.text.strip())
        if coins_amount <= 0:
            bot.send_message(message.chat.id, "❌ Количество монет должно быть положительным!")
            return
            
        PROMO_CREATION_STATES[user_id] = {
            "state": "waiting_promo_uses",
            "promo_code": state_data["promo_code"],
            "reward_type": "coins",
            "reward_value": str(coins_amount)
        }
        
        bot.send_message(message.chat.id, 
                        f"🔄 Введите количество использований промокода (0 = бесконечно):\n"
                        f"Монеты: {coins_amount}")
        
    except ValueError:
        bot.send_message(message.chat.id, "❌ Пожалуйста, введите корректное число!")

@bot.message_handler(func=lambda message: PROMO_CREATION_STATES.get(message.from_user.id, {}).get("state") == "waiting_promo_uses")
def process_promo_uses(message):
    if message.date < BOT_START_TIME:
        return
        
    user_id = message.from_user.id
    state_data = PROMO_CREATION_STATES[user_id]
    
    try:
        uses = int(message.text.strip())
        if uses < 0:
            bot.send_message(message.chat.id, "❌ Количество использований не может быть отрицательным!")
            return
        
        conn = sqlite3.connect('cats.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO promocodes (code, reward_type, reward_value, uses_left, created_by)
            VALUES (?, ?, ?, ?, ?)
        ''', (state_data["promo_code"], state_data["reward_type"], state_data["reward_value"], uses, user_id))
        
        conn.commit()
        conn.close()
        
        if state_data["reward_type"] == "coins":
            reward_text = f"💰 {state_data['reward_value']} монет"
        else:
            reward_text = f"🎴 {state_data['reward_value']}"
            
        uses_text = "бесконечно" if uses == 0 else f"{uses} раз"
        
        success_message = f"""✅ Промокод успешно создан!

🎫 Код: {state_data['promo_code']}
🎁 Награда: {reward_text}
🔄 Использований: {uses_text}"""

        bot.send_message(message.chat.id, success_message)
        
        del PROMO_CREATION_STATES[user_id]
        
    except ValueError:
        bot.send_message(message.chat.id, "❌ Пожалуйста, введите корректное число!")

# ОБНОВЛЕННЫЙ РЕДАКТОР КАРТОЧЕК С СОХРАНЕНИЕМ
@bot.message_handler(commands=['editcard'])
def edit_card_command(message):
    if message.date < BOT_START_TIME:
        return
        
    user_id = message.from_user.id
    
    if not is_owner(user_id):
        bot.send_message(message.chat.id, "❌ У вас нет прав для использования этой команды!")
        return
    
    markup = types.InlineKeyboardMarkup()
    for card_name in CARDS_DATABASE.keys():
        rarity = CARDS_DATABASE[card_name]["rarity"]
        markup.add(types.InlineKeyboardButton(
            f"{rarity} {card_name}", 
            callback_data=f"editcard_{card_name}"
        ))
    
    sent_message = bot.send_message(message.chat.id, 
                    "🎴 Выберите карточку для редактирования:", 
                    reply_markup=markup)
    
    store_message_owner(sent_message.message_id, user_id)

@bot.callback_query_handler(func=lambda call: call.data.startswith('editcard_'))
def process_edit_card_selection(call):
    user_id = call.from_user.id
    
    if not check_message_owner(call.message.message_id, user_id):
        bot.answer_callback_query(call.id, "❌ Это не ваше меню!", show_alert=True)
        return
    
    if not is_owner(user_id):
        bot.answer_callback_query(call.id, "❌ У вас нет прав!", show_alert=True)
        return
    
    card_name = call.data.split('_', 1)[1]
    
    CARD_EDIT_STATES[user_id] = {
        "state": "waiting_edit_field",
        "card_name": card_name
    }
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("📝 Описание", callback_data=f"editfield_description"))
    markup.add(types.InlineKeyboardButton("💰 Монеты", callback_data=f"editfield_coins"))
    markup.add(types.InlineKeyboardButton("⭐️ Редкость", callback_data=f"editfield_rarity"))
    markup.add(types.InlineKeyboardButton("🖼 Изображение", callback_data=f"editfield_image"))
    markup.add(types.InlineKeyboardButton("🔨 Тип карточки", callback_data=f"editfield_craft_type"))
    
    card_data = CARDS_DATABASE[card_name]
    current_info = f"""📋 Текущие данные карточки:

📝 Название: {card_name}
📝 Описание: {card_data['description']}
💰 Монеты: {card_data['coins']}
⭐️ Редкость: {card_data['rarity']} {RARITIES[card_data['rarity']]['name']}
🔨 Тип: {'Только крафт' if card_data.get('craft_only', False) else 'Обычная'}"""

    sent_message = bot.send_message(call.message.chat.id, 
                    f"{current_info}\n\nЧто вы хотите изменить?", 
                    reply_markup=markup)
    
    store_message_owner(sent_message.message_id, user_id)
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data.startswith('editfield_'))
def process_edit_field_selection(call):
    user_id = call.from_user.id
    
    if not check_message_owner(call.message.message_id, user_id):
        bot.answer_callback_query(call.id, "❌ Это не ваше меню!", show_alert=True)
        return
    
    if user_id not in CARD_EDIT_STATES:
        bot.send_message(call.message.chat.id, "❌ Сессия истекла!")
        return
    
    field = call.data.split('_')[1]
    card_name = CARD_EDIT_STATES[user_id]["card_name"]
    
    CARD_EDIT_STATES[user_id] = {
        "state": f"waiting_edit_{field}",
        "card_name": card_name,
        "field": field
    }
    
    if field == "description":
        bot.send_message(call.message.chat.id, "📝 Введите новое описание карточки:")
    elif field == "coins":
        bot.send_message(call.message.chat.id, "💰 Введите новое количество монет:")
    elif field == "rarity":
        markup = types.InlineKeyboardMarkup()
        for rarity in RARITIES.keys():
            markup.add(types.InlineKeyboardButton(
                f"{rarity} {RARITIES[rarity]['name']}", 
                callback_data=f"editrarity_{rarity}"
            ))
        sent_message = bot.send_message(call.message.chat.id, "⭐️ Выберите новую редкость:", reply_markup=markup)
        store_message_owner(sent_message.message_id, user_id)
    elif field == "image":
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📸 Отправить фото", callback_data="editimage_photo"))
        markup.add(types.InlineKeyboardButton("🔗 Ввести URL", callback_data="editimage_url"))
        sent_message = bot.send_message(call.message.chat.id, "🖼 Как вы хотите изменить изображение?", reply_markup=markup)
        store_message_owner(sent_message.message_id, user_id)
    elif field == "craft_type":
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔨 Сделать только для крафта", callback_data="editcrafttype_yes"))
        markup.add(types.InlineKeyboardButton("🎴 Сделать обычной", callback_data="editcrafttype_no"))
        sent_message = bot.send_message(call.message.chat.id, "🔨 Изменить тип карточки:", reply_markup=markup)
        store_message_owner(sent_message.message_id, user_id)
    
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data.startswith('editimage_'))
def process_edit_image_method(call):
    user_id = call.from_user.id
    
    if not check_message_owner(call.message.message_id, user_id):
        bot.answer_callback_query(call.id, "❌ Это не ваше меню!", show_alert=True)
        return
    
    if user_id not in CARD_EDIT_STATES:
        bot.send_message(call.message.chat.id, "❌ Сессия истекла!")
        return
    
    method = call.data.split('_')[1]
    
    if method == "photo":
        bot.send_message(call.message.chat.id, "📸 Отправьте новое фото для карточки:")
    elif method == "url":
        bot.send_message(call.message.chat.id, "🔗 Введите новый URL изображения для карточки:")
    
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data.startswith('editrarity_'))
def process_edit_rarity(call):
    user_id = call.from_user.id
    
    if not check_message_owner(call.message.message_id, user_id):
        bot.answer_callback_query(call.id, "❌ Это не ваше меню!", show_alert=True)
        return
    
    if user_id not in CARD_EDIT_STATES:
        bot.send_message(call.message.chat.id, "❌ Сессия истекла!")
        return
    
    rarity = call.data.split('_')[1]
    card_name = CARD_EDIT_STATES[user_id]["card_name"]
    
    CARDS_DATABASE[card_name]["rarity"] = rarity
    CARDS_DATABASE[card_name]["coins"] = RARITIES[rarity]["coins"]
    
    save_cards_database()
    
    bot.send_message(call.message.chat.id, 
                    f"✅ Редкость карточки '{card_name}' изменена на {rarity} {RARITIES[rarity]['name']}")
    
    del CARD_EDIT_STATES[user_id]
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data.startswith('editcrafttype_'))
def process_edit_craft_type(call):
    user_id = call.from_user.id
    
    if not check_message_owner(call.message.message_id, user_id):
        bot.answer_callback_query(call.id, "❌ Это не ваше меню!", show_alert=True)
        return
    
    if user_id not in CARD_EDIT_STATES:
        bot.send_message(call.message.chat.id, "❌ Сессия истекла!")
        return
    
    choice = call.data.split('_')[1]
    card_name = CARD_EDIT_STATES[user_id]["card_name"]
    
    craft_only = (choice == "yes")
    CARDS_DATABASE[card_name]["craft_only"] = craft_only
    
    save_cards_database()
    
    status = "только для крафта" if craft_only else "обычная"
    bot.send_message(call.message.chat.id, 
                    f"✅ Карточка '{card_name}' теперь {status}")
    
    del CARD_EDIT_STATES[user_id]
    bot.answer_callback_query(call.id)

@bot.message_handler(func=lambda message: CARD_EDIT_STATES.get(message.from_user.id, {}).get("state") == "waiting_edit_description")
def process_edit_description(message):
    if message.date < BOT_START_TIME:
        return
        
    user_id = message.from_user.id
    state_data = CARD_EDIT_STATES[user_id]
    card_name = state_data["card_name"]
    
    new_description = message.text.strip()
    CARDS_DATABASE[card_name]["description"] = new_description
    
    save_cards_database()
    
    bot.send_message(message.chat.id, 
                    f"✅ Описание карточки '{card_name}' обновлено!")
    
    del CARD_EDIT_STATES[user_id]

@bot.message_handler(func=lambda message: CARD_EDIT_STATES.get(message.from_user.id, {}).get("state") == "waiting_edit_coins")
def process_edit_coins(message):
    if message.date < BOT_START_TIME:
        return
        
    user_id = message.from_user.id
    state_data = CARD_EDIT_STATES[user_id]
    card_name = state_data["card_name"]
    
    try:
        new_coins = int(message.text.strip())
        if new_coins <= 0:
            bot.send_message(message.chat.id, "❌ Количество монет должно быть положительным!")
            return
        
        CARDS_DATABASE[card_name]["coins"] = new_coins
        
        save_cards_database()
        
        bot.send_message(message.chat.id, 
                        f"✅ Количество монет для карточки '{card_name}' изменено на {new_coins}")
        
        del CARD_EDIT_STATES[user_id]
        
    except ValueError:
        bot.send_message(message.chat.id, "❌ Пожалуйста, введите корректное число!")

@bot.message_handler(content_types=['photo'], 
                    func=lambda message: CARD_EDIT_STATES.get(message.from_user.id, {}).get("state") == "waiting_edit_image")
def process_edit_image_photo(message):
    if message.date < BOT_START_TIME:
        return
        
    user_id = message.from_user.id
    state_data = CARD_EDIT_STATES[user_id]
    card_name = state_data["card_name"]
    
    try:
        file_id = message.photo[-1].file_id
        file_info = bot.get_file(file_id)
        file_url = f"https://api.telegram.org/file/bot{bot.token}/{file_info.file_path}"
        
        CARDS_DATABASE[card_name]["image"] = file_url
        
        save_cards_database()
        
        bot.send_message(message.chat.id, 
                        f"✅ Изображение карточки '{card_name}' обновлено!")
        
        del CARD_EDIT_STATES[user_id]
        
    except Exception as e:
        logger.error(f"Error processing photo: {e}")
        bot.send_message(message.chat.id, "❌ Ошибка при обработке фото!")

@bot.message_handler(func=lambda message: CARD_EDIT_STATES.get(message.from_user.id, {}).get("state") == "waiting_edit_image")
def process_edit_image_url(message):
    if message.date < BOT_START_TIME:
        return
        
    user_id = message.from_user.id
    state_data = CARD_EDIT_STATES[user_id]
    card_name = state_data["card_name"]
    url = message.text.strip()
    
    if not is_valid_url(url):
        bot.send_message(message.chat.id, "❌ Неверный URL! Убедитесь, что ссылка начинается с http:// или https://")
        return
    
    CARDS_DATABASE[card_name]["image"] = url
    
    save_cards_database()
    
    bot.send_message(message.chat.id, 
                    f"✅ Изображение карточки '{card_name}' обновлено!")
    
    del CARD_EDIT_STATES[user_id]

# ОСНОВНЫЕ КОМАНДЫ С ПРОВЕРКОЙ БАНА
@bot.message_handler(commands=['start'])
@check_ban
def start_command(message):
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name

    get_user(user_id, username)

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton('🎴 Получить карточку')
    btn2 = types.KeyboardButton('📊 Мой профиль')
    btn3 = types.KeyboardButton('📋 Мои карточки')
    btn4 = types.KeyboardButton('🛒 Магазин')
    btn5 = types.KeyboardButton('📚 Все карточки')
    btn6 = types.KeyboardButton('🔨 Крафт')
    markup.add(btn1, btn2, btn3, btn4)
    markup.add(btn5, btn6)

    welcome_text = f"""🐱 Добро пожаловать в мир карточек с котами, {username}!

✨ Доступные команды:
• 🎴 Получить карточку
• 📊 Мой профиль  
• 📋 Мои карточки
• 🛒 Магазин
• 📚 Все карточки
• 🔨 Крафт

🎁 Для получения бонусов зайдите в нашего бота @CardsCatsBot

💡 *Магазин работает только в личных сообщениях с ботом!*"""

    bot.send_message(message.chat.id, welcome_text, reply_markup=markup, parse_mode='Markdown')
    
@bot.message_handler(func=lambda message: message.text == '🎴 Получить карточку')
@check_ban
def get_card(message):
    user_id = message.from_user.id
    
    if not check_button_cooldown(user_id, 'get_card'):
        bot.send_message(message.chat.id, "⏳ Подождите немного перед следующим получением карточки!")
        return
    
    username = message.from_user.username or message.from_user.first_name
    get_user(user_id, username)
    
    conn = sqlite3.connect('cats.db')
    cursor = conn.cursor()
    cursor.execute('SELECT last_card_time FROM cooldowns WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    
    current_time = int(time.time())
    cooldown_seconds = 2 * 3600
    
    if result and (current_time - result[0]) < cooldown_seconds:
        time_left = cooldown_seconds - (current_time - result[0])
        hours = time_left // 3600
        minutes = (time_left % 3600) // 60
        bot.send_message(message.chat.id, f"⏰ Следующую карточку можно будет получить через: {hours}ч {minutes}м")
        conn.close()
        return
    
    card_name = get_random_card()
    card_data = CARDS_DATABASE[card_name]
    
    cursor.execute('UPDATE users SET coins = coins + ?, total_cards = total_cards + 1 WHERE user_id = ?',
                   (card_data["coins"], user_id))
    cursor.execute('INSERT OR REPLACE INTO cooldowns (user_id, last_card_time) VALUES (?, ?)',
                   (user_id, current_time))
    cursor.execute('INSERT INTO user_cards (user_id, rarity, card_name) VALUES (?, ?, ?)',
                   (user_id, card_data["rarity"], card_name))
    
    conn.commit()
    conn.close()
    
    card_text = f"""Вам выпала карточка!

🖼 Карточка: "{card_name}"
⭐️ Редкость: {card_data['rarity']} {RARITIES[card_data['rarity']]['name']}
💰 Монеты: +{card_data['coins']} монет 
📝 Описание: {card_data['description']}"""

    try:
        bot.send_photo(message.chat.id, card_data['image'], caption=card_text)
    except Exception as e:
        logger.error(f"Error sending photo: {e}")
        bot.send_message(message.chat.id, card_text)

@bot.message_handler(func=lambda message: message.text == '📊 Мой профиль')
@check_ban
def show_stats(message):
    user_id = message.from_user.id
    
    if not check_button_cooldown(user_id, 'profile'):
        bot.send_message(message.chat.id, "⏳ Подождите немного перед следующим просмотром профиля!")
        return
    
    conn = sqlite3.connect('cats.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT coins, total_cards FROM users WHERE user_id = ?', (user_id,))
    user_stats = cursor.fetchone()
    
    if not user_stats:
        bot.send_message(message.chat.id, "❌ Вы ещё не начали собирать карточки!")
        conn.close()
        return

    coins, total_cards = user_stats

    cursor.execute('''
        SELECT rarity, COUNT(*) as count 
        FROM user_cards 
        WHERE user_id = ? 
        GROUP BY rarity 
        ORDER BY count DESC
    ''', (user_id,))
    cards_by_rarity = cursor.fetchall()
    conn.close()

    stats_text = f"""📊 Ваша статистика:

💰 Монеты: {coins} монет
🎴 Всего карточек: {total_cards} шт.

📈 Коллекция по редкостям:"""

    for rarity, count in cards_by_rarity:
        rarity_name = RARITIES[rarity]["name"]
        stats_text += f"\n{rarity} {rarity_name}: {count} шт."

    bot.send_message(message.chat.id, stats_text)

@bot.message_handler(func=lambda message: message.text == '📋 Мои карточки')
@check_ban
def show_cards(message):
    user_id = message.from_user.id
    
    if not check_button_cooldown(user_id, 'my_cards'):
        bot.send_message(message.chat.id, "⏳ Подождите немного перед следующим просмотром карточек!")
        return
    
    conn = sqlite3.connect('cats.db')
    cursor = conn.cursor()

    cursor.execute('''
        SELECT rarity, card_name, obtained_date 
        FROM user_cards 
        WHERE user_id = ? 
        ORDER BY obtained_date DESC 
        LIMIT 20
    ''', (user_id,))
    cards = cursor.fetchall()
    conn.close()

    if not cards:
        bot.send_message(message.chat.id, "❌ У вас пока нет карточек!")
        return

    cards_text = "📋 Ваши последние карточки:\n\n"

    for i, (rarity, card_name, date) in enumerate(cards, 1):
        rarity_name = RARITIES[rarity]["name"]
        cards_text += f"{i}. {rarity} {card_name} ({rarity_name})\n"

    bot.send_message(message.chat.id, cards_text)

@bot.message_handler(func=lambda message: message.text == '🛒 Магазин')
@check_ban
def shop_menu(message):
    user_id = message.from_user.id
    
    # Проверяем, что это личные сообщения с ботом
    if message.chat.type != 'private':
        bot.send_message(message.chat.id, "❌ Магазин работает только в личных сообщениях с ботом! Напишите мне в ЛС.")
        return
    
    if not check_button_cooldown(user_id, 'shop'):
        bot.send_message(message.chat.id, "⏳ Подождите немного перед следующим действием в магазине!")
        return
    
    # Проверяем, включен ли магазин
    if not SHOP_ENABLED:
        bot.send_message(message.chat.id, "❌ Магазин временно отключен администратором!")
        return
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton('💰 Купить карточки')
    btn2 = types.KeyboardButton('💎 Продать карточки')
    btn3 = types.KeyboardButton('📋 Мои объявления')
    btn4 = types.KeyboardButton('🎴 Получить карточку')
    btn5 = types.KeyboardButton('📊 Мой профиль')
    markup.add(btn1, btn2, btn3)
    markup.add(btn4, btn5)

    shop_text = """🛒 Добро пожаловать в магазин карточек!

💰 **Купить карточки** - просмотреть карточки других игроков
💎 **Продать карточки** - выставить свои карточки на продажу
📋 **Мои объявления** - управление вашими продажами

⏰ *Внимание: процесс продажи отменяется через 20 секунд бездействия*"""

    bot.send_message(message.chat.id, shop_text, reply_markup=markup, parse_mode='Markdown')

@bot.message_handler(func=lambda message: message.text == '📚 Все карточки')
@check_ban
def all_cards_menu(message):
    user_id = message.from_user.id
    
    if not check_button_cooldown(user_id, 'all_cards'):
        bot.send_message(message.chat.id, "⏳ Подождите немного перед следующим просмотром!")
        return
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("📖 Просмотр всех карточек", callback_data="view_all_cards"))
    markup.add(types.InlineKeyboardButton("📊 Список моих карточек", callback_data="view_my_collection"))
    
    bot.send_message(message.chat.id, 
                    "📚 Выберите режим просмотра карточек:",
                    reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == '🔨 Крафт')
@check_ban
def craft_menu(message):
    user_id = message.from_user.id
    
    if not check_button_cooldown(user_id, 'craft'):
        bot.send_message(message.chat.id, "⏳ Подождите немного перед следующим действием!")
        return
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("📖 Просмотр рецептов крафта", callback_data="view_craft_recipes"))
    markup.add(types.InlineKeyboardButton("🔨 Создать карточку", callback_data="start_craft"))
    
    bot.send_message(message.chat.id,
                    "🔨 Мастерская крафта:\n\n"
                    "Здесь вы можете создавать уникальные карточки, объединяя другие карточки!",
                    reply_markup=markup)

# ОБРАБОТЧИК КНОПОК ДЛЯ ПРОСМОТРА КАРТОЧЕК И КРАФТА
@bot.callback_query_handler(func=lambda call: call.data.startswith(('view_', 'craft_', 'select_craft_card_', 'page_', 'craft_recipe_')))
@check_ban_callback
def handle_view_callback(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id

    if not check_button_cooldown(user_id, 'all_cards'):
        bot.answer_callback_query(call.id, "⏳ Подождите немного перед следующим действием!", show_alert=True)
        return

    if call.data == 'view_all_cards':
        show_all_cards_page(call.message, user_id, 0)
        
    elif call.data == 'view_my_collection':
        show_user_collection_page(call.message, user_id, 0)
        
    elif call.data == 'view_craft_recipes':
        show_craft_recipes(call.message, user_id)
        
    elif call.data == 'start_craft':
        start_craft_selection(call.message, user_id)
        
    elif call.data.startswith('select_craft_card_'):
        card_name = call.data.split('_', 3)[3]
        process_craft_selection(call.message, user_id, card_name)
        
    elif call.data.startswith('page_all_'):
        page = int(call.data.split('_')[2])
        show_all_cards_page(call.message, user_id, page)
        
    elif call.data.startswith('page_my_'):
        page = int(call.data.split('_')[2])
        show_user_collection_page(call.message, user_id, page)
        
    elif call.data.startswith('craft_recipe_'):
        card_name = call.data.split('_', 2)[2]
        show_recipe_details(call.message, user_id, card_name)

    bot.answer_callback_query(call.id)

# ФУНКЦИИ ДЛЯ ПРОСМОТРА КАРТОЧЕК
def show_all_cards_page(message, user_id, page):
    cards_per_page = 10
    all_cards = list(CARDS_DATABASE.keys())
    total_pages = (len(all_cards) + cards_per_page - 1) // cards_per_page
    
    start_idx = page * cards_per_page
    end_idx = start_idx + cards_per_page
    page_cards = all_cards[start_idx:end_idx]
    
    conn = sqlite3.connect('cats.db')
    cursor = conn.cursor()
    
    text = f"📚 Все карточки (Страница {page + 1}/{total_pages}):\n\n"
    
    for i, card_name in enumerate(page_cards, start_idx + 1):
        card_data = CARDS_DATABASE[card_name]
        
        # Проверяем, есть ли карточка у пользователя
        cursor.execute('SELECT id FROM user_cards WHERE user_id = ? AND card_name = ?', (user_id, card_name))
        has_card = cursor.fetchone() is not None
        
        status = "✅" if has_card else "❌"
        craft_only = "🔨" if card_data.get('craft_only', False) else ""
        
        text += f"{status} {craft_only} {i}. {card_data['rarity']} {card_name}\n"
    
    conn.close()
    
    markup = types.InlineKeyboardMarkup()
    
    # Кнопки навигации
    nav_buttons = []
    if page > 0:
        nav_buttons.append(types.InlineKeyboardButton("⬅️ Назад", callback_data=f"page_all_{page-1}"))
    if page < total_pages - 1:
        nav_buttons.append(types.InlineKeyboardButton("Вперед ➡️", callback_data=f"page_all_{page+1}"))
    
    if nav_buttons:
        markup.row(*nav_buttons)
    
    try:
        bot.edit_message_text(text, message.chat.id, message.message_id, reply_markup=markup)
    except:
        bot.send_message(message.chat.id, text, reply_markup=markup)

def show_user_collection_page(message, user_id, page):
    cards_per_page = 10
    
    conn = sqlite3.connect('cats.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(DISTINCT card_name) FROM user_cards WHERE user_id = ?', (user_id,))
    total_user_cards = cursor.fetchone()[0]
    total_pages = (total_user_cards + cards_per_page - 1) // cards_per_page
    
    cursor.execute('''
        SELECT card_name, COUNT(*) as count 
        FROM user_cards 
        WHERE user_id = ? 
        GROUP BY card_name 
        ORDER BY card_name
        LIMIT ? OFFSET ?
    ''', (user_id, cards_per_page, page * cards_per_page))
    
    user_cards = cursor.fetchall()
    conn.close()
    
    text = f"📊 Моя коллекция (Страница {page + 1}/{total_pages}):\n\n"
    
    for card_name, count in user_cards:
        if card_name in CARDS_DATABASE:
            card_data = CARDS_DATABASE[card_name]
            craft_only = "🔨" if card_data.get('craft_only', False) else ""
            text += f"✅ {craft_only} {card_data['rarity']} {card_name} ×{count}\n"
        else:
            text += f"✅ {card_name} ×{count}\n"
    
    markup = types.InlineKeyboardMarkup()
    
    # Кнопки навигации
    nav_buttons = []
    if page > 0:
        nav_buttons.append(types.InlineKeyboardButton("⬅️ Назад", callback_data=f"page_my_{page-1}"))
    if page < total_pages - 1:
        nav_buttons.append(types.InlineKeyboardButton("Вперед ➡️", callback_data=f"page_my_{page+1}"))
    
    if nav_buttons:
        markup.row(*nav_buttons)
    
    try:
        bot.edit_message_text(text, message.chat.id, message.message_id, reply_markup=markup)
    except:
        bot.send_message(message.chat.id, text, reply_markup=markup)

# ФУНКЦИИ ДЛЯ КРАФТА
def show_craft_recipes(message, user_id):
    if not CRAFT_RECIPES:
        bot.send_message(message.chat.id, "❌ Пока нет доступных рецептов крафта!")
        return
    
    text = "🔨 Доступные рецепты крафта:\n\n"
    
    for result_card, recipe in CRAFT_RECIPES.items():
        if result_card in CARDS_DATABASE:
            card_data = CARDS_DATABASE[result_card]
            text += f"{card_data['rarity']} {result_card}:\n"
            
            for ingredient, amount in recipe['ingredients'].items():
                text += f"  - {ingredient} ×{amount}\n"
            text += "\n"
    
    markup = types.InlineKeyboardMarkup()
    for result_card in list(CRAFT_RECIPES.keys())[:10]:  # Ограничиваем количество кнопок
        if result_card in CARDS_DATABASE:
            card_data = CARDS_DATABASE[result_card]
            markup.add(types.InlineKeyboardButton(
                f"{card_data['rarity']} {result_card}", 
                callback_data=f"craft_recipe_{result_card}"
            ))
    
    sent_message = bot.send_message(message.chat.id, text, reply_markup=markup)
    store_message_owner(sent_message.message_id, user_id)

def show_recipe_details(message, user_id, card_name):
    if card_name not in CRAFT_RECIPES:
        bot.send_message(message.chat.id, "❌ Рецепт не найден!")
        return
    
    recipe = CRAFT_RECIPES[card_name]
    card_data = CARDS_DATABASE[card_name]
    
    text = f"🔨 Рецепт крафта:\n\n"
    text += f"🎯 Результат: {card_data['rarity']} {card_name}\n\n"
    text += "📦 Ингредиенты:\n"
    
    conn = sqlite3.connect('cats.db')
    cursor = conn.cursor()
    
    can_craft = True
    for ingredient, amount in recipe['ingredients'].items():
        cursor.execute('SELECT COUNT(*) FROM user_cards WHERE user_id = ? AND card_name = ?', 
                      (user_id, ingredient))
        user_has = cursor.fetchone()[0]
        status = "✅" if user_has >= amount else "❌"
        if user_has < amount:
            can_craft = False
        text += f"{status} {ingredient} ×{amount} (у вас: {user_has})\n"
    
    conn.close()
    
    markup = types.InlineKeyboardMarkup()
    if can_craft:
        markup.add(types.InlineKeyboardButton("🔨 Скрафтить", callback_data=f"select_craft_card_{card_name}"))
    markup.add(types.InlineKeyboardButton("⬅️ Назад", callback_data="view_craft_recipes"))
    
    try:
        bot.edit_message_text(text, message.chat.id, message.message_id, reply_markup=markup)
    except:
        bot.send_message(message.chat.id, text, reply_markup=markup)

def start_craft_selection(message, user_id):
    if not CRAFT_RECIPES:
        bot.send_message(message.chat.id, "❌ Пока нет доступных рецептов крафта!")
        return
    
    markup = types.InlineKeyboardMarkup()
    craftable_cards = []
    
    conn = sqlite3.connect('cats.db')
    cursor = conn.cursor()
    
    for result_card, recipe in CRAFT_RECIPES.items():
        if result_card in CARDS_DATABASE:
            can_craft = True
            for ingredient, amount in recipe['ingredients'].items():
                cursor.execute('SELECT COUNT(*) FROM user_cards WHERE user_id = ? AND card_name = ?', 
                              (user_id, ingredient))
                user_has = cursor.fetchone()[0]
                if user_has < amount:
                    can_craft = False
                    break
            
            if can_craft:
                craftable_cards.append(result_card)
    
    conn.close()
    
    if not craftable_cards:
        bot.send_message(message.chat.id, "❌ У вас нет необходимых карточек для крафта!")
        return
    
    for card_name in craftable_cards[:10]:  # Ограничиваем количество кнопок
        card_data = CARDS_DATABASE[card_name]
        markup.add(types.InlineKeyboardButton(
            f"{card_data['rarity']} {card_name}", 
            callback_data=f"select_craft_card_{card_name}"
        ))
    
    markup.add(types.InlineKeyboardButton("⬅️ Назад", callback_data="view_craft_recipes"))
    
    text = "🔨 Выберите карточку для крафта:\n\n*Доступные для крафта карточки:*"
    
    try:
        bot.edit_message_text(text, message.chat.id, message.message_id, reply_markup=markup)
    except:
        bot.send_message(message.chat.id, text, reply_markup=markup)

def process_craft_selection(message, user_id, card_name):
    if card_name not in CRAFT_RECIPES:
        bot.send_message(message.chat.id, "❌ Рецепт не найден!")
        return
    
    recipe = CRAFT_RECIPES[card_name]
    card_data = CARDS_DATABASE[card_name]
    
    conn = sqlite3.connect('cats.db')
    cursor = conn.cursor()
    
    # Проверяем, что у пользователя все еще есть необходимые карточки
    can_craft = True
    for ingredient, amount in recipe['ingredients'].items():
        cursor.execute('SELECT COUNT(*) FROM user_cards WHERE user_id = ? AND card_name = ?', 
                      (user_id, ingredient))
        user_has = cursor.fetchone()[0]
        if user_has < amount:
            can_craft = False
            break
    
    if not can_craft:
        bot.send_message(message.chat.id, "❌ У вас больше нет необходимых карточек для крафта!")
        conn.close()
        return
    
    # Удаляем карточки-ингредиенты
    for ingredient, amount in recipe['ingredients'].items():
        cursor.execute('''
            DELETE FROM user_cards 
            WHERE id IN (
                SELECT id FROM user_cards 
                WHERE user_id = ? AND card_name = ? 
                LIMIT ?
            )
        ''', (user_id, ingredient, amount))
    
    # Добавляем новую карточку
    cursor.execute('INSERT INTO user_cards (user_id, rarity, card_name) VALUES (?, ?, ?)',
                  (user_id, card_data["rarity"], card_name))
    cursor.execute('UPDATE users SET coins = coins + ?, total_cards = total_cards - ? + 1 WHERE user_id = ?',
                  (card_data["coins"], sum(recipe['ingredients'].values()), user_id))
    
    conn.commit()
    conn.close()
    
    success_text = f"""✅ Карточка успешно создана!

🎯 Результат: {card_data['rarity']} {card_name}
💰 Монеты: +{card_data['coins']} монет
📝 Описание: {card_data['description']}"""

    try:
        bot.send_photo(message.chat.id, card_data['image'], caption=success_text)
    except:
        bot.send_message(message.chat.id, success_text)
    
    # Возвращаемся к списку рецептов
    show_craft_recipes(message, user_id)

# УЛУЧШЕННЫЕ ФУНКЦИИ МАГАЗИНА С ТАЙМАУТОМ 20 СЕКУНД
@bot.message_handler(func=lambda message: message.text == '💎 Продать карточки')
@check_ban
def sell_cards_menu(message):
    user_id = message.from_user.id
    
    # Проверяем, что это личные сообщения с ботом
    if message.chat.type != 'private':
        bot.send_message(message.chat.id, "❌ Магазин работает только в личных сообщениях с ботом! Напишите мне в ЛС.")
        return
    
    # Проверяем, включен ли магазин
    if not SHOP_ENABLED:
        bot.send_message(message.chat.id, "❌ Магазин временно отключен администратором!")
        return
    
    # Проверяем, не находится ли пользователь уже в процессе продажи
    if is_user_in_selling_state(user_id):
        bot.send_message(message.chat.id, "⏳ Вы уже находитесь в процессе продажи карточки! Завершите текущую продажу.")
        return
    
    if not check_button_cooldown(user_id, 'shop'):
        bot.send_message(message.chat.id, "⏳ Подождите немного перед следующим действием!")
        return
    
    conn = sqlite3.connect('cats.db')
    cursor = conn.cursor()

    cursor.execute('''
        SELECT uc.id, uc.card_name, uc.rarity 
        FROM user_cards uc 
        LEFT JOIN market m ON uc.id = m.card_id 
        WHERE uc.user_id = ? AND m.card_id IS NULL
        ORDER BY uc.obtained_date DESC
        LIMIT 20
    ''', (user_id,))

    cards = cursor.fetchall()
    conn.close()

    if not cards:
        bot.send_message(message.chat.id, "❌ У вас нет карточек для продажи!")
        return

    markup = types.InlineKeyboardMarkup()

    for card_id, card_name, rarity in cards:
        rarity_name = RARITIES[rarity]["name"]
        btn_text = f"{rarity} {card_name}"
        callback_data = f"sell_{card_id}"
        markup.add(types.InlineKeyboardButton(btn_text, callback_data=callback_data))

    markup.add(types.InlineKeyboardButton("❌ Отмена", callback_data="cancel_sell_menu"))

    sent_message = bot.send_message(message.chat.id, 
                                   "💎 Выберите карточку для продажи:\n\n⏰ *Процесс продажи автоматически отменится через 20 секунд бездействия*", 
                                   reply_markup=markup,
                                   parse_mode='Markdown')
    store_message_owner(sent_message.message_id, user_id)

@bot.message_handler(func=lambda message: message.text == '💰 Купить карточки')
@check_ban
def buy_cards_menu(message):
    user_id = message.from_user.id
    
    # Проверяем, что это личные сообщения с ботом
    if message.chat.type != 'private':
        bot.send_message(message.chat.id, "❌ Магазин работает только в личных сообщениях с ботом! Напишите мне в ЛС.")
        return
    
    if not check_button_cooldown(user_id, 'shop'):
        bot.send_message(message.chat.id, "⏳ Подождите немного перед следующим действием!")
        return
    
    # Проверяем, включен ли магазин
    if not SHOP_ENABLED:
        bot.send_message(message.chat.id, "❌ Магазин временно отключен администратором!")
        return
    
    conn = sqlite3.connect('cats.db')
    cursor = conn.cursor()

    cursor.execute('''
        SELECT m.id, m.card_id, m.seller_id, m.price, u.username, uc.card_name, uc.rarity 
        FROM market m
        JOIN user_cards uc ON m.card_id = uc.id
        JOIN users u ON m.seller_id = u.user_id
        WHERE m.seller_id != ?
        ORDER BY m.listing_time DESC
        LIMIT 10
    ''', (user_id,))

    market_cards = cursor.fetchall()
    conn.close()

    if not market_cards:
        bot.send_message(message.chat.id, "❌ В магазине пока нет карточек для покупки!")
        return

    markup = types.InlineKeyboardMarkup()

    for market_id, card_id, seller_id, price, username, card_name, rarity in market_cards:
        btn_text = f"{rarity} {card_name} - {price} монет"
        callback_data = f"buy_{market_id}"
        markup.add(types.InlineKeyboardButton(btn_text, callback_data=callback_data))

    sent_message = bot.send_message(message.chat.id, "💰 Карточки в магазине:", reply_markup=markup)
    store_message_owner(sent_message.message_id, user_id)

@bot.message_handler(func=lambda message: message.text == '📋 Мои объявления')
@check_ban
def my_listings_menu(message):
    user_id = message.from_user.id
    
    # Проверяем, что это личные сообщения с ботом
    if message.chat.type != 'private':
        bot.send_message(message.chat.id, "❌ Магазин работает только в личных сообщениях с ботом! Напишите мне в ЛС.")
        return
    
    # Проверяем, включен ли магазин
    if not SHOP_ENABLED:
        bot.send_message(message.chat.id, "❌ Магазин временно отключен администратором!")
        return
    
    if not check_button_cooldown(user_id, 'shop'):
        bot.send_message(message.chat.id, "⏳ Подождите немного перед следующим действием!")
        return
    
    conn = sqlite3.connect('cats.db')
    cursor = conn.cursor()

    cursor.execute('''
        SELECT m.id, uc.card_name, uc.rarity, m.price 
        FROM market m
        JOIN user_cards uc ON m.card_id = uc.id
        WHERE m.seller_id = ?
        ORDER BY m.listing_time DESC
    ''', (user_id,))

    listings = cursor.fetchall()
    conn.close()

    if not listings:
        bot.send_message(message.chat.id, "❌ У вас нет активных объявлений!")
        return

    text = "📋 Ваши активные объявления:\n\n"
    markup = types.InlineKeyboardMarkup()

    for market_id, card_name, rarity, price in listings:
        text += f"• {rarity} {card_name} - {price} монет\n"
        callback_data = f"remove_{market_id}"
        markup.add(types.InlineKeyboardButton(f"❌ Снять с продажи: {card_name}", callback_data=callback_data))

    sent_message = bot.send_message(message.chat.id, text, reply_markup=markup)
    store_message_owner(sent_message.message_id, user_id)

# УЛУЧШЕННЫЙ ОБРАБОТЧИК КНОПОК МАГАЗИНА С ТАЙМАУТОМ 20 СЕКУНД
@bot.callback_query_handler(func=lambda call: call.data.startswith(('sell_', 'buy_', 'remove_', 'confirm_', 'cancel_', 'cancel_sell')))
@check_ban_callback
def handle_shop_callback(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id

    # Проверяем, включен ли магазин для всех операций кроме удаления объявлений
    if not call.data.startswith('remove_') and not SHOP_ENABLED:
        bot.answer_callback_query(call.id, "❌ Магазин временно отключен администратором!", show_alert=True)
        return

    if not check_message_owner(call.message.message_id, user_id):
        bot.answer_callback_query(call.id, "❌ Это не ваше меню!", show_alert=True)
        return

    if not check_button_cooldown(user_id, 'shop'):
        bot.answer_callback_query(call.id, "⏳ Подождите немного перед следующим действием!", show_alert=True)
        return

    if call.data.startswith('sell_'):
        card_id = int(call.data.split('_')[1])
        
        # Проверяем, не выбрана ли уже эта карточка
        if check_active_selection(user_id, card_id, 'sell'):
            bot.answer_callback_query(call.id, "❌ Вы уже выбрали эту карточку! Выберите другую.", show_alert=True)
            return
            
        # ПРОВЕРКА: Не выставлена ли карточка уже на продажу
        if is_card_already_selling(user_id, card_id):
            bot.answer_callback_query(call.id, "❌ Вы уже продаёте эту карточку!", show_alert=True)
            return
            
        conn = sqlite3.connect('cats.db')
        cursor = conn.cursor()
        cursor.execute('SELECT user_id FROM user_cards WHERE id = ?', (card_id,))
        card_owner = cursor.fetchone()
        conn.close()
        
        if not card_owner or card_owner[0] != user_id:
            bot.answer_callback_query(call.id, "❌ Эта карточка вам не принадлежит!", show_alert=True)
            return
        
        # Добавляем в активные выборы
        add_active_selection(user_id, card_id, 'sell')
        # Добавляем в состояние продажи
        add_card_selling_state(user_id, card_id)
        # Добавляем пользователя в состояние продажи
        add_user_selling_state(user_id, card_id)
        # Добавляем пользователя в состояние ввода цены
        add_user_price_input_state(user_id, card_id)
        
        # Удаляем сообщение с выбором карточек
        try:
            bot.delete_message(chat_id, call.message.message_id)
        except:
            pass
            
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("❌ Отменить продажу", callback_data="cancel_sell_process"))
        
        msg = bot.send_message(chat_id, 
                              "💵 Введите цену продажи (в монетах):\n\n⏰ *Процесс продажи автоматически отменится через 20 секунд бездействия*", 
                              reply_markup=markup,
                              parse_mode='Markdown')
        bot.register_next_step_handler(msg, process_sell_price, card_id, user_id)

    elif call.data == 'cancel_sell_menu':
        # Отмена в меню выбора карточки
        bot.edit_message_text("❌ Процесс продажи отменен.", chat_id, call.message.message_id)
        remove_active_selection(user_id, 'sell')
        
    elif call.data == 'cancel_sell_process':
        # Отмена в процессе ввода цены
        bot.send_message(chat_id, "❌ Процесс продажи отменен.")
        remove_active_selection(user_id, 'sell')
        remove_card_selling_state(user_id, get_user_selling_card(user_id))
        remove_user_selling_state(user_id)
        remove_user_price_input_state(user_id)
        
    elif call.data.startswith('buy_'):
        market_id = int(call.data.split('_')[1])
        
        # Проверяем, не выбрана ли уже эта карточка для покупки
        if check_active_selection(user_id, market_id, 'buy'):
            bot.answer_callback_query(call.id, "❌ Вы уже выбирали эту карточку! Выберите другую.", show_alert=True)
            return
            
        # Добавляем в активные выборы
        add_active_selection(user_id, market_id, 'buy')
        
        buy_card_confirmation(chat_id, market_id, user_id, call.message.message_id)

    elif call.data.startswith('remove_'):
        market_id = int(call.data.split('_')[1])
        
        conn = sqlite3.connect('cats.db')
        cursor = conn.cursor()
        cursor.execute('SELECT seller_id, card_id FROM market WHERE id = ?', (market_id,))
        listing_info = cursor.fetchone()
        conn.close()
        
        if not listing_info or listing_info[0] != user_id:
            bot.answer_callback_query(call.id, "❌ Это объявление вам не принадлежит!", show_alert=True)
            return
            
        seller_id, card_id = listing_info
        remove_from_market(market_id, user_id)
        # Удаляем из состояния продажи
        remove_card_selling_state(user_id, card_id)
        bot.edit_message_text("✅ Объявление удалено!", chat_id, call.message.message_id)

    elif call.data.startswith('confirm_buy_'):
        market_id = int(call.data.split('_')[2])
        process_buy_card(chat_id, market_id, user_id, call.message.message_id)

    elif call.data == 'cancel_buy':
        # Удаляем из активных выборов при отмене
        remove_active_selection(user_id, 'buy')
        bot.edit_message_text("❌ Покупка отменена.", chat_id, call.message.message_id)

    bot.answer_callback_query(call.id)

# УЛУЧШЕННАЯ ФУНКЦИЯ ОБРАБОТКИ ЦЕНЫ С ТАЙМАУТОМ 20 СЕКУНД
def process_sell_price(message, card_id, user_id):
    if message.date < BOT_START_TIME:
        return
        
    # ПРОВЕРКА: Только тот пользователь, который начал продажу, может вводить цену
    if message.from_user.id != user_id:
        bot.send_message(message.chat.id, "❌ Это не ваш процесс продажи!")
        return
        
    # Проверяем бан
    if is_user_banned(user_id):
        bot.send_message(message.chat.id, "🚫 Вы забанены в боте!")
        cleanup_selling_states(user_id, card_id)
        return
        
    # Проверяем, включен ли магазин
    if not SHOP_ENABLED:
        bot.send_message(message.chat.id, "❌ Магазин временно отключен администратором!")
        cleanup_selling_states(user_id, card_id)
        return
        
    # Проверяем, что пользователь все еще находится в состоянии ввода цены для этой карточки
    if not is_user_in_price_input_state(user_id) or get_user_price_input_card(user_id) != card_id:
        bot.send_message(message.chat.id, "❌ Сессия продажи истекла. Начните заново.")
        cleanup_selling_states(user_id, card_id)
        return
        
    # Проверяем таймаут (20 секунд)
    if user_id in USER_PRICE_INPUT_STATES:
        start_time = USER_PRICE_INPUT_STATES[user_id]['start_time']
        if time.time() - start_time > 20:
            bot.send_message(message.chat.id, "❌ Время на ввод цены истекло. Начните продажу заново.")
            cleanup_selling_states(user_id, card_id)
            return
    
    try:
        # Проверяем, что сообщение содержит текст (цену), а не медиа
        if not message.text:
            bot.send_message(message.chat.id, "❌ Пожалуйста, введите цену числом, а не отправляйте медиафайлы!")
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("❌ Отменить продажу", callback_data="cancel_sell_process"))
            msg = bot.send_message(message.chat.id, 
                                  "💵 Введите цену продажи (в монетах):\n\n⏰ *Процесс продажи автоматически отменится через 20 секунд бездействия*", 
                                  reply_markup=markup,
                                  parse_mode='Markdown')
            bot.register_next_step_handler(msg, process_sell_price, card_id, user_id)
            return
            
        price = int(message.text)
        if price <= 0:
            bot.send_message(message.chat.id, "❌ Цена должна быть положительным числом! Попробуйте снова:")
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("❌ Отменить продажу", callback_data="cancel_sell_process"))
            msg = bot.send_message(message.chat.id, 
                                  "💵 Введите цену продажи (в монетах):\n\n⏰ *Процесс продажи автоматически отменится через 20 секунд бездействия*", 
                                  reply_markup=markup,
                                  parse_mode='Markdown')
            bot.register_next_step_handler(msg, process_sell_price, card_id, user_id)
            return

        conn = sqlite3.connect('cats.db')
        cursor = conn.cursor()
        cursor.execute('SELECT card_name, rarity FROM user_cards WHERE id = ?', (card_id,))
        card_info = cursor.fetchone()
        conn.close()

        if card_info:
            card_name, rarity = card_info
            add_card_to_market(user_id, card_id, price)
            # Очищаем состояния после успешной продажи
            cleanup_selling_states(user_id, card_id)
            
            bot.send_message(message.chat.id,
                             f"✅ Карточка выставлена на продажу!\n\n"
                             f"🖼 {rarity} {card_name}\n"
                             f"💰 Цена: {price} монет")

    except ValueError:
        bot.send_message(message.chat.id, "❌ Пожалуйста, введите корректное число! Попробуйте снова:")
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("❌ Отменить продажу", callback_data="cancel_sell_process"))
        msg = bot.send_message(message.chat.id, 
                              "💵 Введите цену продажи (в монетах):\n\n⏰ *Процесс продажи автоматически отменится через 20 секунд бездействия*", 
                              reply_markup=markup,
                              parse_mode='Markdown')
        bot.register_next_step_handler(msg, process_sell_price, card_id, user_id)

# ФУНКЦИЯ ДЛЯ ОЧИСТКИ СОСТОЯНИЙ ПРОДАЖИ
def cleanup_selling_states(user_id, card_id):
    """Очищает все состояния, связанные с продажей карточки"""
    remove_active_selection(user_id, 'sell')
    remove_card_selling_state(user_id, card_id)
    remove_user_selling_state(user_id)
    remove_user_price_input_state(user_id)

def buy_card_confirmation(chat_id, market_id, buyer_id, message_id):
    conn = sqlite3.connect('cats.db')
    cursor = conn.cursor()

    cursor.execute('''
        SELECT uc.card_name, uc.rarity, m.price, u.username, u.user_id 
        FROM market m
        JOIN user_cards uc ON m.card_id = uc.id
        JOIN users u ON m.seller_id = u.user_id
        WHERE m.id = ?
    ''', (market_id,))

    card_info = cursor.fetchone()
    conn.close()

    if not card_info:
        bot.send_message(chat_id, "❌ Карточка уже продана или удалена!")
        remove_active_selection(buyer_id, 'buy')
        return

    card_name, rarity, price, seller_name, seller_id = card_info

    if buyer_id == seller_id:
        bot.send_message(chat_id, "❌ Нельзя купить свою же карточку!")
        remove_active_selection(buyer_id, 'buy')
        return

    conn = sqlite3.connect('cats.db')
    cursor = conn.cursor()
    cursor.execute('SELECT coins FROM users WHERE user_id = ?', (buyer_id,))
    buyer_balance = cursor.fetchone()
    conn.close()

    if not buyer_balance or buyer_balance[0] < price:
        bot.send_message(chat_id, f"❌ Недостаточно монет для покупки! Нужно: {price} монет")
        remove_active_selection(buyer_id, 'buy')
        return

    markup = types.InlineKeyboardMarkup()
    markup.row(
        types.InlineKeyboardButton("✅ Купить", callback_data=f"confirm_buy_{market_id}"),
        types.InlineKeyboardButton("❌ Отмена", callback_data="cancel_buy")
    )

    sent_message = bot.send_message(chat_id,
                     f"🛒 Подтверждение покупки:\n\n"
                     f"🖼 Карточка: {rarity} {card_name}\n"
                     f"💰 Цена: {price} монет\n"
                     f"👤 Продавец: @{seller_name}\n"
                     f"💳 Ваш баланс: {buyer_balance[0]} монет",
                     reply_markup=markup)
    
    store_message_owner(sent_message.message_id, buyer_id)

def process_buy_card(chat_id, market_id, buyer_id, message_id):
    sale_info, result_message = buy_card(market_id, buyer_id)

    if sale_info:
        card_id, seller_id, price, card_name, rarity = sale_info
        success_text = f"✅ Покупка успешно завершена!\n\n🖼 Карточка: {rarity} {card_name}\n💰 Цена: {price} монет"
        bot.edit_message_text(success_text, chat_id, message_id)

        try:
            seller_text = f"💰 Ваша карточка продана!\n\n🖼 Карточка: {rarity} {card_name}\n💰 Получено: {price} монет"
            bot.send_message(seller_id, seller_text)
        except:
            pass
    else:
        bot.edit_message_text(f"❌ {result_message}", chat_id, message_id)
    
    # Удаляем из активных выборов после завершения покупки
    remove_active_selection(buyer_id, 'buy')

# ФУНКЦИИ ДЛЯ МАГАЗИНА
def add_card_to_market(seller_id, card_id, price):
    conn = sqlite3.connect('cats.db')
    cursor = conn.cursor()

    cursor.execute('INSERT INTO market (seller_id, card_id, price) VALUES (?, ?, ?)',
                   (seller_id, card_id, price))
    conn.commit()
    conn.close()

def remove_from_market(market_id, user_id):
    conn = sqlite3.connect('cats.db')
    cursor = conn.cursor()

    cursor.execute('DELETE FROM market WHERE id = ? AND seller_id = ?', (market_id, user_id))
    conn.commit()
    conn.close()

def buy_card(market_id, buyer_id):
    conn = sqlite3.connect('cats.db')
    cursor = conn.cursor()

    try:
        cursor.execute('''
            SELECT m.card_id, m.seller_id, m.price, uc.card_name, uc.rarity 
            FROM market m
            JOIN user_cards uc ON m.card_id = uc.id
            WHERE m.id = ?
        ''', (market_id,))
        sale_info = cursor.fetchone()

        if not sale_info:
            return None, "Карточка не найдена в магазине"

        card_id, seller_id, price, card_name, rarity = sale_info

        cursor.execute('SELECT coins FROM users WHERE user_id = ?', (buyer_id,))
        buyer_coins = cursor.fetchone()

        if not buyer_coins or buyer_coins[0] < price:
            return None, "Недостаточно монет для покупки"

        if buyer_id == seller_id:
            return None, "Нельзя купить свою же карточку"

        cursor.execute('UPDATE users SET coins = coins - ? WHERE user_id = ?', (price, buyer_id))
        cursor.execute('UPDATE users SET coins = coins + ? WHERE user_id = ?', (price, seller_id))
        cursor.execute('UPDATE user_cards SET user_id = ? WHERE id = ?', (buyer_id, card_id))
        cursor.execute('DELETE FROM market WHERE id = ?', (market_id,))

        # Удаляем из состояния продажи после успешной продажи
        remove_card_selling_state(seller_id, card_id)

        conn.commit()
        return sale_info, "Успешная покупка"

    except Exception as e:
        conn.rollback()
        return None, f"Ошибка при покупке: {str(e)}"
    finally:
        conn.close()

# КОМАНДА АКТИВАЦИИ ПРОМОКОДА ДЛЯ ВСЕХ ПОЛЬЗОВАТЕЛЕЙ
@bot.message_handler(commands=['promo'])
@check_ban
def use_promo_command(message):
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name
    
    try:
        parts = message.text.split()
        if len(parts) != 2:
            bot.send_message(message.chat.id, "❌ Используйте: /promo КОД")
            return
            
        promo_code = parts[1].upper()
        
        conn = sqlite3.connect('cats.db')
        cursor = conn.cursor()
        
        cursor.execute('SELECT reward_type, reward_value, uses_left FROM promocodes WHERE code = ?', (promo_code,))
        promo = cursor.fetchone()
        
        if not promo:
            bot.send_message(message.chat.id, "❌ Промокод не найден!")
            conn.close()
            return
        
        reward_type, reward_value, uses_left = promo
        
        cursor.execute('SELECT * FROM used_promocodes WHERE user_id = ? AND promo_code = ?', (user_id, promo_code))
        already_used = cursor.fetchone()
        
        if already_used:
            bot.send_message(message.chat.id, "❌ Вы уже использовали этот промокод!")
            conn.close()
            return
        
        if uses_left == 0:
            pass
        elif uses_left > 0:
            cursor.execute('UPDATE promocodes SET uses_left = uses_left - 1 WHERE code = ?', (promo_code,))
            
            if uses_left - 1 == 0:
                cursor.execute('DELETE FROM promocodes WHERE code = ?', (promo_code,))
        else:
            bot.send_message(message.chat.id, "❌ Лимит использований промокода исчерпан!")
            conn.close()
            return
        
        if reward_type == "coins":
            coins = int(reward_value)
            cursor.execute('UPDATE users SET coins = coins + ? WHERE user_id = ?', (coins, user_id))
            reward_text = f"💰 {coins} монет"
            
        elif reward_type == "card":
            card_name = reward_value
            if card_name not in CARDS_DATABASE:
                bot.send_message(message.chat.id, "❌ Ошибка: карточка из промокода не найдена!")
                conn.rollback()
                conn.close()
                return
                
            card_data = CARDS_DATABASE[card_name]
            cursor.execute('INSERT INTO user_cards (user_id, rarity, card_name) VALUES (?, ?, ?)',
                          (user_id, card_data["rarity"], card_name))
            cursor.execute('UPDATE users SET coins = coins + ?, total_cards = total_cards + 1 WHERE user_id = ?',
                          (card_data["coins"], user_id))
            reward_text = f"🎴 {card_name}"
        
        cursor.execute('INSERT INTO used_promocodes (user_id, promo_code) VALUES (?, ?)', (user_id, promo_code))
        
        conn.commit()
        conn.close()
        
        success_message = f"""🎉 Промокод активирован!

🎫 Код: {promo_code}
🎁 Вы получили: {reward_text}"""

        bot.send_message(message.chat.id, success_message)
        
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Ошибка при активации промокода: {str(e)}")

# ОБРАБОТЧИК НЕИЗВЕСТНЫХ КОМАНД
@bot.message_handler(func=lambda message: True)
@check_ban
def handle_unknown(message):
    if message.text.startswith('/'):
        bot.send_message(message.chat.id, 
                        "❌ Неизвестная команда!\n\n"
                        "✨ Доступные команды:\n"
                        "• /start - начать работу\n"
                        "• /promo КОД - активировать промокод\n\n"
                        "Используйте кнопки меню для навигации.")

# ЗАПУСК БОТА С ЗАГРУЗКОЙ ДАННЫХ
if __name__ == "__main__":
    # Загружаем сохраненные данные
    load_saved_data()
    
    init_db()
    logger.info("Бот запущен!")
    logger.info(f"Статус магазина: {'ВКЛЮЧЕН' if SHOP_ENABLED else 'ВЫКЛЮЧЕН'}")
    logger.info(f"Загружено карточек: {len(CARDS_DATABASE)}")
    logger.info(f"Загружено рецептов крафта: {len(CRAFT_RECIPES)}")
    
    while True:
        try:
            logger.info("Запуск polling...")
            bot.polling(none_stop=True, timeout=60, long_polling_timeout=30)
        except Exception as e:
            logger.error(f"Ошибка бота: {e}")
            logger.info("Перезапуск через 10 секунд...")
            time.sleep(10)
