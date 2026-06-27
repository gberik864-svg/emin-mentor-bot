import os
import tempfile
import requests

from dotenv import load_dotenv

from groq import Groq
from openai import OpenAI

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
OPENAI_KEY = os.getenv("OPENAI_API_KEY")


if not TOKEN or not GROQ_KEY:
    print("Missing ENV variables")
    exit()


# ================= AI =================

client = Groq(
    api_key=GROQ_KEY
)


openai_client = OpenAI(
    api_key=OPENAI_KEY
)



def ask_ai(prompt):

    try:

        response = client.chat.completions.create(

            model="llama-3.3-70b-versatile",

            messages=[
                {
                    "role":"system",
                    "content":
                    "Ты помощник по работе, обучению и резюме."
                },
                {
                    "role":"user",
                    "content":prompt
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
["🎤 Голосовой помощник", "🔎 Вакансии"],
["🖼 CV Фото"],
["💬 Мотивация"],
["ℹ️ О проекте"]

],

resize_keyboard=True

)



# ================= TEXT =================


def get_motivation():

    return (
        "✨ Ваши возможности не ограничиваются обстоятельствами.\n\n"
        "📚 Обучение — путь к развитию.\n"
        "🚀 Каждый новый навык приближает к цели.\n\n"
        "💪 Верьте в себя!"
    )



def project_text():

    return (
        "🤖 AI-ментор по обучению и трудоустройству.\n\n"
        "Возможности:\n"
        "• анализ резюме\n"
        "• голосовой помощник\n"
        "• поиск вакансий\n"
        "• подготовка CV фото\n\n"
        "Цель — помочь пользователю найти путь к работе."
    )



def training_text():

    return (
        "🎓 Как сделать хорошее резюме:\n\n"
        "1. Укажите навыки\n"
        "2. Добавьте опыт\n"
        "3. Пишите кратко\n"
        "4. Покажите результаты"
    )



# ================= START =================


async def start(update: Update, context):

    await update.message.reply_text(

        "👋 Добро пожаловать!\n\n"
        "🤖 AI-ментор по обучению и трудоустройству",

        reply_markup=MENU
    )



# ================= VOICE =================


async def voice_handler(update, context):

    voice = update.message.voice

    file = await voice.get_file()

    path = "voice.ogg"

    await file.download_to_drive(path)


    text = openai_client.audio.transcriptions.create(

        model="whisper-1",

        file=open(path,"rb")

    )


    answer = ask_ai(text.text)



    audio = openai_client.audio.speech.create(

        model="gpt-4o-mini-tts",

        voice="alloy",

        input=answer

    )


    audio.stream_to_file(
        "answer.mp3"
    )


    await update.message.reply_voice(

        voice=open(
            "answer.mp3",
            "rb"
        )

    )



# ================= JOBS =================


async def jobs(update, context):


    url = "https://api.hh.ru/vacancies"


    params = {

        "text":
        "удаленная работа гибкий график",

        "per_page":5
    }


    data = requests.get(

        url,
        params=params

    ).json()



    result = "🔎 Подходящие вакансии:\n\n"



    for item in data["items"]:

        result += (

            "💼 "
            + item["name"]
            + "\n"
            + item["alternate_url"]
            + "\n\n"

        )


    await update.message.reply_text(result)





# ================= PHOTO =================


async def photo_handler(update, context):

    await update.message.reply_text(

        "🖼 Отправьте ваше фото.\n\n"
        "AI подготовит профессиональный портрет для резюме."

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
3. Оценку от 0 до 100
4. Совет
"""

    )



# ================= TEXT =================


async def handle(update, context):

    text = update.message.text or ""



    if text == "🎓 Обучение":

        await update.message.reply_text(
            training_text()
        )
        return



    if text == "💼 Резюме":

        await update.message.reply_text(
            "📄 Отправьте PDF резюме для анализа."
        )
        return



    if text == "🎤 Голосовой помощник":

        await update.message.reply_text(
            "🎤 Отправьте голосовое сообщение."
        )
        return



    if text == "🔎 Вакансии":

        await jobs(update, context)
        return



    if text == "🖼 CV Фото":

        await photo_handler(update, context)
        return



    if text == "💬 Мотивация":

        await update.message.reply_text(
            get_motivation()
        )
        return



    if text == "ℹ️ О проекте":

        await update.message.reply_text(
            project_text()
        )
        return



    answer = ask_ai(text)

    await update.message.reply_text(answer)



# ================= PDF =================


async def handle_file(update, context):

    doc = update.message.document


    if not doc.file_name.endswith(".pdf"):

        return


    file = await doc.get_file()


    tmp = tempfile.NamedTemporaryFile(
        delete=False,
        suffix=".pdf"
    )


    path = tmp.name

    tmp.close()



    await file.download_to_drive(path)



    reader = PdfReader(path)


    text = ""


    for page in reader.pages:

        text += page.extract_text() or ""



    result = check_resume(text)



    await update.message.reply_text(result)



# ================= MAIN =================


def main():

    app = ApplicationBuilder().token(TOKEN).build()



    app.add_handler(
        CommandHandler(
            "start",
            start
        )
    )


    app.add_handler(

        MessageHandler(
            filters.VOICE,
            voice_handler
        )

    )


    app.add_handler(

        MessageHandler(
            filters.Document.ALL,
            handle_file
        )

    )


    app.add_handler(

        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle
        )

    )


    print("Bot started")


    app.run_polling()



if __name__ == "__main__":

    main()