from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
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
import socket
from datetime import datetime

# ======================
#  إعدادات التكوين الأساسية
# ======================
TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = int(os.environ.get("ADMIN_ID", 0))
ATTACK_PROFILES = {
    '🚀 سريع': {'delay': 0.3},
    '⚡ متوسط': {'delay': 1.5},
    '🐢 بطيء': {'delay': 3}
}

# ======================
#  المتغيرات العامة
# ======================
active_sessions = {}
user_settings = {}
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# ======================
#  لوحة التحكم التفاعلية (تم تحديثها)
# ======================
control_panel = ReplyKeyboardMarkup(
    [
        ["🚀 بدء الهجوم", "🛑 إيقاف الهجوم"],
        ["✏️ تعديل الرسالة", "📊 الإحصائيات"],
        ["🔙 العودة للخلف"]  # <-- تمت إضافة زر العودة هنا
    ],
    resize_keyboard=True,
    is_persistent=True
)

# ======================
#  الدوال الرئيسية (تم تحديثها)
# ======================
async def handle_commands(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة الأوامر مع دعم زر العودة"""
    text = update.message.text
    user = update.effective_user
    
    if text == "🔙 العودة للخلف":
        await show_main_menu(update)
        return
        
    if text == "🚀 بدء الهجوم":
        await start_attack_flow(update, context)
    elif text == "🛑 إيقاف الهجوم":
        await stop_attack(update, context)
    elif text == "✏️ تعديل الرسالة":
        await request_custom_message(update)
    elif text == "📊 الإحصائيات":
        await show_stats(update)

async def show_main_menu(update: Update):
    """عرض القائمة الرئيسية مع زر العودة"""
    await update.message.reply_text(
        "القائمة الرئيسية:",
        reply_markup=control_panel
    )

# ======================
#  نظام الهجوم (تم تصحيح الخطأ النحوي)
# ======================
async def execute_attack(update: Update, context: ContextTypes.DEFAULT_TYPE, speed: str):
    user = update.effective_user
    config = ATTACK_PROFILES[speed]
    
    job = context.application.job_queue.run_repeating(  # <-- التصحيح هنا
        callback=attack_callback,
        interval=config['delay'],
        first=0,
        data={
            'user_id': user.id,
            'message': user_settings[user.id]['custom_message']
        },
        name=str(user.id)
    )
    
    active_sessions[user.id] = {
        'job': job,
        'start_time': datetime.now(),
        'count': 0
    }
    
    await update.message.reply_text(
        f"⚡ الهجوم النشط: {speed}",
        reply_markup=control_panel
    )

# ======================
#  باقي الدوال بدون تغيير
# ======================
# ... (أبقيت باقي الدوال كما هي في الإصدار السابق)

# ======================
#  التهيئة والتشغيل
# ======================
def main():
    try:
        lock_socket = socket.socket()
        lock_socket.bind(("localhost", 65432))
    except socket.error:
        logging.error("⚡ البوت يعمل بالفعل!")
        return

    application = Application.builder().token(TOKEN).build()
    
    handlers = [
        CommandHandler("start", start),
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_commands),
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_custom_message)
    ]
    
    for handler in handlers:
        application.add_handler(handler)
    
    application.add_error_handler(error_handler)
    
    logging.info("✅ البوت يعمل الآن!")
    application.run_polling()

if __name__ == "__main__":
    main()
