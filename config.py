import os
from dotenv import load_dotenv

# Загружаем переменные из .env
load_dotenv()

# Получаем токен телеграм бота из переменных окружения
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')

if TELEGRAM_TOKEN is None:
    raise ValueError("TELEGRAM_TOKEN не установлен в переменных окружения")
