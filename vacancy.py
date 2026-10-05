import re
import requests

from bs4 import BeautifulSoup
from urllib.parse import urljoin


# ==================================================
# SETTINGS
# ==================================================

ENBEK_BASE_URL = "https://www.enbek.kz"
ENBEK_SEARCH_URL = "https://www.enbek.kz/ru/search/vacancy"

HH_API_URL = "https://api.hh.ru/vacancies"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/154.0 Safari/537.36"
    ),
    "Accept-Language": "ru-RU,ru;q=0.9",
}


# ==================================================
# CLEAN TEXT
# ==================================================

def clean_text(text):

    if not text:
        return ""

    return " ".join(
        text.split()
    )


# ==================================================
# HH SALARY
# ==================================================

def format_hh_salary(salary):

    if not salary:
        return "Не указана"

    salary_from = salary.get("from")
    salary_to = salary.get("to")
    currency = salary.get(
        "currency",
        ""
    )

    if currency == "KZT":
        currency = "₸"

    if salary_from and salary_to:

        return (
            f"{salary_from:,} – "
            f"{salary_to:,} "
            f"{currency}"
        ).replace(",", " ")

    if salary_from:

        return (
            f"от {salary_from:,} "
            f"{currency}"
        ).replace(",", " ")

    if salary_to:

        return (
            f"до {salary_to:,} "
            f"{currency}"
        ).replace(",", " ")

    return "Не указана"


# ==================================================
# ENBEK SEARCH
# ==================================================

def get_enbek_vacancies(
    filter_type="all",
    limit=5
):

    try:

        response = requests.get(
            ENBEK_SEARCH_URL,
            headers=HEADERS,
            timeout=20,
        )

        print(
            "Enbek status:",
            response.status_code
        )

        if response.status_code != 200:

            print(
                "Enbek error:",
                response.text[:300]
            )

            return []

        soup = BeautifulSoup(
            response.text,
            "html.parser"
        )

        vacancy_links = []

        # ==================================================
        # FIND REAL VACANCY LINKS
        # ==================================================

        for a in soup.find_all(
            "a",
            href=True
        ):

            href = a.get(
                "href",
                ""
            )

            if "/ru/vacancy/" not in href:
                continue

            if "pdf" in href.lower():
                continue

            full_url = urljoin(
                ENBEK_BASE_URL,
                href
            )

            if full_url not in vacancy_links:

                vacancy_links.append(
                    full_url
                )

        print(
            "Enbek links found:",
            len(vacancy_links)
        )

        vacancies = []

        # ==================================================
        # PARSE VACANCIES
        # ==================================================

        for url in vacancy_links[:40]:

            job = parse_enbek_vacancy(
                url
            )

            if not job:
                continue

            if not matches_filter(
                job,
                filter_type
            ):
                continue

            vacancies.append(
                job
            )

            if len(vacancies) >= limit:
                break

        print(
            "Enbek vacancies:",
            len(vacancies)
        )

        return vacancies

    except requests.RequestException as e:

        print(
            "Enbek request error:",
            e
        )

        return []

    except Exception as e:

        print(
            "Enbek error:",
            e
        )

        return []


# ==================================================
# PARSE ONE ENBEK VACANCY
# ==================================================

def parse_enbek_vacancy(url):

    try:

        response = requests.get(
            url,
            headers=HEADERS,
            timeout=15,
        )

        if response.status_code != 200:

            print(
                "Vacancy status:",
                response.status_code
            )

            return None

        soup = BeautifulSoup(
            response.text,
            "html.parser"
        )

        text = clean_text(
            soup.get_text(
                " ",
                strip=True
            )
        )

        if not text:
            return None

        lower_text = text.lower()

        # ==================================================
        # TITLE
        # ==================================================

        title = ""

        h1 = soup.find("h1")

        if h1:

            value = clean_text(
                h1.get_text(
                    " ",
                    strip=True
                )
            )

            if value:
                title = value

        if not title:

            h4 = soup.find("h4")

            if h4:

                value = clean_text(
                    h4.get_text(
                        " ",
                        strip=True
                    )
                )

                if value:
                    title = value

        if not title:

            title_tag = soup.find(
                "title"
            )

            if title_tag:

                value = clean_text(
                    title_tag.get_text()
                )

                if value:
                    title = value

        if not title:

            title = "Вакансия Enbek"

        # ==================================================
        # CLEAN TITLE
        # ==================================================

        title = re.sub(
            r"\s*[-|]\s*Enbek.*$",
            "",
            title,
            flags=re.IGNORECASE
        )

        title = clean_text(
            title
        )

        # ==================================================
        # COMPANY
        # ==================================================

        company = "Работодатель Enbek"

        company_link = soup.find(
            "a",
            href=lambda x:
            x and (
                "/company/" in x
                or "/employer/" in x
            )
        )

        if company_link:

            value = clean_text(
                company_link.get_text(
                    " ",
                    strip=True
                )
            )

            if value:

                company = value

        # ==================================================
        # REGION
        # ==================================================

        city = "Казахстан"

        region_patterns = [

            (
                r"Регион\s*[:\-]?\s*"
                r"(.+?)"
                r"(?="
                r"Обучитесь|"
                r"Заработная плата|"
                r"Зарплата|"
                r"График|"
                r"Режим работы|"
                r"Опыт работы|"
                r"Опыт|"
                r"Образование|"
                r"Требования|"
                r"Условия труда|"
                r"Профессиональные навыки|"
                r"Вакансия опубликована|"
                r"Опубликовано|"
                r"$)"
            ),

            (
                r"Место работы\s*[:\-]?\s*"
                r"(.+?)"
                r"(?="
                r"Заработная плата|"
                r"Зарплата|"
                r"График|"
                r"Опыт|"
                r"Образование|"
                r"$)"
            ),
        ]

        for pattern in region_patterns:

            match = re.search(
                pattern,
                text,
                re.IGNORECASE
            )

            if match:

                value = clean_text(
                    match.group(1)
                )

                if value:

                    city = value[:150]

                break

        # ==================================================
        # REMOVE SKILLS ENBEK TEXT FROM REGION
        # ==================================================

        cleanup_words = [
            "Обучитесь новым навыкам",
            "Skills Enbek",
            "Ваш сертификат",
        ]

        for word in cleanup_words:

            if word.lower() in city.lower():

                position = city.lower().find(
                    word.lower()
                )

                city = city[:position]

        city = clean_text(
            city
        )

        if not city:
            city = "Казахстан"

        # ==================================================
        # SALARY
        # ==================================================

        salary = "Не указана"

        salary_patterns = [

            (
                r"от\s+[\d\s]+"
                r"\s+до\s+[\d\s]+"
                r"\s*(?:тенге|тг\.?)"
            ),

            (
                r"от\s+[\d\s]+"
                r"\s*(?:тенге|тг\.?)"
            ),

            (
                r"до\s+[\d\s]+"
                r"\s*(?:тенге|тг\.?)"
            ),

            (
                r"[\d\s]+"
                r"\s*[-–]\s*"
                r"[\d\s]+"
                r"\s*(?:тенге|тг\.?)"
            ),
        ]

        for pattern in salary_patterns:

            match = re.search(
                pattern,
                text,
                re.IGNORECASE
            )

            if match:

                salary = clean_text(
                    match.group(0)
                )

                break

        # ==================================================
        # SCHEDULE
        # ==================================================

        schedule = "Не указан"

        schedules = [
            "Полный рабочий день",
            "Неполный рабочий день",
            "Неполная рабочая неделя",
            "Гибкий график",
            "Вахтовый метод",
            "Посменный",
            "Дистанционная работа",
            "Удалённая работа",
            "Удаленная работа",
            "Надомная работа",
        ]

        for item in schedules:

            if item.lower() in lower_text:

                schedule = item
                break

        # ==================================================
        # EXPERIENCE
        # ==================================================

        experience = ""

        # First check no experience
        if (
            "опыт не требуется"
            in lower_text
        ):

            experience = (
                "Опыт не требуется"
            )

        elif "без опыта" in lower_text:

            experience = (
                "Без опыта"
            )

        else:

            experience_patterns = [

                (
                    r"Опыт работы\s*[:\-]?\s*"
                    r"(.+?)"
                    r"(?="
                    r"Образование|"
                    r"Профессиональные навыки|"
                    r"Требования|"
                    r"Условия труда|"
                    r"График|"
                    r"Режим работы|"
                    r"Вакансия опубликована|"
                    r"Опубликовано|"
                    r"$)"
                ),

                (
                    r"Опыт\s*[:\-]?\s*"
                    r"(.+?)"
                    r"(?="
                    r"Образование|"
                    r"Профессиональные навыки|"
                    r"Требования|"
                    r"Условия труда|"
                    r"График|"
                    r"Вакансия опубликована|"
                    r"Опубликовано|"
                    r"$)"
                ),
            ]

            for pattern in experience_patterns:

                match = re.search(
                    pattern,
                    text,
                    re.IGNORECASE
                )

                if match:

                    value = clean_text(
                        match.group(1)
                    )

                    if value:

                        experience = value[:80]

                    break

        # ==================================================
        # CLEAN EXPERIENCE
        # ==================================================

        if experience:

            stop_words = [
                "Образование",
                "Техническое и профессиональное",
                "Профессиональные навыки",
                "Опубликовано",
            ]

            for word in stop_words:

                position = (
                    experience.lower()
                    .find(word.lower())
                )

                if position != -1:

                    experience = (
                        experience[:position]
                    )

            experience = clean_text(
                experience
            )

        # ==================================================
        # PUBLISHED DATE
        # ==================================================

        published = ""

        date_patterns = [

            (
                r"Вакансия опубликована"
                r"\s*[:\-]?\s*"
                r"(\d{2}\.\d{2}\.\d{4})"
            ),

            (
                r"Опубликовано"
                r"\s*[:\-]?\s*"
                r"(\d{2}\.\d{2}\.\d{4})"
            ),
        ]

        for pattern in date_patterns:

            match = re.search(
                pattern,
                text,
                re.IGNORECASE
            )

            if match:

                published = (
                    match.group(1)
                )

                break

        # ==================================================
        # DESCRIPTION
        # Used only for filters
        # ==================================================

        description = text[:5000]

        # ==================================================
        # RESULT
        # ==================================================

        return {

            "name":
                title,

            "company":
                company,

            "city":
                city,

            "salary":
                salary,

            "schedule":
                schedule,

            "experience":
                experience,

            "published":
                published,

            "description":
                description,

            "source":
                "Enbek.kz",

            "link":
                url,
        }

    except Exception as e:

        print(
            "Enbek vacancy parse error:",
            e
        )

        return None


# ==================================================
# FILTERS
# ==================================================

def matches_filter(
    job,
    filter_type
):

    if filter_type == "all":
        return True

    text = (
        f"{job.get('name', '')} "
        f"{job.get('schedule', '')} "
        f"{job.get('experience', '')} "
        f"{job.get('description', '')}"
    ).lower()

    # ==================================================
    # YOUTH
    # ==================================================

    if filter_type == "youth":

        keywords = [
            "без опыта",
            "опыт не требуется",
            "молодеж",
            "молодёж",
            "студент",
            "стажер",
            "стажёр",
            "стажировка",
            "начинающий специалист",
            "от 14 лет",
        ]

        return any(
            word in text
            for word in keywords
        )

    # ==================================================
    # ACCESSIBLE
    # ==================================================

    if filter_type == "accessible":

        keywords = [
            "для лиц с инвалидностью",
            "лица с инвалидностью",
            "лиц с инвалидностью",
            "инвалидность",
            "инвалид",
            "доступная среда",
            "особые потребности",
        ]

        return any(
            word in text
            for word in keywords
        )

    # ==================================================
    # REMOTE
    # ==================================================

    if filter_type == "remote":

        keywords = [
            "удаленная работа",
            "удалённая работа",
            "удаленно",
            "удалённо",
            "дистанционная работа",
            "дистанционно",
            "надомная работа",
        ]

        return any(
            word in text
            for word in keywords
        )

    # ==================================================
    # FLEXIBLE
    # ==================================================

    if filter_type == "flexible":

        keywords = [
            "гибкий график",
            "неполный рабочий день",
            "неполная рабочая неделя",
            "сменный график",
            "посменный",
            "вахтовый метод",
        ]

        return any(
            word in text
            for word in keywords
        )

    return True


# ==================================================
# HH.KZ
# ==================================================

def get_hh_vacancies(
    search_text="",
    filter_type="all",
    limit=5
):

    params = {
        "area": 40,
        "host": "hh.kz",
        "locale": "RU",
        "per_page": limit,
        "page": 0,
        "order_by": "publication_time",
    }

    # ==================================================
    # FILTER SEARCH
    # ==================================================

    if filter_type == "youth":

        search_text = (
            f"{search_text} без опыта"
        ).strip()

    elif filter_type == "remote":

        search_text = (
            f"{search_text} удаленная работа"
        ).strip()

    elif filter_type == "flexible":

        search_text = (
            f"{search_text} гибкий график"
        ).strip()

    elif filter_type == "accessible":

        search_text = (
            f"{search_text} инвалидность"
        ).strip()

    if search_text:

        params["text"] = (
            search_text
        )

    hh_headers = {
        "User-Agent":
            "EminAskerovBot/1.0",

        "HH-User-Agent":
            "EminAskerovBot/1.0",
    }

    try:

        response = requests.get(
            HH_API_URL,
            params=params,
            headers=hh_headers,
            timeout=15,
        )

        print(
            "HH status:",
            response.status_code
        )

        # ==================================================
        # HH BLOCKED
        # ==================================================

        if response.status_code == 403:

            print(
                "HH blocked: "
                "403 Forbidden"
            )

            return []

        if response.status_code != 200:

            print(
                "HH error status:",
                response.status_code
            )

            return []

        data = response.json()

        vacancies = []

        # ==================================================
        # HH ITEMS
        # ==================================================

        for item in data.get(
            "items",
            []
        ):

            employer = (
                item.get("employer")
                or {}
            )

            area = (
                item.get("area")
                or {}
            )

            schedule = (
                item.get("schedule")
                or {}
            )

            experience = (
                item.get("experience")
                or {}
            )

            link = item.get(
                "alternate_url"
            )

            if not link:
                continue

            vacancy = {

                "name":
                    item.get(
                        "name",
                        "Без названия"
                    ),

                "company":
                    employer.get(
                        "name",
                        "Компания не указана"
                    ),

                "city":
                    area.get(
                        "name",
                        "Казахстан"
                    ),

                "salary":
                    format_hh_salary(
                        item.get("salary")
                    ),

                "schedule":
                    schedule.get(
                        "name",
                        "Не указан"
                    ),

                "experience":
                    experience.get(
                        "name",
                        ""
                    ),

                "published":
                    item.get(
                        "published_at",
                        ""
                    ),

                "description":
                    "",

                "source":
                    "HH.kz",

                "link":
                    link,
            }

            vacancies.append(
                vacancy
            )

        print(
            "HH vacancies:",
            len(vacancies)
        )

        return vacancies

    except requests.RequestException as e:

        print(
            "HH request error:",
            e
        )

        return []

    except Exception as e:

        print(
            "HH error:",
            e
        )

        return []


# ==================================================
# GET VACANCIES
# ==================================================

def get_vacancies(
    search_text="",
    filter_type="all"
):

    result = []

    # ==================================================
    # ENBEK
    # ==================================================

    enbek_jobs = get_enbek_vacancies(
        filter_type=filter_type,
        limit=5,
    )

    result.extend(
        enbek_jobs
    )

    # ==================================================
    # HH
    # ==================================================

    hh_jobs = get_hh_vacancies(
        search_text=search_text,
        filter_type=filter_type,
        limit=5,
    )

    result.extend(
        hh_jobs
    )

    # ==================================================
    # REMOVE DUPLICATES
    # ==================================================

    unique = []

    used_links = set()

    for job in result:

        link = job.get(
            "link"
        )

        if not link:
            continue

        if link in used_links:
            continue

        used_links.add(
            link
        )

        unique.append(
            job
        )

    print(
        "Total real vacancies:",
        len(unique)
    )

    return unique[:10]