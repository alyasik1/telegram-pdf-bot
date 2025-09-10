import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
import pdfplumber

# Переменные окружения
TOKEN = os.getenv("TOKEN")

# Логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ----- Конвертация PDF в текст -----
def convert_pdf_to_text(pdf_path):
    txt_path = pdf_path.replace(".pdf", ".txt")
    with pdfplumber.open(pdf_path) as pdf:
        text = ""
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    with open(txt_path, 'w', encoding='utf-8') as f:
        f.write(text)
    return txt_path

# ----- Клавиатура -----
def main_keyboard():
    keyboard = [
        [InlineKeyboardButton("Отправить PDF", callback_data="send_pdf")],
        [InlineKeyboardButton("Помощь", callback_data="help")]
    ]
    return InlineKeyboardMarkup(keyboard)

# ----- Обработчики -----
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Я PDF конвертер. Выберите действие ниже:",
        reply_markup=main_keyboard()
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Отправьте PDF-файл, и я конвертирую его в текстовый файл (.txt) и верну вам."
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "send_pdf":
        await query.message.reply_text("Пожалуйста, отправьте PDF-файл.")
    elif query.data == "help":
        await query.message.reply_text("Отправьте PDF-файл, и я конвертирую его в текстовый файл (.txt).")

async def pdf_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    document = update.message.document
    if not document.file_name.lower().endswith(".pdf"):
        await update.message.reply_text("Пожалуйста, отправьте файл в формате PDF.")
        return

    if document.file_size > 50*1024*1024:
        await update.message.reply_text("Файл слишком большой (макс. 50 МБ).")
        return

    await update.message.reply_text("Файл получен, начинаю конвертацию…")
    file = await context.bot.get_file(document.file_id)
    pdf_path = f"/tmp/{document.file_name}"
    await file.download_to_drive(pdf_path)

    try:
        txt_path = convert_pdf_to_text(pdf_path)
        with open(txt_path, "rb") as f:
            await update.message.reply_document(f)
        await update.message.reply_text("Конвертация завершена. Вот ваш файл.")
    except Exception as e:
        logger.error(f"Ошибка при конвертации: {e}")
        await update.message.reply_text("Произошла ошибка при конвертации файла.")
    finally:
        if os.path.exists(pdf_path):
            os.remove(pdf_path)
        if os.path.exists(txt_path):
            os.remove(txt_path)

# ----- Создание приложения -----
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("help", help_command))
app.add_handler(CallbackQueryHandler(button_handler))
app.add_handler(MessageHandler(filters.Document.ALL, pdf_handler))

# ----- Запуск -----
if __name__ == "__main__":
    app.run_polling()
