import json
import os
import threading
from datetime import datetime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8650075665:AAGUTkGhIJUfkgpOU16Zy21DqTgX7LZkzc0")
ADMIN_ID = 1269988382

DATA_FILE = "files.json"
lock = threading.Lock()

#   تحميل البيانات
def load_data():
    if not os.path.exists(DATA_FILE):
        return {
            "computer programming": [],
            "mathematics": [],
            "arabic": [],
            "english": [],
            "electrical circuit analysis": [],
            "cyber security fundamentals": [],
            "network fundamentals": []
        }

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

#   حفظ البيانات
def save_data(data):
    with lock:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

files_db = load_data()
user_state = {}

#   /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📘 computer programming", callback_data="computer programming")],
        [InlineKeyboardButton("📗 mathematics", callback_data="mathematics")],
        [InlineKeyboardButton("📕 arabic", callback_data="arabic")],
        [InlineKeyboardButton("📙 english", callback_data="english")],
        [InlineKeyboardButton("📔 Electrical Circuit Analysis", callback_data="electrical circuit analysis")],
        [InlineKeyboardButton("🔐 cyber security fundamentals", callback_data="cyber security fundamentals")],
        [InlineKeyboardButton("🌐 network fundamentals", callback_data="network fundamentals")]
    ]

    if update.effective_user.id == ADMIN_ID:
        keyboard.append([InlineKeyboardButton("➕ رفع ملف", callback_data="upload")])

    await update.message.reply_text(
        "اختر المادة 📚:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

#   الأزرار
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data

    if data == "upload":
        user_state[query.from_user.id] = "awaiting_subject"
        await query.message.reply_text("اكتب اسم المادة الآن 📚")
        return

    subject_files = files_db.get(data, [])

    if not subject_files:
        await query.message.reply_text("لا توجد ملفات ❌")
        return

    for f in subject_files:
        caption = f"📄 {f['file_name']}"
        await context.bot.send_document(
            chat_id=query.message.chat_id,
            document=f["file_id"],
            caption=caption
        )

#   اختيار المادة
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id != ADMIN_ID:
        return

    if user_state.get(user_id) == "awaiting_subject":
        subject = update.message.text

        if subject not in files_db:
            await update.message.reply_text("المادة غير موجودة ❌")
            return

        user_state[user_id] = subject
        await update.message.reply_text(f"ارسل الملف الآن لمادة {subject}")

#   رفع الملفات
async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id != ADMIN_ID:
        return

    subject = user_state.get(user_id)

    if not subject:
        await update.message.reply_text("اختار مادة أولاً")
        return

    file = update.message.document

    file_data = {
        "file_id": file.file_id,
        "file_name": file.file_name,
        "uploader": update.message.from_user.first_name,
        "user_id": user_id,
        "date": datetime.now().strftime("%Y-%m-%d %H:%M")
    }

    files_db[subject].append(file_data)
    save_data(files_db)

    await update.message.reply_text("تم الحفظ بشكل مرتب ودائم ✅")

#   حذف ملف
async def remove_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    if len(context.args) != 2:
        await update.message.reply_text("استخدام: /remove <المادة> <الفهرس>")
        return

    subject = context.args[0]

    try:
        index = int(context.args[1])
    except:
        await update.message.reply_text("الفهرس خطأ")
        return

    if subject in files_db and 0 <= index < len(files_db[subject]):
        del files_db[subject][index]
        save_data(files_db)
        await update.message.reply_text("تم الحذف ✅")
    else:
        await update.message.reply_text("غير موجود")

#   تشغيل البوت
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("remove", remove_file))
app.add_handler(CallbackQueryHandler(button))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
app.add_handler(MessageHandler(filters.Document.ALL, handle_file))

print("Bot is running... ")
app.run_polling()
