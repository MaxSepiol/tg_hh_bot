def format_vacancy(vacancy):
    title = vacancy.get('name', 'Нет названия')
    salary_data = vacancy.get('salary')
    if salary_data:
        salary = ''
        if salary_data.get('from'):
            salary += f"от {salary_data['from']} "
        if salary_data.get('to'):
            salary += f"до {salary_data['to']} "
        salary += salary_data.get('currency', '')
    else:
        salary = 'Не указана'

    employer = vacancy.get('employer', {}).get('name', 'Неизвестно')
    url = vacancy.get('alternate_url', 'Ссылка отсутствует')

    text = f"<b>Вакансия:</b> {title}\n" \
           f"<b>Зарплата:</b> {salary.strip()}\n" \
           f"<b>Работодатель:</b> {employer}\n" \
           f"<b>Ссылка:</b> {url}"
    return text

def vacancy_to_dict(vacancy):
    title = vacancy.get('name', 'Нет названия')
    salary_data = vacancy.get('salary')
    if salary_data:
        salary = ''
        if salary_data.get('from'):
            salary += f"от {salary_data['from']} "
        if salary_data.get('to'):
            salary += f"до {salary_data['to']} "
        salary += salary_data.get('currency', '')
    else:
        salary = 'Не указана'
    employer = vacancy.get('employer', {}).get('name', 'Неизвестно')
    url = vacancy.get('alternate_url', 'Ссылка отсутствует')

    return {
        "title": title,
        "salary": salary.strip(),
        "employer": employer,
        "url": url
    }
