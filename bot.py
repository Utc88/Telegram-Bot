from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import logging
import time

TOKEN = "YOUR_BOT_TOKEN"
GROUP_ID = -1002607695043  # آيدي القروب
ADMIN_ID = 6651872224  # آيدي حسابك

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("مرحبا! البوت يعمل عبر GitHub 🚀")

async def send_to_group(context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=GROUP_ID,
        text="📢 إشعار تلقائي من البوت!"
    )

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.error(f"Error: {context.error}")
    await context.bot.send_message(ADMIN_ID, f"⚠️ خطأ في البوت: {context.error}")

def main():
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_error_handler(error_handler)

    # إرسال إشعار كل ساعة
    job_queue = application.job_queue
    job_queue.run_repeating(send_to_group, interval=3600, first=10)

    application.run_polling()

if __name__ == "__main__":
    while True:
        try:
            main()
        except Exception as e:
            logging.error(f"Restarting bot due to: {e}")
            time.sleep(10)
