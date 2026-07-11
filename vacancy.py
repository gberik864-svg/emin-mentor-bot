def get_vacancies():

    vacancies = [
        {
            "name": "Оператор Call-центра",
            "company": "Kaspi.kz",
            "city": "Алматы",
            "link": "https://kaspi.kz"
        },
        {
            "name": "Менеджер поддержки",
            "company": "Halyk Bank",
            "city": "Астана",
            "link": "https://halykbank.kz"
        },
        {
            "name": "Специалист по работе с клиентами",
            "company": "Beeline Казахстан",
            "city": "Шымкент",
            "link": "https://beeline.kz"
        },
        {
            "name": "Оператор ПК",
            "company": "Freedom Bank",
            "city": "Алматы",
            "link": "https://bankffin.kz"
        },
        {
            "name": "Удаленный консультант",
            "company": "Tele2 Казахстан",
            "city": "Удаленно",
            "link": "https://tele2.kz"
        }
    ]

    result = "💼 Подходящие вакансии:\n\n"

    for job in vacancies:
        result += (
            f"🔹 {job['name']}\n"
            f"🏢 {job['company']}\n"
            f"📍 {job['city']}\n"
            f"🔗 {job['link']}\n\n"
        )

    return result