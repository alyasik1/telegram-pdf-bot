import os
import logging
import asyncio
from fastapi import FastAPI, Request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from telegram.ext import MessageHandler, filters

from dotenv import load_dotenv
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

app = FastAPI()
telegram_app = Application.builder().token(BOT_TOKEN).build()

MAX_FILE_SIZE = 200 * 1024 * 1024  # 200 MB

# ----------- Helper Functions -----------
def main_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("📄 Скачать TXT", callback_data="download_txt")],
        [InlineKeyboardButton("📝 OCR (скан)", callback_data="ocr")],
        [InlineKeyboardButton("✂️ Разделить PDF", callback_data="split_pdf")]
    ]
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Привет! Я PDF-бот. Загрузи PDF, и я конвертирую его в текст. "
        "Используй кнопки ниже для действий.",
        reply_markup=main_menu_keyboard()
    )

async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    document = update.message.document
    if not document:
        return

    if document.file_size > MAX_FILE_SIZE:
        await update.message.reply_text("❌ Файл слишком большой. Максимум 200 МБ.")
        return

    await update.message.reply_text("📥 Загружаю файл...")
    file = await document.get_file()
    file_path = f"./{document.file_name}"
    await file.download_to_drive(file_path)

    await update.message.reply_text("🔄 Конвертирую PDF в текст...")

    try:
        from pdfminer.high_level import extract_text
        text = extract_text(file_path)
        if not text.strip():
            text = "⚠️ PDF пустой или не содержит текста."
    except Exception as e:
        text = f"❌ Ошибка при обработке PDF: {e}"

    text_file_path = file_path.replace(".pdf", ".txt")
    with open(text_file_path, "w", encoding="utf-8") as f:
        f.write(text)

    await update.message.reply_text("✅ Конвертация завершена.", reply_markup=main_menu_keyboard())

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(f"Вы выбрали: {query.data}\n⚠️ Пока эта функция недоступна.")

# ----------- Telegram Handlers -----------
telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(MessageHandler(filters.Document.ALL, handle_file))
telegram_app.add_handler(CallbackQueryHandler(button_handler))

# ----------- FastAPI Webhook -----------
@app.on_event("startup")
async def on_startup():
    logger.info("🚀 Устанавливаю webhook...")
    await telegram_app.bot.set_webhook(WEBHOOK_URL)

@app.post("/webhook")
async def telegram_webhook(req: Request):
    try:
        update = Update.de_json(await req.json(), telegram_app.bot)
        await telegram_app.update_queue.put(update)
        return {"ok": True}
    except Exception as e:
        logger.error(f"❌ Ошибка при обработке webhook: {e}")
        return {"ok": False}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
