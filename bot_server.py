import os
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from pdf_to_text import convert_pdf_to_txt

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Приветствие с красивыми кнопками
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Конвертировать PDF", callback_data="convert")],
        [InlineKeyboardButton("Помощь", callback_data="help")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Привет! Я бот, который конвертирует PDF в текст. Выберите действие ниже 👇",
        reply_markup=reply_markup
    )

# Обработка кнопок
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "convert":
        await query.edit_message_text("Отправьте PDF-файл для конвертации.")
    elif query.data == "help":
        await query.edit_message_text("Просто отправьте PDF-файл, и я конвертирую его в текст.")

# Обработка PDF
async def handle_pdf(update: Update, context: ContextTypes.DEFAULT_TYPE):
    doc = update.message.document
    file_id = doc.file_id
    file_name = doc.file_name
    file_size = doc.file_size

    file_path = os.path.join(UPLOAD_FOLDER, file_name)
    file = await context.bot.get_file(file_id)
    await file.download_to_drive(file_path)

    # Ответим пользователю сразу
    await update.message.reply_text(f"Файл {file_name} принят. Конвертация запущена...")

    # Фоновая задача
    asyncio.create_task(convert_and_send(file_path, update, context))

# Асинхронная конвертация и отправка
async def convert_and_send(file_path: str, update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        output_txt = os.path.splitext(file_path)[0] + ".txt"
        convert_pdf_to_txt(file_path, output_txt)

        # Проверяем размер
        if os.path.getsize(output_txt) <= 50 * 1024 * 1024:
            await context.bot.send_document(chat_id=update.effective_chat.id, document=open(output_txt, "rb"))
        else:
            # Генерируем ссылку для скачивания (FastAPI)
            file_url = f"{os.getenv('DOMAIN', 'http://localhost:8000')}/files/{os.path.basename(output_txt)}"
            await update.message.reply_text(f"Файл слишком большой для Telegram (>50МБ).\nСкачайте здесь: {file_url}")

    except Exception as e:
        await update.message.reply_text(f"Ошибка конвертации: {e}")

# FastAPI сервер для отдачи файлов
from fastapi import FastAPI
from fastapi.responses import FileResponse

app = FastAPI()

@app.get("/files/{filename}")
async def get_file(filename: str):
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    if os.path.exists(file_path):
        return FileResponse(file_path, filename=filename)
    return {"error": "Файл не найден"}

# Основная функция запуска
def main():
    if not TELEGRAM_TOKEN:
        print("[ERROR] Установите TELEGRAM_TOKEN")
        return

    tg_app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    tg_app.add_handler(CommandHandler("start", start))
    tg_app.add_handler(MessageHandler(filters.Document.PDF, handle_pdf))
    tg_app.add_handler(MessageHandler(filters.Regex("convert|help"), button_handler))

    # Запуск Telegram бота и FastAPI вместе
    import uvicorn
    asyncio.create_task(uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000))))
    tg_app.run_polling()

if __name__ == "__main__":
    main()
