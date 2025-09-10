import os
import logging
from fastapi import FastAPI, Request
from telegram import Update, Bot
from telegram.ext import Dispatcher, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from pdf_converter import convert_pdf_to_text
from keyboards import main_keyboard

# Переменные окружения
TOKEN = os.getenv("TOKEN")
PORT = int(os.getenv("PORT", 8000))

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация бота и FastAPI
bot = Bot(token=TOKEN)
app = FastAPI()
dp = Dispatcher(bot, update_queue=None, workers=4, use_context=True)

# Обработчики команд
def start(update, context):
    update.message.reply_text(
        "Привет! Я PDF конвертер. Выберите действие ниже:",
        reply_markup=main_keyboard()
    )

def help_command(update, context):
    update.message.reply_text(
        "Отправьте PDF-файл, и я конвертирую его в текстовый файл (.txt) и верну вам."
    )

def status(update, context):
    update.message.reply_text("Сервер работает нормально.")

# Обработчик инлайн-кнопок
def button_handler(update, context):
    query = update.callback_query
    query.answer()
    if query.data == "send_pdf":
        query.message.reply_text("Пожалуйста, отправьте PDF-файл.")
    elif query.data == "help":
        query.message.reply_text(
            "Отправьте PDF-файл, и я конвертирую его в текстовый файл (.txt) и верну вам."
        )

# Обработчик PDF
def pdf_handler(update, context):
    document = update.message.document
    if not document.file_name.lower().endswith(".pdf"):
        update.message.reply_text("Пожалуйста, отправьте файл в формате PDF.")
        return

    if document.file_size > 100*1024*1024:
        update.message.reply_text("Файл слишком большой (макс. 100 МБ).")
        return

    update.message.reply_text("Файл получен, начинаю конвертацию…")
    file = bot.get_file(document.file_id)
    pdf_path = f"/tmp/{document.file_name}"
    file.download(pdf_path)
    
    try:
        txt_path = convert_pdf_to_text(pdf_path)
        with open(txt_path, "rb") as f:
            update.message.reply_document(f)
        update.message.reply_text("Конвертация завершена. Вот ваш файл.")
    except Exception as e:
        logger.error(f"Ошибка при конвертации: {e}")
        update.message.reply_text("Произошла ошибка при конвертации файла.")
    finally:
        # Очистка временных файлов
        if os.path.exists(pdf_path):
            os.remove(pdf_path)
        if os.path.exists(txt_path):
            os.remove(txt_path)

# Регистрация обработчиков
dp.add_handler(CommandHandler("start", start))
dp.add_handler(CommandHandler("help", help_command))
dp.add_handler(CommandHandler("status", status))
dp.add_handler(CallbackQueryHandler(button_handler))
dp.add_handler(MessageHandler(filters.Document.ALL, pdf_handler))

# Webhook endpoint
@app.post(f"/{TOKEN}")
async def telegram_webhook(request: Request):
    update = Update.de_json(await request.json(), bot)
    dp.process_update(update)
    return {"ok": True}

# Запуск бота на Railway
if __name__ == "__main__":
    import uvicorn
    WEBHOOK_URL = f"https://telegram-pdf-bot-production-debc.up.railway.app/{TOKEN}"
    bot.set_webhook(WEBHOOK_URL)
    uvicorn.run(app, host="0.0.0.0", port=PORT)
