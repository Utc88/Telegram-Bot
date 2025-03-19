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
#  لوحة التحكم التفاعلية
# ======================
control_panel = ReplyKeyboardMarkup(
    [
        ["🚀 بدء الهجوم", "🛑 إيقاف الهجوم"],
        ["✏️ تعديل الرسالة", "📊 الإحصائيات"]
    ],
    resize_keyboard=True,
    is_persistent=True
)

# ======================
#  الدوال الرئيسية
# ======================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """بدء المحادثة وتجهيز الإعدادات"""
    user = update.effective_user
    user_id = user.id
    
    # تهيئة الإعدادات الافتراضية
    if user_id not in user_settings:
        user_settings[user_id] = {
            'custom_message': '.' * 100,
            'attack_count': 0
        }
    
    await update.message.reply_text(
        f"مرحبًا {user.first_name}! 👾\nاختر أحد الخيارات:",
        reply_markup=control_panel
    )

async def handle_commands(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة الأوامر من لوحة التحكم"""
    text = update.message.text
    user = update.effective_user
    
    if text == "🚀 بدء الهجوم":
        await start_attack_flow(update, context)
    elif text == "🛑 إيقاف الهجوم":
        await stop_attack(update, context)
    elif text == "✏️ تعديل الرسالة":
        await request_custom_message(update)
    elif text == "📊 الإحصائيات":
        await show_stats(update)

# ======================
#  نظام الهجوم
# ======================
async def start_attack_flow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """بدء تدفق اختيار السرعة"""
    speed_selector = ReplyKeyboardMarkup(
        [[speed] for speed in ATTACK_PROFILES.keys()],
        resize_keyboard=True
    )
    await update.message.reply_text("⚡ اختر سرعة الهجوم:", reply_markup=speed_selector)
    user_settings[update.effective_user.id]['awaiting_speed'] = True

async def execute_attack(update: Update, context: ContextTypes.DEFAULT_TYPE, speed: str):
    """تنفيذ الهجوم الفعلي"""
    user = update.effective_user
    config = ATTACK_PROFILES[speed]
    
    # إلغاء أي هجوم سابق
    if user.id in active_sessions:
        active_sessions[user.id]['job'].schedule_removal()
    
    # إنشاء مهمة جديدة
    job = context.application.job_queue.run_repeating(
        callback=attack_callback,
        interval=config['delay'],
        first=0,
        data={
            'user_id': user.id,
            'message': user_settings[user.id]['custom_message']
        },
        name=str(user.id)
    
    # تحديث السجلات
    active_sessions[user.id] = {
        'job': job,
        'start_time': datetime.now(),
        'count': 0
    }
    user_settings[user.id]['attack_count'] += 1
    
    await update.message.reply_text(
        f"⚔️ الهجوم النشط: {speed}\n"
        f"⏱ التكرار كل {config['delay']} ثانية\n"
        f"✉️ الرسالة: {user_settings[user.id]['custom_message'][:30]}...",
        reply_markup=control_panel
    )

async def attack_callback(context: CallbackContext):
    """الإرسال التلقائي للرسائل"""
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

# ======================
#  الدوال المساعدة
# ======================
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
        "📝 أرسل الرسالة الجديدة (سيتم تكرارها تلقائيًا):",
        reply_markup=ReplyKeyboardRemove()
    )
    user_settings[update.effective_user.id]['awaiting_input'] = True

async def handle_custom_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة الرسالة المخصصة"""
    user = update.effective_user
    if user_settings.get(user.id, {}).get('awaiting_input', False):
        new_message = update.message.text * 100  # تكرار 100 مرة
        user_settings[user.id]['custom_message'] = new_message
        user_settings[user.id]['awaiting_input'] = False
        await update.message.reply_text(
            f"✅ تم تعيين الرسالة:\n{new_message[:50]}...",
            reply_markup=control_panel
        )

async def show_stats(update: Update):
    """عرض إحصائيات المستخدم"""
    user = update.effective_user
    stats = user_settings.get(user.id, {})
    await update.message.reply_text(
        f"📈 إحصائياتك:\n"
        f"• عدد الهجمات: {stats.get('attack_count', 0)}\n"
        f"• آخر رسالة: {stats.get('custom_message', '')[:30]}..."
    )

async def notify_admin(context: CallbackContext, message: str):
    """إرسال إشعارات للمطور"""
    try:
        await context.bot.send_message(ADMIN_ID, message)
    except Exception as e:
        logging.error(f"فشل إرسال التنبيه: {str(e)}")

async def error_handler(update: Update, context: CallbackContext):
    """معالجة الأخطاء العامة"""
    error = context.error
    logging.error(f"حدث خطأ: {error}")
    await notify_admin(context, f"🚨 خطأ حرج: {str(error)[:200]}")

# ======================
#  التهيئة والتشغيل
# ======================
def main():
    # منع التشغيل المزدوج
    try:
        lock_socket = socket.socket()
        lock_socket.bind(("localhost", 65432))
    except socket.error:
        logging.error("⚡ البوت يعمل بالفعل!")
        return

    # بناء التطبيق
    application = Application.builder().token(TOKEN).build()
    
    # إضافة المعالجات
    handlers = [
        CommandHandler("start", start),
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_commands),
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_custom_message)
    ]
    
    for handler in handlers:
        application.add_handler(handler)
    
    application.add_error_handler(error_handler)
    
    # بدء التشغيل
    logging.info("✅ البوت يعمل الآن!")
    application.run_polling()

if __name__ == "__main__":
    main()
