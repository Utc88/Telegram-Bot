from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    JobQueue,
    CallbackContext,
)
import logging
import os
import time
from datetime import datetime

# إعدادات البوت
TOKEN = os.environ.get("BOT_TOKEN")
GROUP_ID = int(os.environ.get("GROUP_ID"))
ADMIN_ID = int(os.environ.get("ADMIN_ID"))

# إعدادات الهجوم
ATTACK_PROFILES = {
    '🚀 سريع': {'delay': 0.3},
    '⚡ متوسط': {'delay': 1.5},
    '🐢 بطيء': {'delay': 3}
}

# تخزين الحالات
active_sessions = {}
user_settings = {}
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# لوحة التحكم الرئيسية
main_keyboard = ReplyKeyboardMarkup(
    [
        ["🚀 بدء الهجوم", "🛑 إيقاف الهجوم"],
        ["✏️ تعديل الرسالة", "🏠 القائمة الرئيسية"]
    ],
    resize_keyboard=True,
    is_persistent=True
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """بدء المحادثة وعرض اللوحة"""
    user = update.effective_user
    user_settings[user.id] = {'custom_message': '.' * 100}
    
    await update.message.reply_text(
        f"مرحبًا {user.first_name}! 👾\nاختر أحد الخيارات:",
        reply_markup=main_keyboard
    )
    
    await context.bot.send_message(
        GROUP_ID,
        f"🌟 مستخدم جديد: {user.mention_html()}",
        parse_mode='HTML'
    )

async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة جميع الرسائل"""
    text = update.message.text
    user = update.effective_user
    
    if text == "🏠 القائمة الرئيسية":
        await show_main_menu(update)
    elif text == "🚀 بدء الهجوم":
        await start_attack(update, context)
    elif text == "🛑 إيقاف الهجوم":
        await stop_attack(update, context)
    elif text == "✏️ تعديل الرسالة":
        await request_custom_message(update)
    else:
        if user_settings.get(user.id, {}).get('awaiting_input'):
            await set_custom_message(update, context)

async def show_main_menu(update: Update):
    """عرض القائمة الرئيسية"""
    await update.message.reply_text(
        "القائمة الرئيسية:",
        reply_markup=main_keyboard
    )

async def start_attack(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """بدء عملية الهجوم"""
    speed_keyboard = ReplyKeyboardMarkup(
        [[speed] for speed in ATTACK_PROFILES.keys()],
        resize_keyboard=True
    )
    await update.message.reply_text("⚡ اختر سرعة الهجوم:", reply_markup=speed_keyboard)
    user_settings[update.effective_user.id]['awaiting_speed'] = True

async def stop_attack(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إيقاف الهجوم الحالي"""
    user_id = update.effective_user.id
    if user_id in active_sessions:
        active_sessions[user_id]['job'].schedule_removal()
        del active_sessions[user_id]
        await update.message.reply_text("✅ تم إيقاف الهجوم!")
    else:
        await update.message.reply_text("⚠️ لا يوجد هجوم نشط!")

async def request_custom_message(update: Update):
    """طلب رسالة مخصصة من المستخدم"""
    await update.message.reply_text(
        "📝 أرسل الرسالة الجديدة (سيتم تكرارها):",
        reply_markup=ReplyKeyboardRemove()
    )
    user_settings[update.effective_user.id]['awaiting_input'] = True

async def set_custom_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """حفظ الرسالة المخصصة"""
    user = update.effective_user
    new_message = update.message.text * 100  # تكرار الرسالة 100 مرة
    user_settings[user.id]['custom_message'] = new_message
    user_settings[user.id]['awaiting_input'] = False
    
    await update.message.reply_text(
        f"✅ تم تعيين الرسالة:\n{new_message[:50]}...",
        reply_markup=main_keyboard
    )

async def attack_callback(context: CallbackContext):
    """إرسال الرسائل التلقائية"""
    job = context.job
    user_id = job.data['user_id']
    
    try:
        message = user_settings[user_id]['custom_message']
        await context.bot.send_message(user_id, message)
        active_sessions[user_id]['count'] += 1
    except Exception as e:
        logging.error(f"فشل الإرسال: {e}")
        await notify_admin(context, f"🚨 خطأ: {str(e)[:200]}")

async def handle_speed_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة اختيار السرعة"""
    user = update.effective_user
    if user_settings.get(user.id, {}).get('awaiting_speed'):
        speed = update.message.text
        if speed in ATTACK_PROFILES:
            delay = ATTACK_PROFILES[speed]['delay']
            job = context.application.job_queue.run_repeating(
                attack_callback,
                interval=delay,
                data={'user_id': user.id}
            )
            active_sessions[user.id] = {'job': job, 'count': 0}
            await update.message.reply_text(
                f"⚡ بدأ الهجوم بسرعة {speed}!",
                reply_markup=main_keyboard
            )
            user_settings[user.id]['awaiting_speed'] = False

async def notify_admin(context: CallbackContext, message: str):
    """إرسال إشعارات للمطور"""
    try:
        await context.bot.send_message(ADMIN_ID, message)
    except Exception as e:
        logging.error(f"فشل إرسال الإشعار: {e}")

async def error_handler(update: Update, context: CallbackContext):
    """معالجة الأخطاء العامة"""
    error = context.error
    logging.error(f"حدث خطأ: {error}")
    await notify_admin(context, f"🔥 خطأ حرج: {error}")

def main():
    """تهيئة وتشغيل البوت"""
    application = Application.builder().token(TOKEN).build()
    
    # إضافة المعالجات
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_messages))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_speed_selection))
    application.add_error_handler(error_handler)
    
    application.run_polling()

if __name__ == "__main__":
    main()
