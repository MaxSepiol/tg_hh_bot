import telebot
from telebot import types
from hh_api import SearchSession
from favorites import load_favorites, add_to_favorites, remove_from_favorites
from utils import format_vacancy, vacancy_to_dict
from sessions import user_sessions
import logging
from config import TELEGRAM_TOKEN

# --- Настройки ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = telebot.TeleBot(TELEGRAM_TOKEN)

# --- Обработчики команд ---

@bot.message_handler(commands=['start'])
def handle_start(message):
    welcome_text = (
        "Привет! Я бот для поиска вакансий на hh.ru.\n"
        "Введите ключевое слово для поиска вакансий, например:\n"
        "Python разработчик\n\n"
        "Команды:\n"
        "/favorites - показать избранные вакансии\n"
        "/help - помощь по боту"
    )
    bot.send_message(message.chat.id, welcome_text)

@bot.message_handler(commands=['help'])
def handle_help(message):
    help_text = (
        "Функционал бота:\n"
        "- Введите ключевое слово для поиска вакансий.\n"
        "- Просматривайте вакансии по одной.\n"
        "- Используйте кнопки для просмотра следующей вакансии или сохранения в избранное.\n"
        "- /favorites - посмотреть сохранённые вакансии.\n"
        "- В избранном можно удалять вакансии."
    )
    bot.send_message(message.chat.id, help_text)

@bot.message_handler(commands=['favorites'])
def handle_favorites(message):
    user_id = message.from_user.id
    data = load_favorites()
    favorites = data.get('favorites', [])
    if not favorites:
        bot.send_message(message.chat.id, "Ваш список избранного пуст.")
        return

    favorite = favorites[0]
    text = f"<b>Ваши избранные вакансии:</b>\n\n" \
           f"<b>Вакансия:</b> {favorite['title']}\n" \
           f"<b>Зарплата:</b> {favorite['salary']}\n" \
           f"<b>Работодатель:</b> {favorite['employer']}\n" \
           f"<b>Ссылка:</b> {favorite['url']}"

    markup = types.InlineKeyboardMarkup()
    btn_delete = types.InlineKeyboardButton("Удалить из избранного", callback_data=f"delfav|{favorite['url']}")
    btn_next = types.InlineKeyboardButton("Показать следующую", callback_data="fav_next|0")
    markup.add(btn_delete, btn_next)

    if 'favorites_index' not in user_sessions:
        user_sessions['favorites_index'] = {}
    user_sessions['favorites_index'][user_id] = 0

    bot.send_message(message.chat.id, text, parse_mode='HTML', reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    user_id = call.from_user.id
    data = call.data

    # Импортируем здесь, чтобы избежать циклических импортов
    from hh_api import HH_API_URL
    import requests

    if data.startswith('show_more'):
        parts = data.split('|')
        if len(parts) != 3:
            bot.answer_callback_query(call.id, "Ошибка навигации.")
            return
        keyword = parts[1]
        try:
            index = int(parts[2])
        except:
            index = 0

        session = user_sessions.get(user_id)
        if not session or session.keyword != keyword:
            session = SearchSession(keyword)
            success = session.fetch_vacancies()
            if not success:
                bot.answer_callback_query(call.id, "Ошибка при запросе вакансий.")
                return
            user_sessions[user_id] = session

        if index >= len(session.vacancies):
            bot.answer_callback_query(call.id, "Больше вакансий нет.")
            return

        session.index = index
        vacancy = session.get_current_vacancy()
        if not vacancy:
            bot.answer_callback_query(call.id, "Вакансия не найдена.")
            return

        text = format_vacancy(vacancy)
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("Показать еще", callback_data=f"show_more|{keyword}|{index+1}"))
        markup.add(types.InlineKeyboardButton("Сохранить в избранное", callback_data=f"save_fav|{vacancy['id']}"))

        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                              text=text, parse_mode='HTML', reply_markup=markup)
        bot.answer_callback_query(call.id)

    elif data.startswith('save_fav'):
        parts = data.split('|')
        if len(parts) != 2:
            bot.answer_callback_query(call.id, "Ошибка сохранения.")
            return
        vacancy_id = parts[1]

        session = user_sessions.get(user_id)
        if not session:
            bot.answer_callback_query(call.id, "Нет активного поиска.")
            return

        vacancy = next((v for v in session.vacancies if v['id'] == vacancy_id), None)
        if not vacancy:
            bot.answer_callback_query(call.id, "Вакансия не найдена.")
            return

        vacancy_dict = vacancy_to_dict(vacancy)
        added = add_to_favorites(vacancy_dict)
        if added:
            bot.answer_callback_query(call.id, "Вакансия сохранена в избранное.")
        else:
            bot.answer_callback_query(call.id, "Вакансия уже в избранном.")

    elif data.startswith('delfav'):
        parts = data.split('|', 1)
        if len(parts) != 2:
            bot.answer_callback_query(call.id, "Ошибка удаления.")
            return
        url = parts[1]
        removed = remove_from_favorites(url)
        if removed:
            bot.answer_callback_query(call.id, "Вакансия удалена из избранного.")
            data_fav = load_favorites()
            fav_list = data_fav.get('favorites', [])
            if not fav_list:
                bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                      text="Ваш список избранного пуст.")
                return

            idx = user_sessions.get('favorites_index', {}).get(user_id, 0)
            if idx >= len(fav_list):
                idx = max(0, len(fav_list) - 1)
            user_sessions['favorites_index'][user_id] = idx

            favorite = fav_list[idx]
            text = f"<b>Ваши избранные вакансии:</b>\n\n" \
                   f"<b>Вакансия:</b> {favorite['title']}\n" \
                   f"<b>Зарплата:</b> {favorite['salary']}\n" \
                   f"<b>Работодатель:</b> {favorite['employer']}\n" \
                   f"<b>Ссылка:</b> {favorite['url']}"

            markup = types.InlineKeyboardMarkup()
            btn_delete = types.InlineKeyboardButton("Удалить из избранного", callback_data=f"delfav|{favorite['url']}")
            btn_next = types.InlineKeyboardButton("Показать следующую", callback_data=f"fav_next|{idx}")
            markup.add(btn_delete, btn_next)

            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                  text=text, parse_mode='HTML', reply_markup=markup)
        else:
            bot.answer_callback_query(call.id, "Вакансия не найдена в избранном.")

    elif data.startswith('fav_next'):
        parts = data.split('|')
        if len(parts) != 2:
            bot.answer_callback_query(call.id, "Ошибка навигации.")
            return
        try:
            idx = int(parts[1]) + 1
        except:
            idx = 0

        data_fav = load_favorites()
        fav_list = data_fav.get('favorites', [])
        if not fav_list:
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                  text="Ваш список избранного пуст.")
            return

        if idx >= len(fav_list):
            bot.answer_callback_query(call.id, "Больше вакансий нет.")
            return

        user_sessions['favorites_index'][user_id] = idx
        favorite = fav_list[idx]
        text = f"<b>Ваши избранные вакансии:</b>\n\n" \
               f"<b>Вакансия:</b> {favorite['title']}\n" \
               f"<b>Зарплата:</b> {favorite['salary']}\n" \
               f"<b>Работодатель:</b> {favorite['employer']}\n" \
               f"<b>Ссылка:</b> {favorite['url']}"

        markup = types.InlineKeyboardMarkup()
        btn_delete = types.InlineKeyboardButton("Удалить из избранного", callback_data=f"delfav|{favorite['url']}")
        btn_next = types.InlineKeyboardButton("Показать следующую", callback_data=f"fav_next|{idx}")
        markup.add(btn_delete, btn_next)

        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                              text=text, parse_mode='HTML', reply_markup=markup)
        bot.answer_callback_query(call.id)

    else:
        bot.answer_callback_query(call.id, "Неизвестная команда.")

@bot.message_handler(func=lambda message: True)
def handle_search(message):
    keyword = message.text.strip()
    if not keyword:
        bot.send_message(message.chat.id, "Пожалуйста, введите ключевое слово для поиска вакансий.")
        return

    session = SearchSession(keyword)
    success = session.fetch_vacancies()
    if not success:
        bot.send_message(message.chat.id, "Ошибка при запросе к hh.ru API. Попробуйте позже.")
        return

    if not session.vacancies:
        bot.send_message(message.chat.id, "По вашему запросу вакансий не найдено.")
        return

    user_sessions[message.from_user.id] = session
    vacancy = session.get_current_vacancy()
    text = format_vacancy(vacancy)

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Показать еще", callback_data=f"show_more|{keyword}|1"))
    markup.add(types.InlineKeyboardButton("Сохранить в избранное", callback_data=f"save_fav|{vacancy['id']}"))

    bot.send_message(message.chat.id, text, parse_mode='HTML', reply_markup=markup)

if __name__ == '__main__':
    print("Бот запущен...")
    bot.infinity_polling()
