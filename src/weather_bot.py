import os
import json
import requests
import telebot
import time
from dotenv import load_dotenv
from telebot.types import ReplyKeyboardMarkup, KeyboardButton

load_dotenv()



BOT_TOKEN = os.environ.get('BOT_TOKEN')
API_KEY = os.environ.get('API_KEY')

bot = telebot.TeleBot(BOT_TOKEN)

FAVORITES_FILE = 'favorites.json'

user_settings = {}  # user_id -> {'city': 'Москва'}

# =================== Вспомогательные функции ===================
def load_user_settings():
    global user_settings
    if os.path.exists('user_settings.json'):
        with open('user_settings.json', 'r', encoding='utf-8') as f:
            user_settings = json.load(f)

def save_user_settings():
    with open('user_settings.json', 'w', encoding='utf-8') as f:
        json.dump(user_settings, f, ensure_ascii=False)

load_user_settings()


def is_valid_city(city):
    url = "http://api.openweathermap.org/data/2.5/weather"
    params = {'q': city, 'appid': API_KEY}
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        # Проверка, есть ли в ответе поле 'cod' и его значение != '404'
        if data.get('cod') == 200:
            return True
        else:
            return False
    except:
        return False


def process_add_favorite(message):
    city = message.text.strip()
    if not is_valid_city(city):
        safe_send_message(message.chat.id, f"Город '{city}' не найден или недоступен. Попробуйте другое название.")
        return

    favs = load_favorites(message.from_user.id)
    if city in favs:
        bot.send_message(message.chat.id, f"{city} уже есть в списке.", reply_markup=main_menu())
    else:
        favs.append(city)
        save_favorites(message.from_user.id, favs)
        bot.send_message(message.chat.id, f"{city} добавлен(а) в список.", reply_markup=main_menu())

def remove_favorite(message):
    city = message.text.strip()
    favs = load_favorites(message.from_user.id)
    if city in favs:
        favs.remove(city)
        save_favorites(message.from_user.id, favs)
        safe_send_message(message.chat.id, f"Город '{city}' удалён из избранных.", reply_markup=main_menu())
    else:
        safe_send_message(message.chat.id, f"Город '{city}' не найден в списке избранных.", reply_markup=main_menu())

def safe_send_message(chat_id, text, reply_markup=None):
    try:
        bot.send_message(chat_id, text, reply_markup=reply_markup)
    except Exception as e:
        print(f"Ошибка отправки сообщения: {e}")

def load_favorites(user_id):
    try:
        if os.path.exists(FAVORITES_FILE):
            with open(FAVORITES_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data.get(str(user_id), [])
        return []
    except Exception as e:
        print(f"Ошибка загрузки избранных: {e}")
        return []

def save_favorites(user_id, cities):
    try:
        if os.path.exists(FAVORITES_FILE):
            with open(FAVORITES_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
        else:
            data = {}
        data[str(user_id)] = cities
        with open(FAVORITES_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f)
    except Exception as e:
        print(f"Ошибка сохранения избранных: {e}")

def get_weather_by_coords(lat, lon):
    url = "http://api.openweathermap.org/data/2.5/weather"
    params = {'lat': lat, 'lon': lon, 'appid': API_KEY, 'units': 'metric', 'lang': 'ru'}
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        return {
            'description': data['weather'][0]['description'].capitalize(),
            'temp': data['main']['temp'],
            'humidity': data['main']['humidity'],
            'wind_speed': data['wind']['speed']
        }
    except Exception as e:
        print(f"Ошибка получения погоды по координатам: {e}")
        return None

def get_weather(city):
    url = "http://api.openweathermap.org/data/2.5/weather"
    params = {'q': city, 'appid': API_KEY, 'units': 'metric', 'lang': 'ru'}
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        return {
            'description': data['weather'][0]['description'].capitalize(),
            'temp': data['main']['temp'],
            'humidity': data['main']['humidity'],
            'wind_speed': data['wind']['speed']
        }
    except Exception as e:
        print(f"Ошибка получения погоды: {e}")
        return None

from datetime import datetime, timedelta

from datetime import datetime, timedelta

def get_structured_forecast(city):
    url = "http://api.openweathermap.org/data/2.5/forecast"
    params = {'q': city, 'appid': API_KEY, 'units': 'metric', 'lang': 'ru'}
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        forecast_list = data['list']

        today = datetime.utcnow().date()
        days = [today + timedelta(days=i) for i in range(3)]

        forecast_by_day = {}
        for day in days:
            forecast_by_day[day] = {
                'утро': None,
                'день': None,
                'вечер': None,
                'ночь': None
            }

        time_slots = {
            'утро': 6,
            'день': 12,
            'вечер': 18,
            'ночь': 0
        }

        # Сопоставление описания погоды с эмодзи
        weather_emojis = {
            'ясно': '☀️',
            'солнечно': '☀️',
            'облачно с прояснениями': '🌤️',
            'облачно ': '☁️',
            'пасмурно': '☁️',
            'переменная облачность': '⛅',
            'небольшая облачность': '🌥️',
            'дождь': '🌧️',
            'Небольшой дождь': '🌦️',
            'дождливо': '🌧️',
            'снег': '❄️',
            'снежно': '❄️',
            'туман': '🌫️',
            'туманно': '🌫️',
            'гроза': '🌩️',
            'буря': '🌬️',
            'ветренно': '💨',
        }

        for item in forecast_list:
            dt = datetime.utcfromtimestamp(item['dt'])
            date = dt.date()
            hour = dt.hour

            if date in forecast_by_day:
                for period, period_hour in time_slots.items():
                    if abs(hour - period_hour) <= 1:
                        slot = period
                        if forecast_by_day[date][slot] is None:
                            desc = item['weather'][0]['description'].lower()
                            # Ищем подходящий эмодзи по описанию
                            emoji = ''
                            for key in weather_emojis:
                                if key in desc:
                                    emoji = weather_emojis[key]
                                    break
                            forecast_by_day[date][slot] = {
                                'dt_txt': dt.strftime('%d.%m'),
                                'description': item['weather'][0]['description'].capitalize(),
                                'temp': item['main']['temp'],
                                'emoji': emoji
                            }
                        break

        # Формируем сообщение
        emojis = {
            'утро': '🌅',
            'день': '☀️',
            'вечер': '🌇',
            'ночь': '🌙'
        }

        forecast_text = ""
        for day in days:
            forecast_text += f"\n📅 {day.strftime('%d.%m')}:\n"
            for period in ['утро', 'день', 'вечер', 'ночь']:
                info = forecast_by_day[day][period]
                emoji_time = emojis.get(period, '')
                if info:
                    weather_emoji = info.get('emoji', '')
                    # Если есть погодный эмодзи, добавляем его после описания
                    forecast_text += f"{emoji_time} {period.capitalize()}: {info['description']} {weather_emoji}, {info['temp']}°C\n"
                else:
                    forecast_text += f"{emoji_time} {period.capitalize()}: Нет данных\n"

        return forecast_text

    except Exception as e:
        print(f"Ошибка получения структурированного прогноза: {e}")
        return None
# =================== Основные меню ===================

def main_menu():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(
        KeyboardButton("🌤️ Текущая погода в городе"),
        KeyboardButton("🌅 Прогноз на 3 дня")
    )
    markup.row(
        KeyboardButton("🌍 Получить погоду по геолокации"),
        KeyboardButton("📍 Отправить геолокацию", request_location=True)
    )
    markup.row(
        KeyboardButton("⭐ Мои любимые города"),
        KeyboardButton("🗑️ Удалить город из избранных")
    )
    markup.row(
        KeyboardButton("➕ Добавить город в избранное"),
        KeyboardButton("⚙️ Настройки")  # Новая кнопка
    )
    markup.row(
        KeyboardButton("ℹ️ Помощь и инструкции")
    )
    return markup

# =================== Обработчики ===================

@bot.message_handler(commands=['start'])
def handle_start(message):
    safe_send_message(
        message.chat.id,
        "👋 Привет! Я — бот погоды.\nВыберите опцию ниже.",
        reply_markup=main_menu()
    )

@bot.message_handler(func=lambda m: m.text in ["🌍 Получить погоду по геолокации", "📍 Отправить геолокацию"])
def handle_location_request(message):
    safe_send_message(message.chat.id, "Пожалуйста, отправьте вашу геолокацию.", reply_markup=main_menu())

@bot.message_handler(func=lambda m: m.text == "🗑️ Удалить город из избранных")
def handle_delete_favorite_prompt(message):
    favs = load_favorites(message.from_user.id)
    if not favs:
        safe_send_message(message.chat.id, "У вас нет сохранённых городов.", reply_markup=main_menu())
        return
    safe_send_message(message.chat.id, "Введите название города для удаления из избранных:")
    bot.register_next_step_handler(message, remove_favorite)
@bot.message_handler(func=lambda m: m.text == "🌤️ Текущая погода в городе")
def handle_current_weather(message):
    user_id = message.from_user.id
    city = None
    if user_id in user_settings and 'city' in user_settings[user_id]:
        city = user_settings[user_id]['city']
    if city:
        # показываем погоду по сохранённому городу
        weather = get_weather(city)
        if weather:
            reply = (
                f"🌆 Текущая погода в {city}:\n"
                f"🌤️ {weather['description']}\n"
                f"🌡️ Температура: {weather['temp']}°C\n"
                f"💧 Влажность: {weather['humidity']}%\n"
                f"💨 Скорость ветра: {weather['wind_speed']} м/с"
            )
            safe_send_message(message.chat.id, reply, reply_markup=main_menu())
        else:
            safe_send_message(message.chat.id, "Не удалось получить погоду. Попробуйте снова или введите название города вручную.", reply_markup=main_menu())
    else:
        safe_send_message(message.chat.id, "Введите название города, например: Москва")
        bot.register_next_step_handler(message, process_current_weather)
@bot.message_handler(content_types=['location'])
def handle_location(message):
    if message.location:
        lat = message.location.latitude
        lon = message.location.longitude
        weather = get_weather_by_coords(lat, lon)
        if weather:
            reply = (
                f"🌐 Погода по вашему местоположению:\n"
                f"🌤️ {weather['description']}\n"
                f"🌡️ Температура: {weather['temp']}°C\n"
                f"💧 Влажность: {weather['humidity']}%\n"
                f"💨 Скорость ветра: {weather['wind_speed']} м/с"
            )
            safe_send_message(message.chat.id, reply, reply_markup=main_menu())
        else:
            safe_send_message(message.chat.id, "Не удалось получить данные о погоде для вашего местоположения.", reply_markup=main_menu())
    else:
        safe_send_message(message.chat.id, "Не было получено гео-данных. Попробуйте снова отправить геолокацию.", reply_markup=main_menu())
@bot.message_handler(func=lambda m: m.text == "⚙️ Настройки")
def handle_settings(message):
    user_id = message.from_user.id
    current_city = None
    if user_id in user_settings and 'city' in user_settings[user_id]:
        current_city = user_settings[user_id]['city']
        safe_send_message(
            message.chat.id,
            f"Текущий сохранённый город: {current_city}. Хотите его изменить?",
            reply_markup=markup_change_city()
        )
    else:
        safe_send_message(
            message.chat.id,
            "Вы ещё не сохранили город. Введите название города для сохранения:",
            reply_markup=None
        )
        bot.register_next_step_handler(message, save_user_city)
from telebot.types import ReplyKeyboardMarkup, KeyboardButton

def markup_change_city():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(
        KeyboardButton("Да, изменить город"),
        KeyboardButton("Нет, оставить текущий")
    )
    return markup

def save_user_city(message):
    city = message.text.strip()
    if not is_valid_city(city):
        safe_send_message(message.chat.id, f"Город '{city}' не найден или недоступен. Попробуйте снова.")
        return
    user_id = message.from_user.id
    user_settings.setdefault(user_id, {})['city'] = city
    save_user_settings()
    safe_send_message(
        message.chat.id,
        f"Город '{city}' сохранён. Теперь вы можете быстро просматривать погоду для этого города.",
        reply_markup=main_menu()


    )

@bot.message_handler(func=lambda m: m.text in ["Да, изменить город", "Нет, оставить текущий"])
def handle_change_city_choice(message):
    choice = message.text
    if choice == "Да, изменить город":
        safe_send_message(
            message.chat.id,
            "Введите новый город для сохранения:"
        )
        bot.register_next_step_handler(message, save_user_city)
    else:
        safe_send_message(
            message.chat.id,
            "Настройки сохранены. Можно просматривать погоду по сохранённому городу.",
            reply_markup=main_menu()
        )
@bot.message_handler(func=lambda m: True)
def handle_text(message):
    text = message.text.strip()

    if text == "🌤️ Текущая погода в городе":
        safe_send_message(message.chat.id, "Введите название города, например: Москва")
        bot.register_next_step_handler(message, process_current_weather)

    elif text == "🌅 Прогноз на 3 дня":
        safe_send_message(message.chat.id, "Введите название города для прогноза на 3 дня, например: Москва")
        bot.register_next_step_handler(message, process_forecast_request)

    elif text == "ℹ️ Помощь и инструкции":
        help_text = (
            "📝 Инструкции:\n"
            "- Для просмотра текущей погоды введите 'Текущая погода в городе' и затем название города.\n"
            "- Для прогноза на 3 дня выберите 'Прогноз на 3 дня' и введите название города.\n"
            "- Для получения погоды по вашему местоположению нажмите '🌍 Получить погоду по геолокации' или '📍 Отправить геолокацию' и поделитесь своей геоданными.\n"
            "- В меню есть опции 'Мои любимые города' и '➕ Добавить город в избранное'."
        )
        safe_send_message(message.chat.id, help_text, reply_markup=main_menu())

    elif text == "⭐ Мои любимые города":
        favs = load_favorites(message.from_user.id)
        if favs:
            reply = "Ваши любимые города:\n" + "\n".join(favs)
        else:
            reply = "У вас еще нет сохранённых городов."
        safe_send_message(message.chat.id, reply, reply_markup=main_menu())

    elif text == "➕ Добавить город в избранное":
        safe_send_message(message.chat.id, "Введите название города для добавления:")
        bot.register_next_step_handler(message, process_add_favorite)

    elif text.startswith("/removefavorite"):
        parts = text.split(maxsplit=1)
        if len(parts) == 2:
            city_to_remove = parts[1]
            remove_favorite(message, city_to_remove)
        else:
            safe_send_message(message.chat.id, "Используйте команду: /removefavorite <название города> для удаления.")

    else:
        safe_send_message(message.chat.id, "Пожалуйста, используйте меню для выбора опций.", reply_markup=main_menu())
def process_current_weather(message):
    city = message.text.strip()
    weather = get_weather(city)
    if weather:
        reply = (
            f"🌆 Текущая погода в {city}:\n"
            f"🌤️ {weather['description']}\n"
            f"🌡️ Температура: {weather['temp']}°C\n"
            f"💧 Влажность: {weather['humidity']}%\n"
            f"💨 Скорость ветра: {weather['wind_speed']} м/с"
        )
        safe_send_message(message.chat.id, reply, reply_markup=main_menu())
    else:
        safe_send_message(message.chat.id, "Не удалось найти такой город или данные недоступны. Попробуйте еще раз.", reply_markup=main_menu())

@bot.message_handler(func=lambda m: m.text == "🌅 Прогноз на 3 дня")
def handle_forecast_on_start(message):
    user_id = message.from_user.id
    city = None
    if user_id in user_settings and 'city' in user_settings[user_id]:
        city = user_settings[user_id]['city']

    if city:
        forecast = get_structured_forecast(city)
        if forecast:
            reply = f"📅 Прогноз на 3 дня для {city}:\n{forecast}"
            safe_send_message(message.chat.id, reply, reply_markup=main_menu())
        else:
            safe_send_message(message.chat.id, f"Не удалось получить прогноз для {city}. Попробуйте ввести другой город.", reply_markup=main_menu())
    else:
        # Нет сохранённого города — запрашиваем ввод
        safe_send_message(message.chat.id, "Введите название города для прогноза на 3 дня, например: Москва")
        bot.register_next_step_handler(message, process_forecast_request)

def process_forecast_request(message):
    city = message.text.strip()
    forecast = get_structured_forecast(city)
    print("user_settings:", user_settings)
    print("Запрошенный город:", city)
    print("Прогноз:", forecast)
    if forecast:
        reply = f"📅 Прогноз на 3 дня для {city}:\n{forecast}"
        safe_send_message(message.chat.id, reply, reply_markup=main_menu())
    else:
        safe_send_message(message.chat.id, "Не удалось получить прогноз по этому городу. Попробуйте еще раз.", reply_markup=main_menu())
# =================== Запуск ===================

if __name__ == '__main__':
    while True:
        try:
            bot.infinity_polling(timeout=60)
        except Exception as e:
            print(f"Произошла ошибка: {e}")
            time.sleep(5)

