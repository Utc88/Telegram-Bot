from telegram import Update, ReplyKeyboardMarkup
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
import os
import random

# إعدادات البوت من المتغيرات البيئية
TOKEN = os.environ.get("BOT_TOKEN")
GROUP_ID = int(os.environ.get("GROUP_ID"))
ADMIN_ID = int(os.environ.get("ADMIN_ID"))

# إعدادات الهجوم
ATTACK_MODES = {
    'fast': {'delay': 0.5, 'messages': ["🚀 هجوم سريع!", "💣 إنفجار رسائل!"]},
    'medium': {'delay': 2, 'messages': ["🌀 هجوم متوسط!", "🕷 زحف إزعاج!"]},
    'slow': {'delay': 5, 'messages': ["🐌 هجوم بطيء!", "⏳ إستفزاز ناعم!"]}
}

# لوحة المفاتيح التفاعلية
main_keyboard = ReplyKeyboardMarkup(
    [
        ["تشغيل الهجوم 🚀", "إيقاف الهجوم 🛑"],
        ["تغيير السرعة ⚡", "العودة للقائمة 🏠"],
    ],
    resize_keyboard=True,
    persistent=True
)

# متغيرات النظام
active_attacks = {}
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض لوحة المفاتيح الرئيسية تلقائيًا"""
    user = update.effective_user
    await update.message.reply_text(
        f"مرحبا {user.first_name}! 👾\nاختر من الأزرار:",
        reply_markup=main_keyboard
    )
    
    # إرسال إشعار للقروب
    await context.bot.send_message(
        chat_id=GROUP_ID,
        text=f"👤 مستخدم جديد:\n{user.full_name}\n@{user.username}"
    )

async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    chat_id = update.effective_chat.id
    
    if text == "العودة للقائمة 🏠":
        await start(update, context)
    elif text == "تشغيل الهجوم 🚀":
        await start_attack(update, context, 'fast')
    elif text == "إيقاف الهجوم 🛑":
        await stop_attack(update, context)
    elif text == "تغيير السرعة ⚡":
        await switch_mode(update, context)

async def start_attack(update: Update, context: ContextTypes.DEFAULT_TYPE, mode: str):
    chat_id = update.effective_chat.id
    
    if chat_id in active_attacks:
        await update.message.reply_text("⚠️ الهجوم يعمل بالفعل!")
        return
    
    job = context.application.job_queue.run_repeating(
        attack_callback,
        interval=ATTACK_MODES[mode]['delay'],
        first=1,
        data={'chat_id': chat_id, 'mode': mode}
    )
    
    active_attacks[chat_id] = {'mode': mode, 'job': job}
    await update.message.reply_text(f"⚡ بدأ الهجوم بنمط {mode}!")
    
    # إرسال إشعار للقروب
    await context.bot.send_message(
        chat_id=GROUP_ID,
        text=f"🚨 هجوم جديد بدأ بواسطة @{update.effective_user.username}"
    )

async def stop_attack(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    
    if chat_id not in active_attacks:
        await update.message.reply_text("❌ لا يوجد هجوم نشط!")
        return
    
    active_attacks[chat_id]['job'].schedule_removal()
    del active_attacks[chat_id]
    await update.message.reply_text("✅ تم إيقاف الهجوم!")
    
    # إرسال إشعار للقروب
    await context.bot.send_message(
        chat_id=GROUP_ID,
        text=f"🛑 توقف الهجوم بواسطة @{update.effective_user.username}"
    )

async def switch_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    
    if chat_id not in active_attacks:
        await update.message.reply_text("❌ أبدأ الهجوم أولاً!")
        return
    
    current_mode = active_attacks[chat_id]['mode']
    modes = list(ATTACK_MODES.keys())
    new_mode = modes[(modes.index(current_mode) + 1) % len(modes)]
    
    await stop_attack(update, context)
    await start_attack(update, context, new_mode)

async def attack_callback(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    mode = job.data['mode']
    chat_id = job.data['chat_id']
    
    try:
        message = random.choice(ATTACK_MODES[mode]['messages'])
        await context.bot.send_message(chat_id, message)
    except Exception as e:
        logging.error(f"فشل الإرسال: {e}")
        await context.bot.send_message(ADMIN_ID, f"⚠️ خطأ: {e}")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    error = context.error
    logging.error(f"خطأ غير متوقع: {error}")
    await context.bot.send_message(ADMIN_ID, f"🔥 خطأ حرج: {error}")

def main():
    application = Application.builder().token(TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_buttons))
    application.add_error_handler(error_handler)
    
    application.run_polling()

if __name__ == "__main__":
    while True:
        try:
            main()
        except Exception as e:
            logging.error(f"إعادة التشغيل بسبب: {e}")
            time.sleep(10)
