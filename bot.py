import os
import tempfile
from dotenv import load_dotenv

from voice import voice_handler
from vacancy import get_vacancies

from groq import Groq

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

from PyPDF2 import PdfReader


# ================= ENV =================

load_dotenv()

TOKEN = os.getenv("TELEGRAM_TOKEN")
GROQ_KEY = os.getenv("GROQ_API_KEY")


print("TOKEN =", TOKEN)
print("GROQ =", GROQ_KEY)


if not TOKEN or not GROQ_KEY:
    print("Missing ENV variables")
    exit()



# ================= GROQ =================

client = Groq(
    api_key=GROQ_KEY
)


def ask_ai(prompt):

    try:

        response = client.chat.completions.create(

            model="llama-3.3-70b-versatile",

            messages=[

                {
                    "role": "system",
                    "content":
                    "Ты помощник по работе, обучению и резюме."
                },

                {
                    "role": "user",
                    "content": prompt
                }

            ]

        )


        return response.choices[0].message.content


    except Exception as e:

        return f"❌ AI ошибка: {e}"




# ================= MENU =================


MENU = ReplyKeyboardMarkup(

    [
        ["🎓 Обучение", "💼 Резюме"],
        ["💼 Вакансии"],
        ["💬 Мотивация"],
        ["ℹ️ О проекте"]
    ],

    resize_keyboard=True

)




# ================= TEXT =================


def get_motivation():

    return (

        "✨ Твои возможности не ограничиваются обстоятельствами.\n"
        "📚 Образование — это твой инструмент свободы.\n"
        "🚀 Каждый новый навык — это шаг к независимости и уверенности в себе.\n"
        "⏳ Не важно, с какой скоростью ты идёшь — важно, что ты не останавливаешься.\n\n"
        "💡 Верь в себя и двигайся вперёд!"

    )



def project_text():

    return (

        "AI-ментор по обучению и трудоустройству для людей с инвалидностью.\n\n"

        "Основные возможности:\n"
        "• анализ резюме\n"
        "• ответы на вопросы\n"
        "• помощь в обучении\n"
        "• карьерные советы\n"
        "• поиск вакансий\n"
        "• голосовой помощник\n\n"

        "Цель проекта — сопровождение пользователя от обучения до трудоустройства."

    )



def training_text():

    return (

        "🎓 Как правильно составить резюме:\n\n"
        "1. Кратко и по делу\n"
        "2. Укажи реальные навыки\n"
        "3. Добавь опыт работы\n"
        "4. Избегай лишнего текста\n\n"
        "📌 Делай акцент на результатах"

    )




# ================= START =================


async def start(update: Update, context):

    await update.message.reply_text(

        "👋 Добро пожаловать!\n\n"
        "🤖 AI-ментор по обучению и трудоустройству.",

        reply_markup=MENU

    )




# ================= RESUME =================


def check_resume(text):

    return ask_ai(

f"""

Проанализируй резюме:

{text}

Дай:

1. Ошибки
2. Улучшения
3. Оценку (0-100)
4. Совет

"""

    )




# ================= HANDLER =================


async def handle(update: Update, context):

    text = update.message.text or ""



    if text == "🎓 Обучение":

        video_path = "object.mp4"


        if os.path.exists(video_path):

            await update.message.reply_video(

                video=open(video_path, "rb"),

                caption=training_text()

            )

        else:

            await update.message.reply_text(
                "❌ Видео файл не найден"
            )


        return




    if text == "💼 Вакансии":

        await update.message.reply_text(

            get_vacancies()

        )

        return




    if text == "💼 Резюме":

        await update.message.reply_text(

            "📄 Создайте резюме\n\n"
            "📤 Затем отправьте PDF — я проверю его 🤖"

        )

        return