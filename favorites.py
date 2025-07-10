import json
import os
import logging

FAVORITES_FILE = 'favorites.json'
logger = logging.getLogger(__name__)

def load_favorites():
    if not os.path.exists(FAVORITES_FILE):
        return {"favorites": []}
    try:
        with open(FAVORITES_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if "favorites" not in data:
                data = {"favorites": []}
            return data
    except Exception as e:
        logger.error(f"Ошибка при загрузке файла избранного: {e}")
        return {"favorites": []}

def save_favorites(data):
    try:
        with open(FAVORITES_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        logger.error(f"Ошибка при сохранении файла избранного: {e}")

def add_to_favorites(vacancy):
    data = load_favorites()
    if any(fav['url'] == vacancy['url'] for fav in data['favorites']):
        return False
    data['favorites'].append(vacancy)
    save_favorites(data)
    return True

def remove_from_favorites(url):
    data = load_favorites()
    new_list = [fav for fav in data['favorites'] if fav['url'] != url]
    if len(new_list) == len(data['favorites']):
        return False
    data['favorites'] = new_list
    save_favorites(data)
    return True
