import os
import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from contextlib import asynccontextmanager

# Логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Переменные окружения
BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # например: https://your-app.up.railway.app

if not BOT_TOKEN or not WEBHOOK_URL:
    raise RuntimeError("❌ BOT_TOKEN и WEBHOOK_URL должны быть заданы в Railway Variables")

# Создаём приложение Telegram
telegram_app = Application.builder().token(BOT_TOKEN).build()

# --- Handlers ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Привет! Отправь мне PDF, и я конвертирую его в текст.")

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    doc = update.message.document
    if not doc.file_name.endswith(".pdf"):
        await update.message.reply_text("❌ Пришли именно PDF-файл.")
        return

    await update.message.reply_text("📥 Загружаю файл...")

    file = await doc.get_file()
    file_path = f"/tmp/{doc.file_name}"
    await file.download_to_drive(file_path)

    await update.message.reply_text("✅ Файл загружен! (Здесь будет конвертация)")

# --- Роутинг для Telegram Webhook ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Устанавливаю webhook...")
    await telegram_app.bot.set_webhook(WEBHOOK_URL + "/webhook")
    yield
    logger.info("🛑 Удаляю webhook...")
    await telegram_app.bot.delete_webhook()

app = FastAPI(lifespan=lifespan)

@app.post("/webhook")
async def webhook_handler(request: Request):
    try:
        data = await request.json()
        update = Update.de_json(data, telegram_app.bot)
        await telegram_app.process_update(update)
    except Exception as e:
        logger.error(f"❌ Ошибка при обработке webhook: {e}")
        return JSONResponse(content={"ok": False}, status_code=500)
    return JSONResponse(content={"ok": True})

@app.get("/")
async def root():
    return {"status": "бот работает 🚀"}

# --- Регистрация хендлеров ---
telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(MessageHandler(filters.Document.PDF, handle_document))
