
import logging
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# ================= ENBEK.KZ =================

ENBEK_BASE_URL = "https://www.enbek.kz"
ENBEK_SEARCH_URL = "https://www.enbek.kz/ru/search/vacancy"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; EminMentor/1.1)",
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "ru-RU,ru;q=0.9",
}

# ================= FILTERS =================

SEARCH_WORDS = {
    "all": [""],
    "youth": [
        "без опыта",
        "стажер",
        "студент",
    ],
    "accessible": [
        "инвалидность",
        "для лиц с инвалидностью",
    ],
    "remote": [
        "удаленная работа",
        "дистанционная работа",
    ],
    "flexible": [
        "гибкий график",
        "неполный рабочий день",
    ],
}


def clean_text(value):
    return " ".join(str(value or "").split())


def extract_field(text, label, next_labels):
    """
    Enbek бетінен нақты өрісті бөліп алу.
    """
    boundaries = "|".join(
        re.escape(item) for item in next_labels
    )

    pattern = (
        rf"{re.escape(label)}\s*[:\-]?\s*(.*?)"
        rf"(?=\s*(?:{boundaries})\b|$)"
    )

    match = re.search(
        pattern,
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )

    if match:
        return clean_text(match.group(1))

    return ""


def matches_filter(job, filter_type):
    if filter_type == "all":
        return True

    name = str(job.get("name") or "").lower()
    schedule = str(job.get("schedule") or "").lower()
    employment = str(job.get("employment") or "").lower()
    experience = str(job.get("experience") or "").lower()
    description = str(job.get("description") or "").lower()

    if filter_type == "remote":
        remote_words = [
            "дистанцион",
            "удален",
            "удалён",
            "надомн",
            "remote",
        ]

        return any(
            word in (employment + " " + schedule)
            for word in remote_words
        )

    if filter_type == "flexible":
        flexible_words = [
            "гибкий",
            "неполный",
            "частичная",
            "посменный",
            "сменный",
        ]

        return any(
            word in (employment + " " + schedule)
            for word in flexible_words
        )

    if filter_type == "youth":
        youth_words = [
            "без опыта",
            "опыт не требуется",
            "стажер",
            "стажёр",
            "стажировка",
            "студент",
            "начинающий",
        ]

        combined = (
            name + " " + experience + " " + description
        )

        return any(
            word in combined
            for word in youth_words
        )

    if filter_type == "accessible":
        accessible_words = [
            "для лиц с инвалидностью",
            "для людей с инвалидностью",
            "для инвалидов",
            "рабочее место для инвалидов",
        ]

        return any(
            word in description
            for word in accessible_words
        )

    return True


# ================= PARSE VACANCY =================

def parse_enbek_vacancy(url):
    try:
        response = requests.get(
            url,
            headers=HEADERS,
            timeout=15,
        )

        if response.status_code != 200:
            logger.warning(
                "Enbek vacancy status: %s",
                response.status_code,
            )
            return None

        soup = BeautifulSoup(
            response.text,
            "html.parser",
        )

        title_tag = soup.find("h1") or soup.find("h4")

        if not title_tag:
            return None

        title = clean_text(
            title_tag.get_text(" ", strip=True)
        )

        if not title:
            return None

        text = clean_text(
            soup.get_text(" ", strip=True)
        )

        # Компания
        company = "Компания не указана"

        company_tag = soup.find(
            "a",
            href=lambda href: href and (
                "/company/" in href
                or "/employer/" in href
            ),
        )

        if company_tag:
            company = clean_text(
                company_tag.get_text(" ", strip=True)
            ) or company

        if company == "Компания не указана":
            company_match = re.search(
                r"от\s+("
                r"Товарищество с ограниченной ответственностью"
                r'\s*["«][^"»]+["»]'
                r"|Индивидуальный предприниматель"
                r"\s+[^,]+"
                r")",
                text,
                flags=re.IGNORECASE,
            )

            if company_match:
                company = clean_text(
                    company_match.group(1)
                )

        # Қала
        city = "Казахстан"

        city_match = re.search(
            r"Регион\s+(.{2,100}?)"
            r"(?=\s+Место работы\b|$)",
            text,
            flags=re.IGNORECASE,
        )

        if city_match:
            city = clean_text(
                city_match.group(1)
            )[:100]
        else:
            city_match = re.search(
                r"\bв\s+(Астане|Алматы|Шымкенте|"
                r"Таразе|Караганде|Актобе|"
                r"Павлодаре|Костанае)\b",
                text,
                flags=re.IGNORECASE,
            )

            if city_match:
                city = city_match.group(1)

        # Жалақы
        salary = "Не указана"

        salary_match = re.search(
            r"(?:от\s*)?\d[\d\s]*"
            r"(?:[-–]\s*\d[\d\s]*)?"
            r"\s*(?:тенге|тг\.?|₸)",
            text,
            flags=re.IGNORECASE,
        )

        if salary_match:
            salary = clean_text(
                salary_match.group(0)
            )

        # Жұмыс түрі
        employment = extract_field(
            text,
            "Тип занятости",
            [
                "График работы",
                "Условия труда",
                "Стажировка",
                "Опыт работы",
            ],
        )

        # Жұмыс кестесі
        schedule = extract_field(
            text,
            "График работы",
            [
                "Условия труда",
                "Стажировка",
                "Опыт работы",
                "Образование",
            ],
        )

        if not schedule:
            schedule = "Не указан"

        # Тәжірибе
        experience = extract_field(
            text,
            "Опыт работы",
            [
                "Образование",
                "Рабочих мест",
                "Обязанности",
            ],
        )

        # Жарияланған күні
        published = ""

        date_match = re.search(
            r"Вакансия опубликована\s+"
            r"(\d{2}\.\d{2}\.\d{4})",
            text,
            flags=re.IGNORECASE,
        )

        if date_match:
            published = date_match.group(1)

        return {
            "name": title,
            "company": company,
            "city": city,
            "salary": salary,
            "schedule": schedule,
            "experience": experience,
            "published": published,
            "description": text[:5000],
            "employment": employment,
            "source": "Enbek.kz",
            "link": url,
        }

    except requests.RequestException as error:
        logger.warning(
            "Enbek request error: %s",
            error,
        )

    except Exception as error:
        logger.exception(
            "Enbek parsing error: %s",
            error,
        )

    return None


# ================= SEARCH VACANCIES =================

def get_enbek_vacancies(
    filter_type="all",
    limit=10,
):
    result = []
    seen_links = set()
    links = []

    queries = SEARCH_WORDS.get(
        filter_type,
        [""],
    )

    for word in queries:
        try:
            params = {}

            if word:
                params["search"] = word

            response = requests.get(
                ENBEK_SEARCH_URL,
                params=params,
                headers=HEADERS,
                timeout=20,
            )

            print(
                "Enbek status:",
                response.status_code,
                "query:",
                word,
                flush=True,
            )

            if response.status_code != 200:
                continue

            soup = BeautifulSoup(
                response.text,
                "html.parser",
            )

            count = 0

            for tag in soup.find_all("a", href=True):
                href = tag.get("href", "")

                if "/ru/vacancy/" not in href:
                    continue

                url = urljoin(
                    ENBEK_BASE_URL,
                    href,
                )

                parsed = urlparse(url)

                if parsed.netloc not in (
                    "enbek.kz",
                    "www.enbek.kz",
                ):
                    continue

                if url in seen_links:
                    continue

                seen_links.add(url)
                links.append(url)
                count += 1

            print(
                "Enbek links:",
                count,
                flush=True,
            )

        except requests.RequestException as error:
            logger.warning(
                "Enbek search error: %s",
                error,
            )

    # Бір уақытта бірнеше вакансияны тексеру
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {
            executor.submit(
                parse_enbek_vacancy,
                url,
            ): url
            for url in links[:40]
        }

        for future in as_completed(futures):
            try:
                job = future.result()

                if not job:
                    continue

                if not matches_filter(
                    job,
                    filter_type,
                ):
                    continue

                result.append(job)

                if len(result) >= limit:
                    break

            except Exception as error:
                logger.warning(
                    "Vacancy worker error: %s",
                    error,
                )

    return result[:limit]


# ================= MAIN FUNCTION =================

def get_vacancies(
    search_text="",
    filter_type="all",
):
    """
    bot.py қолданатын негізгі функция.
    Тек Enbek.kz нәтижелерін қайтарады.
    """

    if filter_type not in SEARCH_WORDS:
        filter_type = "all"

    vacancies = get_enbek_vacancies(
        filter_type=filter_type,
        limit=10,
    )

    print(
        "Enbek vacancies:",
        len(vacancies),
        flush=True,
    )

    return vacancies
