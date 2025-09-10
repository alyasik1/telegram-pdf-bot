import os
import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
)
from contextlib import asynccontextmanager
from pdfminer.high_level import extract_text
from PyPDF2 import PdfReader
from pdf2image import convert_from_path
import pytesseract
import asyncio

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # Например: https://your-app.up.railway.app

if not BOT_TOKEN or not WEBHOOK_URL:
    raise RuntimeError("BOT_TOKEN и WEBHOOK_URL должны быть заданы")

telegram_app = Application.builder().token(BOT_TOKEN).build()

# --- Стартовое приветствие ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📥 Загрузить PDF", callback_data="upload_pdf")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "👋 Привет! Я бот для конвертации PDF.\n"
        "Нажми кнопку ниже, чтобы начать:",
        reply_markup=reply_markup
    )

# --- Обработка PDF ---
async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    doc = update.message.document
    if not doc.file_name.endswith(".pdf"):
        await update.message.reply_text("❌ Пожалуйста, отправьте PDF-файл.")
        return

    await update.message.reply_text("📥 Загружаю файл...")
    file = await doc.get_file()
    file_path = f"/tmp/{doc.file_name}"
    await file.download_to_drive(file_path)

    keyboard = [
        [InlineKeyboardButton("📄 Скачать TXT", callback_data=f"to_txt|{file_path}")],
        [InlineKeyboardButton("🔍 OCR", callback_data=f"ocr|{file_path}")],
        [InlineKeyboardButton("✂ Разбить PDF", callback_data=f"split|{file_path}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("✅ Файл загружен! Выберите действие:", reply_markup=reply_markup)

# --- Кнопки ---
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    action, file_path = query.data.split("|", maxsplit=1)

    if action == "to_txt":
        await query.edit_message_text("🔄 Конвертирую PDF в текст...")
        text = extract_text(file_path)
        txt_path = file_path.replace(".pdf", ".txt")
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(text)
        await query.edit_message_text(f"✅ TXT готов! Файл: {txt_path}")
    elif action == "ocr":
        await query.edit_message_text("🔍 Распознаю текст через OCR...")
        images = convert_from_path(file_path)
        text = ""
        for img in images:
            text += pytesseract.image_to_string(img)
        txt_path = file_path.replace(".pdf", "_ocr.txt")
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(text)
        await query.edit_message_text(f"✅ OCR завершён! Файл: {txt_path}")
    elif action == "split":
        await query.edit_message_text("✂ Разбиваю PDF...")
        reader = PdfReader(file_path)
        for i, page in enumerate(reader.pages):
            writer = PdfReader()
            writer.add_page(page)
            split_path = file_path.replace(".pdf", f"_page_{i+1}.pdf")
            with open(split_path, "wb") as f:
                writer.write(f)
        await query.edit_message_text("✅ PDF разбит!")

# --- Webhook для FastAPI ---
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
telegram_app.add_handler(CallbackQueryHandler(button_callback))
