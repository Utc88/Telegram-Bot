from telegram import Update, ReplyKeyboardMarkup
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
import random
from datetime import datetime

# ██████╗  ██████╗ ████████╗
# ██╔══██╗██╔═══██╗╚══██╔══╝
# ██████╔╝██║   ██║   ██║   
# ██╔══██╗██║   ██║   ██║   
# ██████╔╝╚██████╔╝   ██║   
# ╚═════╝  ╚═════╝    ╚═╝   

# إعدادات البوت
TOKEN = os.environ.get("BOT_TOKEN")
GROUP_ID = int(os.environ.get("GROUP_ID"))
ADMIN_ID = int(os.environ.get("ADMIN_ID"))

# إعدادات الهجوم المتقدمة
ATTACK_PROFILES = {
    '🚀 سريع': {'delay': 0.3, 'messages': ["تستمر الضربة! 💥", "إزعاج مكثف! 🔥"]},
    '⚡ متوسط': {'delay': 1.5, 'messages': ["هجوم مستمر.. 🌪", "لا مفر! 🌀"]},
    '🐢 بطيء': {'delay': 3, 'messages': ["إستفزاز بطيء.. 🐌", "صبرك ينفد! ⏳"]}
}

# لوحة التحكم الذكية
CONTROL_PANEL = ReplyKeyboardMarkup(
    [
        ["🚀 بدء الهجوم", "🛑 إيقاف فوري"],
        ["⚙️ الإعدادات", "📊 الإحصائيات"],
        ["❓ المساعدة", "👤 دعم فني"]
    ],
    resize_keyboard=True,
    is_persistent=True,
    selective=True
)

# ███████╗███████╗██████╗ 
# ██╔════╝██╔════╝██╔══██╗
# █████╗  █████╗  ██████╔╝
# ██╔══╝  ██╔══╝  ██╔══██╗
# ██║     ███████╗██║  ██║
# ╚═╝     ╚══════╝╚═╝  ╚═╝

active_sessions = {}
user_stats = {}
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نظام التشغيل الذكي"""
    user = update.effective_user
    await show_control_panel(update, user)
    
    # تسجيل الإحصائيات
    user_stats[user.id] = {
        'first_seen': datetime.now(),
        'attack_count': 0
    }
    
    # إرسال تنبيه للقروب
    await context.bot.send_message(
        chat_id=GROUP_ID,
        text=f"🌟 دخول جديد:\n┌ {user.mention_html()}\n└ ID: {user.id}"
    )

async def show_control_panel(update: Update, user):
    """عرض لوحة التحكم التفاعلية"""
    welcome_msg = (
        f"مرحبًا {user.mention_html()}! 👾\n"
        "╔════════════════╗\n"
        "   نظام التحكم المتقدم\n"
        "╚════════════════╝"
    )
    
    await update.message.reply_html(
        welcome_msg,
        reply_markup=CONTROL_PANEL
    )

async def handle_commands(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نظام معالجة الأوامر الذكي"""
    text = update.message.text
    user = update.effective_user
    
    command_handlers = {
        "🚀 بدء الهجوم": start_attack_sequence,
        "🛑 إيقاف فوري": emergency_stop,
        "⚙️ الإعدادات": show_settings,
        "📊 الإحصائيات": show_statistics,
        "❓ المساعدة": show_help,
        "👤 دعم فني": tech_support
    }
    
    if text in command_handlers:
        await command_handlers[text](update, context, user)

# ██████╗ ██████╗ ███╗   ██╗████████╗███████╗
#██╔════╝██╔═══██╗████╗  ██║╚══██╔══╝██╔════╝
#██║     ██║   ██║██╔██╗ ██║   ██║   ███████╗
#██║     ██║   ██║██║╚██╗██║   ██║   ╚════██║
#╚██████╗╚██████╔╝██║ ╚████║   ██║   ███████║
# ╚═════╝ ╚═════╝ ╚═╝  ╚═══╝   ╚═╝   ╚══════╝

async def start_attack_sequence(update: Update, context: ContextTypes.DEFAULT_TYPE, user):
    """نظام الهجوم الذكي"""
    if user.id in active_sessions:
        await update.message.reply_text("⚠️ يوجد هجوم نشط بالفعل!")
        return
    
    # إنشاء قائمة سرعات هجوم ديناميكية
    speed_selector = ReplyKeyboardMarkup(
        [[speed] for speed in ATTACK_PROFILES.keys()],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    
    await update.message.reply_text(
        "⚡ اختر سرعة الهجوم:",
        reply_markup=speed_selector
    )
    
    # تعيين حالة الانتظار
    context.user_data['awaiting_speed'] = True

async def handle_attack_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة اختيار السرعة"""
    if context.user_data.get('awaiting_speed'):
        selected_speed = update.message.text
        if selected_speed in ATTACK_PROFILES:
            await execute_attack(update, context, selected_speed)
            context.user_data['awaiting_speed'] = False

async def execute_attack(update: Update, context: ContextTypes.DEFAULT_TYPE, speed):
    """تنفيذ الهجوم"""
    user = update.effective_user
    config = ATTACK_PROFILES[speed]
    
    job = context.application.job_queue.run_repeating(
        attack_callback,
        interval=config['delay'],
        first=1,
        data={
            'user_id': user.id,
            'speed': speed,
            'start_time': datetime.now()
        }
    )
    
    active_sessions[user.id] = {
        'job': job,
        'speed': speed,
        'message_count': 0
    }
    
    # تحديث الإحصائيات
    user_stats[user.id]['attack_count'] += 1
    
    await update.message.reply_text(
        f"⚔️ هجوم {speed} جاري التنفيذ!\n"
        f"⏱ المدة: {config['delay']} ثانية/رسالة"
    )

async def attack_callback(context: CallbackContext):
    """نظام إرسال الرسائل التلقائي"""
    job = context.job
    user_id = job.data['user_id']
    
    try:
        msg_pool = ATTACK_PROFILES[job.data['speed']]['messages']
        await context.bot.send_message(
            chat_id=user_id,
            text=random.choice(msg_pool)
        
        # تحديث الإحصائيات
        active_sessions[user_id]['message_count'] += 1
        
    except Exception as e:
        logging.error(f"فشل الهجوم: {e}")
        await notify_admin(context, f"🚨 فشل هجوم: {e}")

# ███████╗██╗  ██╗██████╗ 
# ██╔════╝╚██╗██╔╝██╔══██╗
# █████╗   ╚███╔╝ ██████╔╝
# ██╔══╝   ██╔██╗ ██╔═══╝ 
# ███████╗██╔╝ ██╗██║     
# ╚══════╝╚═╝  ╚═╝╚═╝     

async def emergency_stop(update: Update, context: ContextTypes.DEFAULT_TYPE, user):
    """الإيقاف الفوري الذكي"""
    if user.id not in active_sessions:
        await update.message.reply_text("🔇 لا يوجد هجوم نشط!")
        return
    
    active_sessions[user.id]['job'].schedule_removal()
    del active_sessions[user.id]
    
    duration = datetime.now() - user_stats[user.id].get('last_attack_start', datetime.now())
    await update.message.reply_text(
        f"✅ تم إيقاف الهجوم!\n"
        f"⏳ المدة الإجمالية: {duration.total_seconds():.1f} ثانية"
    )
    
    await notify_admin(context, f"🛑 إيقاف هجوم من: {user.mention_html()}")

async def show_settings(update: Update, context: ContextTypes.DEFAULT_TYPE, user):
    """لوحة الإعدادات المتقدمة"""
    settings_msg = (
        "⚙️ الإعدادات المتقدمة:\n"
        "▸ ضبط سرعات الهجوم\n"
        "▸ إدارة الإشعارات\n"
        "▸ تخصيص الرسائل\n"
        "▸ إعدادات الأمان"
    )
    await update.message.reply_text(settings_msg)

async def show_statistics(update: Update, context: ContextTypes.DEFAULT_TYPE, user):
    """نظام الإحصائيات التفصيلي"""
    stats = user_stats.get(user.id, {})
    msg = (
        f"📊 إحصائياتك:\n"
        f"▸ عدد الهجمات: {stats.get('attack_count', 0)}\n"
        f"▸ الرسائل المرسلة: {active_sessions.get(user.id, {}).get('message_count', 0)}\n"
        f"▸ أول استخدام: {stats.get('first_seen', 'غير معروف')}"
    )
    await update.message.reply_text(msg)

async def show_help(update: Update, context: ContextTypes.DEFAULT_TYPE, user):
    """نظام المساعدة التفاعلي"""
    help_msg = (
        "❔ دليل الاستخدام:\n"
        "▸ 🚀 بدء الهجوم: بدء إرسال الرسائل\n"
        "▸ 🛑 إيقاف فوري: وقف أي هجوم نشط\n"
        "▸ ⚙️ الإعدادات: ضبط خيارات متقدمة\n"
        "▸ 📊 الإحصائيات: عرض تفاصيل الاستخدام\n"
        "▸ 👤 دعم فني: التواصل مع المطور"
    )
    await update.message.reply_text(help_msg)

async def tech_support(update: Update, context: ContextTypes.DEFAULT_TYPE, user):
    """نظام الدعم الفني المباشر"""
    support_msg = (
        "👨💻 الدعم الفني:\n"
        "للإبلاغ عن مشاكل أو اقتراحات:\n"
        "▸ تواصل مع المطور: @YourTechSupport\n"
        "▸ الإصدار الحالي: 2.1.0\n"
        "▸ آخر تحديث: 2024-03-20"
    )
    await update.message.reply_text(support_msg)

# ███████╗██╗   ██╗███╗   ██╗ ██████╗ 
# ██╔════╝██║   ██║████╗  ██║██╔════╝ 
# █████╗  ██║   ██║██╔██╗ ██║██║  ███╗
# ██╔══╝  ██║   ██║██║╚██╗██║██║   ██║
# ██║     ╚██████╔╝██║ ╚████║╚██████╔╝
# ╚═╝      ╚═════╝ ╚═╝  ╚═══╝ ╚═════╝ 

async def notify_admin(context: CallbackContext, message: str):
    """نظام الإشعارات المتقدم"""
    try:
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=message,
            parse_mode='HTML'
        )
    except Exception as e:
        logging.error(f"فشل إرسال الإشعار: {e}")

async def error_handler(update: Update, context: CallbackContext):
    """نظام معالجة الأخطاء الذكي"""
    error = context.error
    logging.error(f"حدث خطأ: {error}")
    
    error_report = (
        "🚨 خطأ حرج:\n"
        f"▸ المستخدم: {update.effective_user.mention_html() if update else 'غير معروف'}\n"
        f"▸ التفاصيل: {str(error)[:200]}"
    )
    
    await notify_admin(context, error_report)

def main():
    """نظام التشغيل الرئيسي"""
    application = Application.builder().token(TOKEN).build()
    
    # إضافة المعالجات
    handlers = [
        CommandHandler('start', start),
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_commands),
        MessageHandler(filters.ALL, handle_attack_selection)
    ]
    
    for handler in handlers:
        application.add_handler(handler)
    
    application.add_error_handler(error_handler)
    application.run_polling()

if __name__ == "__main__":
    main()
