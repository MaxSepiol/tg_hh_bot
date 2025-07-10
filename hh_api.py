import requests
import logging

HH_API_URL = 'https://api.hh.ru/vacancies'

logger = logging.getLogger(__name__)

class SearchSession:
    def __init__(self, keyword):
        self.keyword = keyword
        self.vacancies = []
        self.index = 0

    def fetch_vacancies(self):
        params = {
            'text': self.keyword,
            'per_page': 20,
            'page': 0
        }
        try:
            response = requests.get(HH_API_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            self.vacancies = data.get('items', [])
            self.index = 0
            return True
        except Exception as e:
            logger.error(f"Ошибка при запросе к hh.ru API: {e}")
            return False

    def get_current_vacancy(self):
        if 0 <= self.index < len(self.vacancies):
            return self.vacancies[self.index]
        return None

    def next_vacancy(self):
        self.index += 1
        if self.index >= len(self.vacancies):
            return None
        return self.vacancies[self.index]
