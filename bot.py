import os
import tempfile
from dotenv import load_dotenv

from groq import Groq

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

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
client = Groq(api_key=GROQ_KEY)

def ask_ai(prompt):
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",  # ✅ FIXED MODEL
            messages=[
                {
                    "role": "system",
                    "content": "Ты помощник по работе, обучению и резюме."
                },
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"❌ AI ошибка: {e}"

# ================= MENU =================
MENU = ReplyKeyboardMarkup(
    [
        ["🎓 Обучение", "💼 Резюме"],
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

# 🔥 UPDATED ONLY "О ПРОЕКТЕ"
def project_text():
    return (
        "AI-ментор по обучению и трудоустройству для людей с инвалидностью.\n\n"
        "Проект создан для помощи людям в профессиональном развитии.\n\n"
        "Основные возможности:\n"
        "• анализ резюме\n"
        "• ответы на вопросы\n"
        "• помощь в обучении\n"
        "• карьерные советы\n\n"
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

# ================= START (UPDATED) =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Добро пожаловать!\n\n"
        "🤖 AI-ментор по обучению и трудоустройству для людей с инвалидностью.",
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
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text or ""

    # ===== ОБУЧЕНИЕ (НЕ ТРОГАЕМ) =====
    if text == "🎓 Обучение":
        video_path = "object.mp4"

        if os.path.exists(video_path):
            await update.message.reply_video(
                video=open(video_path, "rb"),
                caption=training_text()
            )
        else:
            await update.message.reply_text("❌ Видео файл не найден")
        return

    # ===== РЕЗЮМЕ (НЕ ТРОГАЕМ) =====
    if text == "💼 Резюме":
        await update.message.reply_text(
            "📄 Создайте резюме здесь:\n"
            "https://www.jobseeker.com\n\n"
            "📤 Затем отправьте PDF — я проверю его 🤖"
        )
        return

    # ===== МОТИВАЦИЯ (НЕ ТРОГАЕМ) =====
    if text == "💬 Мотивация":
        await update.message.reply_text(get_motivation())
        return

    # ===== О ПРОЕКТЕ (UPDATED) =====
    if text == "ℹ️ О проекте":
        await update.message.reply_text(project_text())
        return

    # ===== AI CHAT =====
    response = ask_ai(text)
    await update.message.reply_text(response)

# ================= PDF =================
async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    doc = update.message.document

    if not doc.file_name.endswith(".pdf"):
        await update.message.reply_text("❌ Отправьте только PDF файл")
        return

    file = await doc.get_file()

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    path = tmp.name
    tmp.close()

    await file.download_to_drive(path)

    try:
        reader = PdfReader(path)
        text = ""

        for page in reader.pages:
            text += page.extract_text() or ""

    except:
        await update.message.reply_text("❌ Ошибка чтения PDF")
        return

    if not text.strip():
        await update.message.reply_text("❌ PDF файл пуст")
        return

    await update.message.reply_text("🤖 Анализирую резюме...")

    result = check_resume(text)
    await update.message.reply_text(result)

    os.remove(path)

# ================= MAIN =================
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_file))

    print("✅ Groq Bot запущен")
    app.run_polling()

if __name__ == "__main__":
    main()