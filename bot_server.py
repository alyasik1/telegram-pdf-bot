import os
elif query.data == 'convert':
await query.edit_message_text('🔄 Отправьте PDF для конвертации в текст.')
elif query.data == 'ocr':
await query.edit_message_text('🔍 OCR выбран. Пришлите PDF.')


async def pdf_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
file = update.message.document
if not file:
await update.message.reply_text('❌ Файл не найден.')
return


if file.file_size > 200 * 1024 * 1024:
await update.message.reply_text('⚠️ Файл слишком большой (макс 200 МБ).')
return


await update.message.reply_text('📥 Загружаю файл...')
file_obj = await context.bot.get_file(file.file_id)
file_bytes = BytesIO()
await file_obj.download_to_memory(out=file_bytes)
file_bytes.seek(0)


await update.message.reply_text('🔄 Конвертирую PDF в текст...')
try:
reader = PdfReader(file_bytes)
text_content = '\n'.join(page.extract_text() or '' for page in reader.pages)
if not text_content.strip():
text_content = 'Файл пустой или текст не найден.'


await update.message.reply_text('✅ Готово! Вот текст:')
for i in range(0, len(text_content), 4000): # Telegram лимит 4096
await update.message.reply_text(text_content[i:i+4000])


except Exception as e:
logger.error(f"Ошибка при обработке PDF: {e}")
await update.message.reply_text(f'❌ Ошибка при обработке PDF: {e}')


# Handlers
telegram_app.add_handler(CommandHandler('start', start))
telegram_app.add_handler(CallbackQueryHandler(handle_button))
telegram_app.add_handler(MessageHandler(filters.Document.PDF, pdf_handler))


# FastAPI webhook route
@app.post('/webhook')
async def webhook(request: Request):
try:
update = Update.de_json(await request.json(), telegram_app.bot)
await telegram_app.update_queue.put(update)
return {'status': 'ok'}
except Exception as e:
logger.error(f"❌ Ошибка при обработке webhook: {e}")
return {'status': 'error', 'error': str(e)}


@app.on_event("startup")
async def on_startup():
logger.info("🚀 Устанавливаю webhook...")
await telegram_app.bot.set_webhook(WEBHOOK_URL)


@app.on_event("shutdown")
async def on_shutdown():
await telegram_app.stop()