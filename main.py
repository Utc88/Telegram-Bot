from handlers import *  # تأكد من وجود handlers.py في نفس المجلد
from telegram.ext import Application, CommandHandler, MessageHandler, filters
import logging
import os
import socket

TOKEN = os.environ.get("BOT_TOKEN")

def main():
    try:
        lock_socket = socket.socket()
        lock_socket.bind(("localhost", 65432))
    except socket.error:
        logging.error("⚡ البوت يعمل بالفعل!")
        return
    
    application = Application.builder().token(TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_commands))
    
    logging.info("✅ البوت يعمل الآن!")
    application.run_polling()

if __name__ == "__main__":
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )
    main()
