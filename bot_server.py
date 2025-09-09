import os
import asyncio
from fastapi import FastAPI, Response
from fastapi.responses import FileResponse
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
from pdf_to_text import pdf_to_txt

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
DOMAIN = os.getenv("DOMAIN", "http://localhost:8000")

if not TELEGRAM_TOKEN:
    raise ValueError("Set TELEGRAM_TOKEN env var")

# FastAPI для отдачи больших файлов
app = FastAPI()
FILES_DIR = "converted_files"
os.makedirs(FILES_DIR, exist_ok=True)

@app.get("/files/{filename}")
async def serve_file(filename: str):
    path = os.path.join(FILES_DIR, filename)
    if os.path.exists(path):
        return FileResponse(path, filename=filename)
    return Response("File not found", status_code=404)

# Telegram bot
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Приветствие с кнопками"""
    keyboard = [
        [InlineKeyboardButton("Конвертировать PDF", callback_data="convert_pdf")],
        [InlineKeyboardButton("Помощь", callback_data="help")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Привет! Я PDF-конвертер.\nВыберите действие кнопкой ниже.",
        reply_markup=reply_markup
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "convert_pdf":
        await query.edit_message_text("Отправьте PDF-файл, который нужно конвертировать.")
    elif query.data == "help":
        await query.edit_message_text("Просто отправьте PDF-файл, и я верну текстовый файл.")

async def handle_pdf(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file = await context.bot.get_file(update.message.document.file_id)
    file_name = update.message.document.file_name
    local_path = os.path.join(FILES_DIR, file_name)
    await file.download_to_drive(local_path)

    # Если файл >50 МБ → просим оплату (пока закомментировано)
    # if update.message.document.file_size > 50*1024*1024:
    #     await update.message.reply_text("Файл слишком большой. Пожалуйста, оплатите через ЮKassa.")
    #     return

    output_file = os.path.join(FILES_DIR, file_name.rsplit(".",1)[0]+".txt")
    await update.message.reply_text("Начинаю конвертацию...")
    loop = asyncio.get_running_loop()
    success = await loop.run_in_executor(None, pdf_to_txt, local_path, output_file)
    if success:
        if os.path.getsize(output_file) > 50*1024*1024:
            # Для больших файлов даём ссылку
            await update.message.reply_text(f"Файл слишком большой для отправки напрямую. Скачайте по ссылке:\n{DOMAIN}/files/{os.path.basename(output_file)}")
        else:
            await update.message.reply_document(document=open(output_file, "rb"))
    else:
        await update.message.reply_text("Ошибка при конвертации PDF.")

async def main():
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.Document.PDF, handle_pdf))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), start))
    application.add_handler(MessageHandler(filters.ALL, start))
    application.add_handler(MessageHandler(filters.COMMAND, start))
    application.add_handler(MessageHandler(filters.ALL, start))
    # Callback кнопки
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), start))
    application.add_handler(MessageHandler(filters.ALL, start))
    application.add_handler(MessageHandler(filters.ALL, start))
    application.add_handler(MessageHandler(filters.ALL, start))
    application.add_handler(MessageHandler(filters.ALL, start))
    application.add_handler(MessageHandler(filters.ALL, start))
    application.add_handler(MessageHandler(filters.ALL, start))
    application.add_handler(MessageHandler(filters.ALL, start))
    application.add_handler(MessageHandler(filters.ALL, start))
    application.add_handler(MessageHandler(filters.ALL, start))
    application.add_handler(MessageHandler(filters.ALL, start))
    # Inline кнопки
    from telegram.ext import CallbackQueryHandler
    application.add_handler(CallbackQueryHandler(button_handler))

    await application.initialize()
    await application.start()
    print("Telegram bot started")
    await application.updater.start_polling()
    await application.updater.idle()

# Для запуска через uvicorn
if __name__ == "__main__":
    import uvicorn
    import threading
    # Запуск FastAPI в отдельном потоке
    threading.Thread(target=lambda: uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))).start()
    asyncio.run(main())
