from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    CallbackContext,
)
import logging
import os

# إعدادات البوت
TOKEN = os.environ.get("BOT_TOKEN")
GROUP_ID = int(os.environ.get("GROUP_ID"))
ADMIN_ID = int(os.environ.get("ADMIN_ID"))

# لوحة المفاتيح التفاعلية
KEYBOARD = ReplyKeyboardMarkup(
    [
        ["تشغيل الهجوم 🚀", "إيقاف الهجوم 🛑"],
        ["تغيير السرعة ⚡", "القائمة الرئيسية 🏠"],
    ],
    resize_keyboard=True,
    is_persistent=True,  # إظهار اللوحة بشكل دائم
    selective=True  # إظهارها للمستخدمين المحددين
)

# تهيئة النظام
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """الدالة المسؤولة عن بدء المحادثة"""
    user = update.effective_user
    
    # إرسال الرسالة مع اللوحة
    await update.message.reply_text(
        f"مرحبا {user.first_name}! 👾\nاختر أحد الأزرار:",
        reply_markup=KEYBOARD
    )
    
    # إرسال إشعار للقروب
    await context.bot.send_message(
        chat_id=GROUP_ID,
        text=f"👤 مستخدم جديد: @{user.username}"
    )

async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة جميع الرسائل الواردة"""
    text = update.message.text
    
    # إعادة إظهار اللوحة عند طلب القائمة
    if text == "القائمة الرئيسية 🏠":
        await start(update, context)
        return
    
    # إعادة إرسال اللوحة مع كل رسالة
    await update.message.reply_text(
        "✅ البوت يعمل، اختر من الأزرار:",
        reply_markup=KEYBOARD
    )

async def error_handler(update: Update, context: CallbackContext):
    """معالجة الأخطاء"""
    logging.error(f"حدث خطأ: {context.error}")
    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"⚠️ خطأ: {context.error}"
    )

def main():
    # تهيئة البوت
    application = Application.builder().token(TOKEN).build()
    
    # إضافة المعالجات
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.ALL, handle_messages))
    application.add_error_handler(error_handler)
    
    # بدء التشغيل
    application.run_polling()

if __name__ == "__main__":
    main()
