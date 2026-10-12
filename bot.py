import os
import tempfile
import base64

from dotenv import load_dotenv
from openai import OpenAI
from gtts import gTTS

from vacancy import get_vacancies

from telegram import (
    Update,
    ReplyKeyboardMarkup,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

from PyPDF2 import PdfReader


# ==================================================
# ENV
# ==================================================

load_dotenv()

TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

print("TELEGRAM_TOKEN loaded:", bool(TOKEN))
print("OPENAI_API_KEY loaded:", bool(OPENAI_API_KEY))

if not TOKEN or not OPENAI_API_KEY:
    print("❌ Missing ENV variables")
    exit()


# ==================================================
# OPENAI
# ==================================================

client = OpenAI(
    api_key=OPENAI_API_KEY
)


def ask_ai(prompt):

    try:

        response = client.responses.create(
            model="gpt-5-mini",

            instructions=(
                "Ты помощник по работе, обучению и резюме. "
                "Помогай школьникам, молодым людям "
                "и людям с инвалидностью. "
                "Отвечай понятно, кратко и по существу. "
                "Основной язык ответа — русский."
            ),

            input=prompt,
        )

        return response.output_text

    except Exception as e:

        print("OpenAI error:", e)

        error_text = str(e)

        if (
            "credit_balance_exhausted" in error_text
            or "insufficient_quota" in error_text
            or "429" in error_text
        ):

            return (
                "🤖 AI-помощник временно недоступен.\n\n"
                "Попробуйте немного позже."
            )

        return (
            "❌ Сейчас AI не смог обработать запрос.\n\n"
            "Попробуйте ещё раз позже."
        )


# ==================================================
# MAIN MENU
# ==================================================

MENU = ReplyKeyboardMarkup(
    [
        [
            "🎓 Обучение",
            "💼 Резюме",
        ],
        [
            "🔎 Вакансии",
            "💬 Мотивация",
        ],
        [
            "📸 Фото для резюме",
        ],
        [
            "ℹ️ О проекте",
        ],
    ],
    resize_keyboard=True,
)


# ==================================================
# TRAINING TEXT
# ==================================================

def training_text():

    return (
        "🎓 Как правильно составить резюме:\n\n"
        "1. Кратко и по делу\n"
        "2. Укажи реальные навыки\n"
        "3. Добавь опыт работы\n"
        "4. Избегай лишнего текста\n\n"
        "📌 Делай акцент на результатах"
    )


# ==================================================
# MOTIVATION
# ==================================================

def get_motivation():

    return (
        "✨ Твои возможности не ограничиваются обстоятельствами.\n\n"
        "📚 Образование — это твой инструмент свободы.\n\n"
        "🚀 Каждый новый навык — это шаг к независимости "
        "и уверенности в себе.\n\n"
        "⏳ Не важно, с какой скоростью ты идёшь — "
        "важно, что ты не останавливаешься.\n\n"
        "💡 Верь в себя и двигайся вперёд!"
    )


# ==================================================
# ABOUT PROJECT
# ==================================================

def project_text():

    return (
        "ℹ️ О проекте\n\n"
        "🤖 AI-ментор помогает с обучением, "
        "резюме и поиском работы.\n\n"
        "🎯 Цель проекта — сделать карьерные "
        "возможности доступнее для каждого."
    )


# ==================================================
# START
# ==================================================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(
        "👋 Добро пожаловать!\n\n"
        "🤖 Я AI-ментор по обучению и трудоустройству.\n\n"
        "Я могу помочь с резюме, обучением, "
        "карьерными вопросами и поиском вакансий.",
        reply_markup=MENU
    )


# ==================================================
# RESUME ANALYSIS
# ==================================================

def check_resume(text):

    resume_text = text[:15000]

    prompt = f"""
Проанализируй следующее резюме:

{resume_text}

Дай ответ по структуре:

1. 🔎 Ошибки
2. ✨ Что можно улучшить
3. 💪 Сильные стороны
4. 📊 Оценка резюме от 0 до 100
5. 💡 Конкретные рекомендации

Не придумывай опыт, которого нет в резюме.

Пиши понятно и профессионально.
"""

    return ask_ai(prompt)


# ==================================================
# VACANCY MENU
# ==================================================

async def show_vacancies(update: Update):

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "🎓 Для молодежи",
                    callback_data="vac_youth"
                )
            ],
            [
                InlineKeyboardButton(
                    "♿ Доступные вакансии",
                    callback_data="vac_accessible"
                )
            ],
            [
                InlineKeyboardButton(
                    "🏠 Удалённая работа",
                    callback_data="vac_remote"
                )
            ],
            [
                InlineKeyboardButton(
                    "🕐 Гибкий график",
                    callback_data="vac_flexible"
                )
            ],
            [
                InlineKeyboardButton(
                    "💼 Все вакансии",
                    callback_data="vac_all"
                )
            ],
        ]
    )

    await update.message.reply_text(
        "🔎 Выберите тип вакансий:",
        reply_markup=keyboard
    )


# ==================================================
# VACANCY CALLBACK
# ==================================================

async def vacancy_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    if not query:
        return

    await query.answer()

    filter_map = {
        "vac_youth": "youth",
        "vac_accessible": "accessible",
        "vac_remote": "remote",
        "vac_flexible": "flexible",
        "vac_all": "all",
    }

    filter_names = {
        "youth": "🎓 Для молодежи",
        "accessible": "♿ Доступные вакансии",
        "remote": "🏠 Удалённая работа",
        "flexible": "🕐 Гибкий график",
        "all": "💼 Все вакансии",
    }

    filter_type = filter_map.get(
        query.data,
        "all"
    )

    filter_name = filter_names.get(
        filter_type,
        "💼 Все вакансии"
    )

    await query.message.reply_text(
        "🔎 Ищу актуальные вакансии...\n\n"
        f"{filter_name}"
    )

    try:

        vacancies = get_vacancies(
            filter_type=filter_type
        )

        if not vacancies:

            await query.message.reply_text(
                "😔 Сейчас подходящие вакансии не найдены.\n\n"
                "Попробуйте другой фильтр "
                "или повторите поиск позже."
            )

            return

        await query.message.reply_text(
            f"💼 Найдено вакансий: {len(vacancies)}"
        )

        for job in vacancies:

            name = job.get(
                "name",
                "Без названия"
            )

            company = job.get(
                "company",
                "Компания не указана"
            )

            city = job.get(
                "city",
                "Казахстан"
            )

            salary = job.get(
                "salary",
                "Не указана"
            )

            schedule = job.get(
                "schedule",
                "Не указан"
            )

            experience = job.get(
                "experience",
                ""
            )

            published = job.get(
                "published",
                ""
            )

            source = job.get(
                "source",
                "Источник не указан"
            )

            link = job.get(
                "link"
            )

            message = (
                f"💼 {name}\n\n"
                f"🏢 Компания: {company}\n"
                f"📍 Регион: {city}\n"
                f"💰 Зарплата: {salary}\n"
                f"🕐 График: {schedule}\n"
            )

            if experience:

                message += (
                    f"🎯 Опыт: {experience}\n"
                )

            if published:

                message += (
                    f"📅 Опубликовано: {published}\n"
                )

            message += (
                f"🌐 Источник: {source}"
            )

            if link:

                keyboard = InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                "🔗 Открыть вакансию",
                                url=link
                            )
                        ]
                    ]
                )

                await query.message.reply_text(
                    message,
                    reply_markup=keyboard
                )

            else:

                await query.message.reply_text(
                    message
                )

    except Exception as e:

        print(
            "Vacancy callback error:",
            e
        )

        await query.message.reply_text(
            "❌ Не удалось загрузить вакансии.\n\n"
            "Попробуйте позже."
        )


# ==================================================
# LONG MESSAGE
# ==================================================

async def send_long_message(
    update: Update,
    text: str
):

    if not text:
        return

    max_length = 3900

    if len(text) <= max_length:

        await update.message.reply_text(
            text
        )

        return

    for i in range(
        0,
        len(text),
        max_length
    ):

        await update.message.reply_text(
            text[i:i + max_length]
        )


# ==================================================
# MAIN TEXT HANDLER
# ==================================================

async def handle(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not update.message:
        return

    text = update.message.text or ""


    # ==================================================
    # ОБУЧЕНИЕ
    # ==================================================

    if text == "🎓 Обучение":

        video_path = "object.mp4"

        if not os.path.exists(video_path):

            print(
                "❌ Video file not found:",
                video_path
            )

            await update.message.reply_text(
                "❌ Видео файл не найден."
            )

            return

        try:

            print(
                "🎬 Sending training video..."
            )

            with open(
                video_path,
                "rb"
            ) as video:

                await update.message.reply_video(
                    video=video,
                    caption=training_text(),
                    read_timeout=120,
                    write_timeout=120,
                    connect_timeout=30,
                    pool_timeout=30,
                )

            print(
                "✅ Training video sent"
            )

        except Exception as e:

            print(
                "Video error:",
                repr(e)
            )

        return


    # ==================================================
    # RESUME
    # ==================================================

    if text == "💼 Резюме":

        await update.message.reply_text(
            "📄 Создайте резюме здесь:\n"
            "https://www.jobseeker.com\n\n"
            "📤 Затем отправьте PDF — я проверю его 🤖"
        )

        return


    # ==================================================
    # VACANCIES
    # ==================================================

    if text == "🔎 Вакансии":

        await show_vacancies(
            update
        )

        return


    # ==================================================
    # MOTIVATION
    # ==================================================

    if text == "💬 Мотивация":

        await update.message.reply_text(
            get_motivation()
        )

        return


    # ==================================================
    # RESUME PHOTO
    # ==================================================

    if text == "📸 Фото для резюме":

        context.user_data[
            "awaiting_resume_photo"
        ] = True

        await update.message.reply_text(
            "📸 Отправьте свою фотографию.\n\n"
            "Я подготовлю её для резюме:\n"
            "• профессиональный стиль\n"
            "• нейтральный фон\n"
            "• естественное освещение\n"
            "• аккуратный деловой вид\n\n"
            "👤 Постараюсь сохранить вашу внешность."
        )

        return


    # ==================================================
    # ABOUT
    # ==================================================

    if text == "ℹ️ О проекте":

        await update.message.reply_text(
            project_text()
        )

        return


    # ==================================================
    # NORMAL AI QUESTION
    # ==================================================

    if not text.strip():
        return

    await update.message.reply_text(
        "🤖 Думаю..."
    )

    response = ask_ai(
        text
    )

    await send_long_message(
        update,
        response
    )


# ==================================================
# PDF HANDLER
# ==================================================

async def handle_file(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not update.message:
        return

    doc = update.message.document

    if not doc:
        return

    file_name = (
        doc.file_name
        or ""
    )

    if not file_name.lower().endswith(
        ".pdf"
    ):

        await update.message.reply_text(
            "❌ Отправьте только PDF файл."
        )

        return

    file = await doc.get_file()

    tmp = tempfile.NamedTemporaryFile(
        delete=False,
        suffix=".pdf"
    )

    path = tmp.name
    tmp.close()

    try:

        await file.download_to_drive(
            path
        )

        reader = PdfReader(
            path
        )

        resume_text = ""

        for page in reader.pages:

            try:

                page_text = (
                    page.extract_text()
                    or ""
                )

                if page_text:

                    resume_text += (
                        page_text
                        + "\n"
                    )

            except Exception as e:

                print(
                    "PDF page error:",
                    e
                )

        if not resume_text.strip():

            await update.message.reply_text(
                "❌ Не удалось найти текст в PDF.\n\n"
                "Возможно, резюме сохранено "
                "как изображение."
            )

            return

        await update.message.reply_text(
            "🤖 Анализирую резюме..."
        )

        result = check_resume(
            resume_text
        )

        await send_long_message(
            update,
            result
        )

    except Exception as e:

        print(
            "PDF error:",
            e
        )

        await update.message.reply_text(
            "❌ Ошибка при обработке PDF-файла."
        )

    finally:

        try:

            if os.path.exists(path):

                os.remove(
                    path
                )

        except Exception as e:

            print(
                "Temp delete error:",
                e
            )


# ==================================================
# VOICE HANDLER
# Voice -> Text -> AI -> Voice
# ==================================================

async def handle_voice(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not update.message:
        return

    if not update.message.voice:
        return

    voice_path = None
    answer_path = None

    try:

        voice = update.message.voice

        telegram_file = await voice.get_file()

        tmp_voice = tempfile.NamedTemporaryFile(
            delete=False,
            suffix=".ogg"
        )

        voice_path = tmp_voice.name
        tmp_voice.close()

        await telegram_file.download_to_drive(
            voice_path
        )

        await update.message.reply_text(
            "🎙 Распознаю голос..."
        )


        # ==============================================
        # VOICE -> TEXT
        # ==============================================

        with open(
            voice_path,
            "rb"
        ) as audio_file:

            transcription = (
                client.audio.transcriptions.create(
                    model="gpt-4o-mini-transcribe",
                    file=audio_file,
                )
            )

        user_text = (
            transcription.text
            or ""
        ).strip()

        if not user_text:

            await update.message.reply_text(
                "❌ Не удалось распознать голос."
            )

            return

        print(
            "🎙 Voice recognized:",
            user_text
        )

        await update.message.reply_text(
            "📝 Вы сказали:\n"
            f"{user_text}\n\n"
            "🤖 Думаю..."
        )


        # ==============================================
        # TEXT -> AI
        # ==============================================

        ai_answer = ask_ai(
            user_text
        )

        await send_long_message(
            update,
            ai_answer
        )


        # ==============================================
        # AI -> VOICE
        # ==============================================

        await update.message.reply_text(
            "🔊 Озвучиваю ответ..."
        )

        tmp_answer = tempfile.NamedTemporaryFile(
            delete=False,
            suffix=".mp3"
        )

        answer_path = tmp_answer.name
        tmp_answer.close()

        tts = gTTS(
            text=ai_answer,
            lang="ru"
        )

        tts.save(
            answer_path
        )

        with open(
            answer_path,
            "rb"
        ) as audio:

            await update.message.reply_voice(
                voice=audio,
                read_timeout=120,
                write_timeout=120,
                connect_timeout=30,
                pool_timeout=30,
            )

        print(
            "🔊 Voice answer sent"
        )

    except Exception as e:

        import traceback
        traceback.print_exc()
        print("Voice error:", repr(e), flush=True)

        error_text = str(e)

        if (
            "429" in error_text
            or "insufficient_quota" in error_text
            or "credit_balance_exhausted" in error_text
        ):

            await update.message.reply_text(
                "🤖 Голосовой AI временно недоступен."
            )

        else:

            await update.message.reply_text(
                "❌ Не удалось обработать голосовое сообщение."
            )

    finally:

        if (
            voice_path
            and os.path.exists(voice_path)
        ):

            try:

                os.remove(
                    voice_path
                )

            except Exception as e:

                print(
                    "Voice temp delete error:",
                    e
                )

        if (
            answer_path
            and os.path.exists(answer_path)
        ):

            try:

                os.remove(
                    answer_path
                )

            except Exception as e:

                print(
                    "AI voice temp delete error:",
                    e
                )


# ==================================================
# RESUME PHOTO HANDLER
# Photo -> OpenAI -> Professional Resume Photo
# ==================================================

async def handle_photo(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not update.message:
        return

    if not update.message.photo:
        return


    # Resume Photo батырмасы басылмаған болса
    if not context.user_data.get(
        "awaiting_resume_photo",
        False
    ):

        await update.message.reply_text(
            "📸 Для обработки фотографии сначала нажмите "
            "«📸 Фото для резюме»."
        )

        return


    input_path = None
    output_path = None

    try:

        # Режимді өшіреміз
        context.user_data[
            "awaiting_resume_photo"
        ] = False


        # ==============================================
        # GET BEST QUALITY TELEGRAM PHOTO
        # ==============================================

        photo = update.message.photo[-1]

        telegram_file = await photo.get_file()


        # ==============================================
        # TEMP INPUT FILE
        # ==============================================

        tmp_input = tempfile.NamedTemporaryFile(
            delete=False,
            suffix=".jpg"
        )

        input_path = tmp_input.name
        tmp_input.close()


        # ==============================================
        # DOWNLOAD PHOTO
        # ==============================================

        await telegram_file.download_to_drive(
            input_path
        )

        await update.message.reply_text(
            "📸 Фото получено.\n\n"
            "🤖 Подготавливаю профессиональное "
            "фото для резюме..."
        )


        # ==============================================
        # OPENAI IMAGE EDIT
        # ==============================================

        prompt = """
Edit the provided photo into a natural professional
resume portrait.

Preserve the identity and recognizable facial features
of the person in the original photo.

Keep the person's natural appearance.

Do not change the person's age or body shape.

Create:
- a clean neutral professional background
- soft realistic lighting
- a professional resume/CV portrait
- natural skin texture
- realistic photographic appearance
- neat head-and-shoulders composition

Avoid:
- excessive retouching
- glamour styling
- unrealistic facial changes
- text
- logos
- frames
- watermarks

The final image should look appropriate for a CV,
resume or professional profile.
"""

        with open(
            input_path,
            "rb"
        ) as image_file:

            result = client.images.edit(
                model="gpt-image-1.5",
                image=image_file,
                prompt=prompt,
                input_fidelity="high",
                output_format="png",
            )


        # ==============================================
        # GET GENERATED IMAGE
        # ==============================================

        image_base64 = (
            result.data[0].b64_json
        )

        if not image_base64:

            raise Exception(
                "OpenAI returned no image data"
            )


        # ==============================================
        # BASE64 -> BYTES
        # ==============================================

        image_bytes = base64.b64decode(
            image_base64
        )


        # ==============================================
        # SAVE GENERATED PHOTO
        # ==============================================

        tmp_output = tempfile.NamedTemporaryFile(
            delete=False,
            suffix=".png"
        )

        output_path = tmp_output.name

        tmp_output.write(
            image_bytes
        )

        tmp_output.close()


        # ==============================================
        # SEND RESULT
        # ==============================================

        with open(
            output_path,
            "rb"
        ) as result_photo:

            await update.message.reply_photo(
                photo=result_photo,
                caption=(
                    "✅ Готово!\n\n"
                    "📸 Профессиональное фото "
                    "для резюме подготовлено."
                ),
                read_timeout=120,
                write_timeout=120,
                connect_timeout=30,
                pool_timeout=30,
            )

        print(
            "📸 Resume photo generated successfully"
        )


    except Exception as e:

        import traceback
        traceback.print_exc()
        print("Resume photo error:", repr(e), flush=True)

        error_text = str(e)

        if (
            "429" in error_text
            or "insufficient_quota" in error_text
            or "credit_balance_exhausted" in error_text
        ):

            await update.message.reply_text(
                "🤖 Обработка фото временно недоступна.\n\n"
                "Проверьте баланс OpenAI API."
            )

        else:

            await update.message.reply_text(
                "❌ Не удалось обработать фотографию.\n\n"
                "Попробуйте другое фото позже."
            )


    finally:

        # ==============================================
        # DELETE INPUT PHOTO
        # ==============================================

        if (
            input_path
            and os.path.exists(input_path)
        ):

            try:

                os.remove(
                    input_path
                )

            except Exception as e:

                print(
                    "Photo input delete error:",
                    e
                )


        # ==============================================
        # DELETE GENERATED PHOTO
        # ==============================================

        if (
            output_path
            and os.path.exists(output_path)
        ):

            try:

                os.remove(
                    output_path
                )

            except Exception as e:

                print(
                    "Photo output delete error:",
                    e
                )


# ==================================================
# ERROR HANDLER
# ==================================================

async def error_handler(
    update: object,
    context: ContextTypes.DEFAULT_TYPE
):

    print(
        "Telegram error:",
        context.error
    )


# ==================================================
# MAIN
# ==================================================

def main():

    print(
        "🚀 Starting Emin Askerov bot..."
    )

    app = (
        ApplicationBuilder()
        .token(TOKEN)
        .connect_timeout(30)
        .read_timeout(120)
        .write_timeout(120)
        .pool_timeout(30)
        .build()
    )


    # START
    app.add_handler(
        CommandHandler(
            "start",
            start
        )
    )


    # VACANCIES
    app.add_handler(
        CallbackQueryHandler(
            vacancy_callback,
            pattern=r"^vac_"
        )
    )


    # PDF
    app.add_handler(
        MessageHandler(
            filters.Document.ALL,
            handle_file
        )
    )


    # VOICE
    app.add_handler(
        MessageHandler(
            filters.VOICE,
            handle_voice
        )
    )


    # PHOTO
    app.add_handler(
        MessageHandler(
            filters.PHOTO,
            handle_photo
        )
    )


    # TEXT
    app.add_handler(
        MessageHandler(
            filters.TEXT
            & ~filters.COMMAND,
            handle
        )
    )


    # ERRORS
    app.add_error_handler(
        error_handler
    )


    print(
        "🤖 Emin Askerov bot started"
    )


    app.run_polling(
        allowed_updates=Update.ALL_TYPES
    )


# ==================================================
# RUN
# ==================================================

if __name__ == "__main__":
    main()