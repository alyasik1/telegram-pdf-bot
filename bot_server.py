import os
import logging
import tempfile
import asyncio

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler

from pdfminer.high_level import extract_text
from PyPDF2 import PdfReader

# --- ЛОГИ ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- TELEGRAM TOKEN ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # например: https://your-app.up.railway.app/webhook

# --- FASTAPI ---
app = FastAPI()

# --- TELEGRAM APP ---
telegram_app = Application.builder().token(BOT_TOKEN).build()


# --- КНОПКИ ---
def main_menu():
    keyboard = [
        [InlineKeyboardButton("📄 Конвертировать PDF → TXT", callback_data="convert_txt")],
        [InlineKeyboardButton("🔍 OCR (распознать текст)", callback_data="convert_ocr")],
        [InlineKeyboardButton("✂️ Разделить PDF", callback_data="split_pdf")],
    ]
    return InlineKeyboardMarkup(keyboard)


# --- ОБРАБОТЧИКИ ---
async def start(update: Update, context):
    await update.message.reply_text(
        "👋 Привет! Я помогу работать с PDF.\n\n"
        "Загрузи PDF и выбери, что сделать:",
        reply_markup=main_menu()
    )


async def handle_file(update: Update, context):
    file = await update.message.document.get_file()
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        await file.download_to_drive(custom_path=tmp.name)
        context.user_data["pdf_path"] = tmp.name

    await update.message.reply_text(
        "📥 Файл получен! Теперь выбери действие:",
        reply_markup=main_menu()
    )


async def button_handler(update: Update, context):
    query = update.callback_query
    await query.answer()

    pdf_path = context.user_data.get("pdf_path")
    if not pdf_path:
        await query.edit_message_text("❌ Сначала загрузи PDF-файл.")
        return

    if query.data == "convert_txt":
        await query.edit_message_text("🔄 Конвертирую PDF в текст...")
        text = extract_text(pdf_path)
        if not text.strip():
            await query.edit_message_text("⚠️ Не удалось извлечь текст (попробуй OCR).")
        else:
            if len(text) > 4000:
                text = text[:4000] + "\n\n... ✂️ Текст обрезан."
            await query.edit_message_text("✅ Готово! Вот текст:\n\n" + text)

    elif query.data == "convert_ocr":
        await query.edit_message_text("🔍 OCR пока не подключён (Tesseract нужен).")

    elif query.data == "split_pdf":
        reader = PdfReader(pdf_path)
        pages = len(reader.pages)
        await query.edit_message_text(f"📑 В файле {pages} страниц. Функция разделения пока в разработке.")


# --- FASTAPI ROUTES ---
@app.post("/webhook")
async def telegram_webhook(request: Request):
    data = await request.json()
    update = Update.de_json(data, telegram_app.bot)
    await telegram_app.process_update(update)
    return JSONResponse({"ok": True})


@app.on_event("startup")
async def on_startup():
    await telegram_app.bot.set_webhook(f"{WEBHOOK_URL}/webhook")
    telegram_app.add_handler(CommandHandler("start", start))
    telegram_app.add_handler(MessageHandler(filters.Document.PDF, handle_file))
    telegram_app.add_handler(CallbackQueryHandler(button_handler))


@app.get("/")
async def home():
    return {"status": "ok", "message": "PDF Bot is running 🚀"}
