from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    JobQueue,
)
import logging
import time
import os  # <-- إضافة هذه المكتبة

# الحصول على التوكن من المتغيرات البيئية
TOKEN = os.environ.get("BOT_TOKEN")  # <-- التعديل هنا
GROUP_ID = int(os.environ.get("GROUP_ID", -100123456789))
ADMIN_ID = int(os.environ.get("ADMIN_ID", 123456789))

# تهيئة نظام التسجيل
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 البوت يعمل بنجاح!")

async def send_notification(context: ContextTypes.DEFAULT_TYPE):
    try:
        await context.bot.send_message(
            chat_id=GROUP_ID,
            text="🔔 إشعار تلقائي من البوت!"
        )
    except Exception as e:
        logging.error(f"فشل الإرسال: {e}")

def main():
    # التحقق من وجود التوكن
    if not TOKEN:
        logging.error("❌ لم يتم تعيين BOT_TOKEN في البيئة!")
        return

    try:
        application = Application.builder().token(TOKEN).build()
        job_queue = application.job_queue
        
        job_queue.run_repeating(
            send_notification,
            interval=300,
            first=10
        )
        
        application.add_handler(CommandHandler("start", start))
        application.run_polling()
        
    except Exception as e:
        logging.error(f"خطأ رئيسي: {e}")

if __name__ == "__main__":
    while True:
        try:
            main()
        except Exception as e:
            logging.error(f"إعادة التشغيل بسبب: {e}")
            time.sleep(10)
