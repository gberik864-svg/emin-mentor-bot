import requests


def get_vacancies():

    url = "https://api.hh.ru/vacancies"


    params = {
        "text":"удаленная работа гибкий график",
        "per_page":5
    }


    data = requests.get(
        url,
        params=params
    ).json()


    result = "💼 Вакансии:\n\n"


    for item in data["items"]:

        result += (
            f"🔹 {item['name']}\n"
            f"🔗 {item['alternate_url']}\n\n"
        )


    return result