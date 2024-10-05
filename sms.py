import logging
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackContext, MessageHandler, filters, ConversationHandler, CallbackQueryHandler
import asyncio
import threading
import os
import json

# Логирование для отладки
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Этапы диалога
API_KEY, ACTION, SELECT_SERVICE, SELECT_COUNTRY, VIEW_ORDERS = range(5)

# Полный список стран и сервисов
COUNTRIES = {
    'Россия': '0', 'Украина': '1', 'Казахстан': '2', 'США': '3', 'Канада': '4',
    'Великобритания': '5', 'Германия': '6', 'Франция': '7', 'Индия': '8', 'Китай': '9',
    'Япония': '10', 'Южная Корея': '11', 'Италия': '12', 'Испания': '13', 'Австралия': '14',
    'Турция': '15', 'Индонезия': '16', 'Бразилия': '17', 'Мексика': '18', 'Аргентина': '19',
    'Саудовская Аравия': '20', 'Объединенные Арабские Эмираты': '21', 'Египет': '22', 'ЮАР': '23',
    'Вьетнам': '24', 'Малайзия': '25', 'Филиппины': '26', 'Таиланд': '27', 'Сингапур': '28'
}

# Список сервисов
SERVICES = {
    'x5id': 'bd', 'Отзовик': 'amy', 'Bebeclub': 'aly', 'Lyft': 'tu', 'Upland': 'aho',
    'SpatenOktoberfest': 'ky', 'Beboo': 'apn', 'GetPlus': 'ajs', '米画师Mihuashi': 'yd', 'HungerStation': 'ayc',
    'CourseHero': 'yg', 'Cita Previa': 'si', 'Loanflix': 'di', 'Ximalaya': 'nw', 'Foxy': 'bbw',
    'Pesohere': 'aqd', 'Tatneft': 'uc', 'Abastece-aí': 'anb', 'FunPay': 'ng', 'RedBook': 'qf',
    'Zazzle': 'avx', 'Stormgain': 'vj', 'Bipa': 'baj', 'Magicbricks': 'hq', 'Asda': 'hs'
    # Продолжение списка сервисов ...
}

# Файл для хранения текущих заказов между перезапусками
ORDERS_FILE = "orders.json"

# Функция для сохранения заказов в файл
def save_orders_to_file(orders):
    with open(ORDERS_FILE, "w") as file:
        json.dump(orders, file)

# Функция для загрузки заказов из файла
def load_orders_from_file():
    if os.path.exists(ORDERS_FILE):
        with open(ORDERS_FILE, "r") as file:
            return json.load(file)
    return []

# Начальная команда для авторизации
async def start(update: Update, context: CallbackContext) -> int:
    context.user_data['orders'] = load_orders_from_file()
    keyboard = [
        [InlineKeyboardButton("Установить API ключ", callback_data='set_api_key')],
        [InlineKeyboardButton("Посмотреть текущий API ключ", callback_data='view_api_key')],
        [InlineKeyboardButton("Баланс", callback_data='balance')],
        [InlineKeyboardButton("Выбрать страну", callback_data='set_country')],
        [InlineKeyboardButton("Заказать номер", callback_data='get_number')],
        [InlineKeyboardButton("Текущие заказы", callback_data='view_orders')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text("Привет! Выберите действие:", reply_markup=reply_markup)
    return ACTION

# Установка API ключа
async def set_api_key(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Введите ваш API ключ:")
    return API_KEY

# Сохранение API ключа
async def api_key_handler(update: Update, context: CallbackContext) -> int:
    context.user_data['api_key'] = update.message.text
    keyboard = [
        [InlineKeyboardButton("Назад в главное меню", callback_data='main_menu')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "API ключ сохранен!", reply_markup=reply_markup
    )
    return ACTION

# Просмотр текущего API ключа
async def view_api_key(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    api_key = context.user_data.get('api_key', 'API ключ не установлен')
    keyboard = [
        [InlineKeyboardButton("Назад в главное меню", callback_data='main_menu')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(f"Текущий API ключ: {api_key}", reply_markup=reply_markup)

# Запрос баланса
async def get_balance(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    api_key = context.user_data.get('api_key')
    if not api_key:
        await query.edit_message_text("API ключ не установлен. Установите API ключ сначала.")
        return
    params = {
        'api_key': api_key,
        'action': 'getBalance',
        'currency': '643'  # Используем рубли (код 643)
    }
    response = requests.get("https://smshub.org/stubs/handler_api.php", params=params)
    if response.status_code == 200 and "ACCESS_BALANCE" in response.text:
        balance = response.text.split(':')[1]
        await query.edit_message_text(f"Ваш баланс: {balance} ₽")
    else:
        await query.edit_message_text("Ошибка при получении баланса. Пожалуйста, проверьте ваш API ключ и попробуйте снова.")

# Изменение страны
async def set_country(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    await query.answer()
    keyboard = [[InlineKeyboardButton(country, callback_data=f'country_{code}')]
                for country, code in COUNTRIES.items()]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("Выберите страну:", reply_markup=reply_markup)
    return SELECT_COUNTRY

async def country_selected(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    await query.answer()
    country_code = query.data.split('_')[1]
    context.user_data['country'] = country_code
    keyboard = [[InlineKeyboardButton("Назад в главное меню", callback_data='main_menu')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(f"Страна установлена. Код страны: {country_code}", reply_markup=reply_markup)
    return ACTION

# Выбор сервиса для заказа номера
async def get_number(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    await query.answer()
    keyboard = [[InlineKeyboardButton(service, callback_data=f'service_{code}')]
                for service, code in SERVICES.items()]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("Выберите сервис, для которого хотите заказать номер:", reply_markup=reply_markup)
    return SELECT_SERVICE

# Заказ номера для выбранного сервиса
async def order_number(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    service = query.data.split('_')[1]
    api_key = context.user_data.get('api_key')
    if not api_key:
        await query.edit_message_text("API ключ не установлен. Установите API ключ сначала.")
        return
    country = context.user_data.get('country', '0')  # Код страны по умолчанию (Россия)
    params = {
        'api_key': api_key,
        'action': 'getNumber',
        'service': service,
        'country': country
    }
    response = requests.get("https://smshub.org/stubs/handler_api.php", params=params)
    if "ACCESS_NUMBER" in response.text:
        _, activation_id, number = response.text.split(':')
        order = {'activation_id': activation_id, 'number': number, 'service': service}
        context.user_data.setdefault('orders', []).append(order)
        save_orders_to_file(context.user_data['orders'])
        context.user_data['chat_id'] = query.message.chat_id  # Сохраняем chat_id для дальнейшей отправки сообщений
        await query.edit_message_text(f"Номер для активации: {number}")

        # Запускаем проверку статуса активации в отдельном потоке
        threading.Thread(target=check_activation_status_thread, args=(context, activation_id, number), daemon=True).start()
    else:
        await query.edit_message_text("Ошибка при заказе номера. Попробуйте позже.")

# Периодическая проверка статуса активации (в отдельном потоке)
def check_activation_status_thread(context: CallbackContext, activation_id: str, number: str) -> None:
    api_key = context.user_data.get('api_key')
    if not api_key:
        return

    url = f"https://smshub.org/stubs/handler_api.php?api_key={api_key}&action=getStatus&id={activation_id}"
    while True:
        response = requests.get(url)
        if "STATUS_OK" in response.text:
            code = response.text.split(':')[1]
            # Отправляем код пользователю
            chat_id = context.user_data.get('chat_id')
            asyncio.run(context.bot.send_message(chat_id=chat_id, text=f"Код активации для номера {number}: {code}"))
            break
        elif "STATUS_WAIT_CODE" in response.text:
            asyncio.sleep(5)  # Проверяем каждые 5 секунд
        else:
            # Обрабатываем другие возможные статусы (например, ошибка или отмена)
            asyncio.sleep(5)

# Просмотр текущих заказов
async def view_orders(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    orders = load_orders_from_file()
    if not orders:
        await query.edit_message_text("У вас нет текущих заказов.")
        return

    text = "Текущие заказы:\n"
    for order in orders:
        activation_id = order['activation_id']
        number = order['number']
        service = order['service']
        status_url = f"https://smshub.org/stubs/handler_api.php?api_key={context.user_data['api_key']}&action=getStatus&id={activation_id}"
        response = requests.get(status_url)
        status = response.text if response.status_code == 200 else "Ошибка при получении статуса"
        text += f"Номер: {number}, Сервис: {service}, Статус: {status}\n"

    keyboard = [[InlineKeyboardButton("Назад в главное меню", callback_data='main_menu')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text, reply_markup=reply_markup)

# Главное меню
async def main_menu(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    await query.answer()
    keyboard = [
        [InlineKeyboardButton("Установить API ключ", callback_data='set_api_key')],
        [InlineKeyboardButton("Посмотреть текущий API ключ", callback_data='view_api_key')],
        [InlineKeyboardButton("Баланс", callback_data='balance')],
        [InlineKeyboardButton("Выбрать страну", callback_data='set_country')],
        [InlineKeyboardButton("Заказать номер", callback_data='get_number')],
        [InlineKeyboardButton("Текущие заказы", callback_data='view_orders')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("Выберите действие:", reply_markup=reply_markup)
    return ACTION

# Обработка ошибок
async def error(update: Update, context: CallbackContext) -> None:
    logger.warning(f'Update "{update}" caused error "{context.error}"')

def main() -> None:
    # Вставьте токен вашего бота, полученный у BotFather
    application = Application.builder().token("8110647148:AAHupEEVe98sbRfEAi44-qa-n_XfnTvndRc").build()

    # Определение этапов разговора
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            API_KEY: [MessageHandler(filters.TEXT & ~filters.COMMAND, api_key_handler)],
            ACTION: [
                CallbackQueryHandler(set_api_key, pattern='^set_api_key$'),
                CallbackQueryHandler(view_api_key, pattern='^view_api_key$'),
                CallbackQueryHandler(get_balance, pattern='^balance$'),
                CallbackQueryHandler(set_country, pattern='^set_country$'),
                CallbackQueryHandler(get_number, pattern='^get_number$'),
                CallbackQueryHandler(view_orders, pattern='^view_orders$'),
                CallbackQueryHandler(main_menu, pattern='^main_menu$'),
            ],
            SELECT_COUNTRY: [
                CallbackQueryHandler(country_selected, pattern='^country_')
            ],
            SELECT_SERVICE: [
                CallbackQueryHandler(order_number, pattern='^service_')
            ],
        },
        fallbacks=[CommandHandler('start', start)],
    )

    application.add_handler(conv_handler)
    application.add_error_handler(error)

    # Запуск бота
    if not asyncio.get_event_loop().is_running():
        asyncio.run(application.run_polling())
    else:
        application.run_polling()

if __name__ == '__main__':
    main()
