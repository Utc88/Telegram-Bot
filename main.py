from telegram.ext import Application, CommandHandler, MessageHandler, filters
from handlers import *
import logging
import os
import socket

# ---------------------------
#  الإعدادات الأساسية
# ---------------------------
TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = int(os.environ.get("ADMIN_ID", 0))

def main():
    # منع التشغيل المزدوج
    try:
        lock_socket = socket.socket()
        lock_socket.bind(("localhost", 65432))
    except socket.error:
        logging.error("⚡ البوت يعمل بالفعل!")
        return
    
    # تهيئة التطبيق
    application = Application.builder().token(TOKEN).build()
    
    # تسجيل المعالجات
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_commands))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_custom_message))
    
    # بدء التشغيل
    logging.info("✅ البوت يعمل الآن!")
    application.run_polling()

if __name__ == "__main__":
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )
    main()
