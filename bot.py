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

if not TOKEN or not GROQ_KEY:
    raise Exception("❌ Missing TELEGRAM_TOKEN or GROQ_API_KEY")

# ================= GROQ =================
client = Groq(api_key=GROQ_KEY)

def ask_ai(prompt):
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "Ты помощник по работе, обучению и резюме."},
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
        "🚀 Каждый новый навык — это шаг к независимости.\n"
        "💡 Главное — не останавливаться!"
    )

def project_text():
    return (
        "🤖 AI-ментор проект\n\n"
        "Помогаю с:\n"
        "• резюме\n"
        "• обучением\n"
        "• карьерой\n"
        "• AI ответами"
    )

def training_text():
    return (
        "🎓 Обучение:\n\n"
        "1. Кратко\n"
        "2. Реальные навыки\n"
        "3. Опыт\n"
        "4. Результаты"
    )

# ================= START (FIXED) =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Добро пожаловать!\n\n🤖 AI-ментор готов помочь тебе 🚀",
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

    if text == "🎓 Обучение":
        await update.message.reply_text(training_text())
        return

    if text == "💼 Резюме":
        await update.message.reply_text(
            "📄 Отправь PDF резюме — я проверю 🤖"
        )
        return

    if text == "💬 Мотивация":
        await update.message.reply_text(get_motivation())
        return

    if text == "ℹ️ О проекте":
        await update.message.reply_text(project_text())
        return

    response = ask_ai(text)
    await update.message.reply_text(response)

# ================= PDF =================
async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    doc = update.message.document

    if not doc.file_name.endswith(".pdf"):
        await update.message.reply_text("❌ Только PDF файл")
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
        await update.message.reply_text("❌ Ошибка PDF")
        return

    if not text.strip():
        await update.message.reply_text("❌ PDF пуст")
        return

    await update.message.reply_text("🤖 Анализирую...")

    result = check_resume(text)
    await update.message.reply_text(result)

    os.remove(path)

# ================= MAIN =================
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_file))

    print("Bot running...")
    app.run_polling()

if __name__ == "__main__":
    main()