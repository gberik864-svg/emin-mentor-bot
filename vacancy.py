import requests


def get_vacancies():

    url = "https://api.hh.ru/vacancies"

    headers = {
        "HH-User-Agent": "EminMentor/1.0 (your_email@gmail.com)"
    }

    params = {
        "host": "hh.kz",
        "area": 40,
        "text": "инвалидность удаленная гибкий график",
        "per_page": 5
    }

    response = requests.get(
        url,
        params=params,
        headers=headers,
        timeout=10
    )

    if response.status_code != 200:
        return f"❌ Ошибка {response.status_code}\n{response.text}"

    data = response.json()

    if not data["items"]:
        return "❌ Вакансии не найдены."

    result = "💼 Вакансии для людей с инвалидностью:\n\n"

    for job in data["items"]:

        result += (
            f"💼 {job['name']}\n"
            f"🏢 {job['employer']['name']}\n"
            f"📍 {job['area']['name']}\n"
            f"🔗 {job['alternate_url']}\n\n"
        )

    return result