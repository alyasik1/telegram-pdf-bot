import os
import logging
from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)
from pdf_converter import convert_pdf_to_text
from keyboards import main_keyboard

# Переменные окружения
TOKEN = os.getenv("TOKEN")
PORT = int(os.getenv("PORT", 8000))

# Логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI приложение
app = FastAPI()

# ----- Обработчики команд -----
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Я PDF конвертер. Выберите действие ниже:",
        reply_markup=main_keyboard()
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Отправьте PDF-файл, и я конвертирую его в текстовый файл (.txt) и верну вам."
    )

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Сервер работает нормально.")

# ----- Обработчик инлайн-кнопок -----
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "send_pdf":
        await query.message.reply_text("Пожалуйста, отправьте PDF-файл.")
    elif query.data == "help":
        await query.message.reply_text(
            "Отправьте PDF-файл, и я конвертирую его в текстовый файл (.txt) и верну вам."
        )

# ----- Обработчик PDF -----
async def pdf_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    document = update.message.document
    if not document.file_name.lower().endswith(".pdf"):
        await update.message.reply_text("Пожалуйста, отправьте файл в формате PDF.")
        return

    if document.file_size > 100*1024*1024:
        await update.message.reply_text("Файл слишком большой (макс. 100 МБ).")
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
        # Очистка временных файлов
        if os.path.exists(pdf_path):
            os.remove(pdf_path)
        if os.path.exists(txt_path):
            os.remove(txt_path)

# ----- Создаем приложение Telegram -----
application = ApplicationBuilder().token(TOKEN).build()

# Регистрируем обработчики
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("help", help_command))
application.add_handler(CommandHandler("status", status))
application.add_handler(CallbackQueryHandler(button_handler))
application.add_handler(MessageHandler(filters.Document.ALL, pdf_handler))

# ----- FastAPI webhook endpoint -----
@app.post(f"/{TOKEN}")
async def telegram_webhook(request: Request):
    data = await request.json()
    update = Update.de_json(data, application.bot)
    await application.update_queue.put(update)
    return {"ok": True}

# ----- Запуск сервера -----
if __name__ == "__main__":
    import uvicorn
    WEBHOOK_URL = f"https://telegram-pdf-bot-production-debc.up.railway.app/{TOKEN}"
    import asyncio
    asyncio.run(application.bot.set_webhook(WEBHOOK_URL))
    uvicorn.run(app, host="0.0.0.0", port=PORT)
