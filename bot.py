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

# إعدادات البوت
TOKEN = os.environ.get("BOT_TOKEN")
GROUP_ID = int(os.environ.get("GROUP_ID"))
ADMIN_ID = int(os.environ.get("ADMIN_ID"))

# إعدادات الهجوم
ATTACK_PROFILES = {
    '🚀 سريع': {'delay': 0.3, 'symbol': '.'},
    '⚡ متوسط': {'delay': 1.5, 'symbol': '.'},
    '🐢 بطيء': {'delay': 3, 'symbol': '.'}
}

# تخزين الرسائل المخصصة
custom_messages = {}

# لوحة التحكم
CONTROL_PANEL = ReplyKeyboardMarkup(
    [
        ["🚀 بدء الهجوم", "🛑 إيقاف فوري"],
        ["✏️ تعديل الرسالة", "⚙️ الإعدادات"],
        ["📊 الإحصائيات", "❓ المساعدة"]
    ],
    resize_keyboard=True,
    is_persistent=True
)

active_sessions = {}
user_stats = {}
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await show_control_panel(update, user)
    
    user_stats[user.id] = {
        'first_seen': datetime.now(),
        'attack_count': 0,
        'custom_message': None
    }

async def show_control_panel(update: Update, user):
    await update.message.reply_text(
        f"مرحبًا {user.first_name}!\nاختر من الأزرار:",
        reply_markup=CONTROL_PANEL
    )

async def handle_commands(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user = update.effective_user
    
    if text == "🚀 بدء الهجوم":
        await start_attack_sequence(update, context, user)
    elif text == "🛑 إيقاف فوري":
        await emergency_stop(update, context, user)
    elif text == "✏️ تعديل الرسالة":
        await request_custom_message(update, user)
    elif text == "⚙️ الإعدادات":
        await show_settings(update)
    elif text == "📊 الإحصائيات":
        await show_statistics(update, user)
    elif text == "❓ المساعدة":
        await show_help(update)

async def request_custom_message(update: Update, user):
    await update.message.reply_text(
        "📝 أرسل الرسالة الجديدة التي تريدها:",
        reply_markup=ReplyKeyboardRemove()
    )
    user_stats[user.id]['awaiting_message'] = True

async def handle_custom_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user_stats.get(user.id, {}).get('awaiting_message', False):
        new_message = update.message.text
        user_stats[user.id]['custom_message'] = new_message
        user_stats[user.id]['awaiting_message'] = False
        await update.message.reply_text(
            f"✅ تم تعيين الرسالة:\n{new_message}",
            reply_markup=CONTROL_PANEL
        )

async def start_attack_sequence(update: Update, context: ContextTypes.DEFAULT_TYPE, user):
    speed_selector = ReplyKeyboardMarkup(
        [[speed] for speed in ATTACK_PROFILES.keys()],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    await update.message.reply_text("⚡ اختر السرعة:", reply_markup=speed_selector)
    context.user_data['awaiting_speed'] = True

async def execute_attack(update: Update, context: ContextTypes.DEFAULT_TYPE, speed):
    user = update.effective_user
    config = ATTACK_PROFILES[speed]
    
    job = context.application.job_queue.run_repeating(
        attack_callback,
        interval=config['delay'],
        first=1,
        data={
            'user_id': user.id,
            'speed': speed,
            'symbol': config['symbol'],
            'custom_message': user_stats[user.id].get('custom_message')
        }
    )
    
    active_sessions[user.id] = {
        'job': job,
        'message_count': 0
    }
    
    await update.message.reply_text(
        f"⚡ بدأ الهجوم بسرعة {speed}!\n"
        f"⏱ كل {config['delay']} ثانية"
    )

async def attack_callback(context: CallbackContext):
    job = context.job
    user_id = job.data['user_id']
    symbol = job.data['symbol']
    custom_msg = job.data['custom_message']
    
    try:
        # استخدام الرسالة المخصصة إذا وجدت
        message = custom_msg if custom_msg else symbol * 100
        
        await context.bot.send_message(
            chat_id=user_id,
            text=message
        )
        
        active_sessions[user_id]['message_count'] += 1
        
    except Exception as e:
        logging.error(f"فشل الإرسال: {e}")

# باقي الدوال (emergency_stop, show_settings, show_statistics, show_help) تبقى كما هي

def main():
    application = Application.builder().token(TOKEN).build()
    
    application.add_handler(CommandHandler('start', start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_commands))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_custom_message))
    application.add_error_handler(error_handler)
    
    application.run_polling()

if __name__ == "__main__":
    main()
