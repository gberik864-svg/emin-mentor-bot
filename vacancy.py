import requests

def get_vacancies():

    url = "https://api.hh.ru/vacancies"

    params = {
        "text": '(удаленная OR "гибкий график" OR инвалидность)',
        "per_page": 5
    }

    response = requests.get(url, params=params)

    if response.status_code != 200:
        return "❌ Не удалось получить вакансии."

    data = response.json()

    if not data.get("items"):
        return "❌ Вакансии не найдены."

    result = "💼 Подходящие вакансии:\n\n"

    for item in data["items"]:
        result += (
            f"🔹 {item['name']}\n"
            f"🏢 {item['employer']['name']}\n"
            f"🔗 {item['alternate_url']}\n\n"
        )

    return result