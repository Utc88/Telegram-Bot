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

# ---------------------------
#  إعدادات البوت الأساسية
# ---------------------------
TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = int(os.environ.get("ADMIN_ID", 0))
ATTACK_PROFILES = {
    '🚀 سريع': {'delay': 0.3},
    '⚡ متوسط': {'delay': 1.5},
    '🐢 بطيء': {'delay': 3}
}

# ---------------------------
#  المتغيرات العامة
# ---------------------------
active_sessions = {}
user_settings = {}
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# ---------------------------
#  لوحات المفاتيح
# ---------------------------
main_keyboard = ReplyKeyboardMarkup(
    [
        ["🚀 بدء الهجوم", "🛑 إيقاف الهجوم"],
        ["✏️ تعديل الرسالة", "📊 الإحصائيات"],
        ["🔙 العودة للخلف"]
    ],
    resize_keyboard=True,
    is_persistent=True
)

speed_keyboard = ReplyKeyboardMarkup(
    [[speed] for speed in ATTACK_PROFILES.keys()],
    resize_keyboard=True
)

# ---------------------------
#  الدوال الأساسية
# ---------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    
    if user_id not in user_settings:
        user_settings[user_id] = {
            'custom_message': '.' * 100,
            'attack_count': 0
        }
    
    await update.message.reply_text(
        f"مرحبًا {user.first_name}! 👾\nاختر أحد الخيارات:",
        reply_markup=main_keyboard
    )

async def handle_commands(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
    await update.message.reply_text(
        "القائمة الرئيسية:",
        reply_markup=main_keyboard
    )

# ---------------------------
#  نظام الهجوم (تم التصحيح هنا)
# ---------------------------
async def start_attack_flow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "⚡ اختر سرعة الهجوم:",
        reply_markup=speed_keyboard
    )
    user_settings[update.effective_user.id]['awaiting_speed'] = True
async def execute_attack(update: Update, context: ContextTypes.DEFAULT_TYPE, speed: str):
    user = update.effective_user
    config = ATTACK_PROFILES[speed]
    
    if user.id in active_sessions:
        active_sessions[user.id]['job'].schedule_removal()
    
    # التصحيح: إضافة القوس المغلق بشكل صحيح
    job = context.application.job_queue.run_repeating(
        callback=attack_callback,
        interval=config['delay'],
        first=0,
        data={
            'user_id': user.id,
            'message': user_settings[user.id]['custom_message']
        },
        name=str(user.id)
    )  # <-- تم إصلاح الخطأ هنا
    
    active_sessions[user.id] = {
        'job': job,
        'start_time': datetime.now(),
        'count': 0
    }
    user_settings[user.id]['attack_count'] += 1
    
    await update.message.reply_text(
        f"⚡ تم تفعيل الهجوم ({speed}) \n"
        f"⏱ كل {config['delay']} ثانية",
        reply_markup=main_keyboard
    )

# ---------------------------
#  باقي الدوال
# ---------------------------
async def attack_callback(context: CallbackContext):
    try:
        job = context.job
        user_id = int(job.name)
        
        if user_id not in active_sessions:
            return
            
        await context.bot.send_message(
            chat_id=user_id,
            text=job.data['message']
        )
        
        active_sessions[user_id]['count'] += 1
        
        if active_sessions[user_id]['count'] % 5 == 0:
            logging.info(f"تم إرسال {active_sessions[user_id]['count']} رسائل")
            
    except Exception as e:
        logging.error(f"فشل الإرسال: {str(e)}")
        await notify_admin(context, f"🔥 خطأ: {str(e)[:200]}")

async def stop_attack(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in active_sessions:
        active_sessions[user_id]['job'].schedule_removal()
        del active_sessions[user_id]
        await update.message.reply_text("✅ تم إيقاف الهجوم!")
    else:
        await update.message.reply_text("⚠️ لا يوجد هجوم نشط!")

async def request_custom_message(update: Update):
    await update.message.reply_text(
        "📝 أرسل الرسالة الجديدة:",
        reply_markup=ReplyKeyboardRemove()
    )
    user_settings[update.effective_user.id]['awaiting_input'] = True

async def handle_custom_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user_settings.get(user.id, {}).get('awaiting_input'):
        new_message = update.message.text * 100
        user_settings[user.id]['custom_message'] = new_message
        user_settings[user.id]['awaiting_input'] = False
        await update.message.reply_text(
            f"✅ تم تعيين الرسالة:\n{new_message[:50]}...",
            reply_markup=main_keyboard
        )

async def show_stats(update: Update):
    user = update.effective_user
    stats = user_settings.get(user.id, {})
    await update.message.reply_text(
        f"📊 الإحصائيات:\n"
        f"• عدد الهجمات: {stats.get('attack_count', 0)}\n"
        f"• الرسائل المرسلة: {active_sessions.get(user.id, {}).get('count', 0)}"
    )

async def notify_admin(context: CallbackContext, message: str):
    try:
        await context.bot.send_message(ADMIN_ID, message)
    except Exception as e:
        logging.error(f"فشل إرسال التنبيه: {str(e)}")

async def error_handler(update: Update, context: CallbackContext):
    error = context.error
    logging.error(f"حدث خطأ: {error}")
    await notify_admin(context, f"🚨 خطأ حرج: {str(error)[:200]}")

# ---------------------------
#  التشغيل الرئيسي
# ---------------------------
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
