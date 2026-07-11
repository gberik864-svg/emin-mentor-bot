import requests
from bs4 import BeautifulSoup


def get_vacancies():

    url = "https://remoteok.com/remote-dev-jobs"

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    try:

        response = requests.get(
            url,
            headers=headers,
            timeout=10
        )

        if response.status_code != 200:
            return "❌ Не удалось получить вакансии."

        soup = BeautifulSoup(response.text, "html.parser")

        jobs = soup.find_all("tr", class_="job")

        if not jobs:
            return "❌ Вакансии не найдены."

        result = "💼 Подходящие вакансии:\n\n"

        count = 0

        for job in jobs:

            if count == 5:
                break

            title = job.get("data-position") or "Без названия"
            company = job.get("data-company") or "Не указано"

            link = job.get("data-href")

            if link:
                link = "https://remoteok.com" + link
            else:
                link = "https://remoteok.com"

            result += (
                f"🔹 {title}\n"
                f"🏢 {company}\n"
                f"🔗 {link}\n\n"
            )

            count += 1

        return result

    except Exception as e:

        return f"❌ Ошибка: {e}"