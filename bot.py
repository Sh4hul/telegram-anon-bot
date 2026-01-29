from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)
import time
from datetime import datetime
import os
BOT_TOKEN = os.environ.get("BOT_TOKEN")

# ================== CONFIG ==================
ADMIN_ID = 1970729876  # <-- your Telegram ID
# ============================================

waiting_users = []
active_chats = {}
user_reports = {}
all_users = set()
today_users = set()
total_chats = 0
bot_start_time = time.time()
today_date = datetime.now().date()

# ================== BUTTONS ==================
def start_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔍 Find Partner", callback_data="find")]
    ])

def chat_menu():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("⏭ Next", callback_data="next"),
            InlineKeyboardButton("🚨 Report", callback_data="report")
        ]
    ])

# ================== START ==================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global today_date
    user_id = update.effective_user.id

    # reset daily users if date changed
    if datetime.now().date() != today_date:
        today_users.clear()
        today_date = datetime.now().date()

    all_users.add(user_id)
    today_users.add(user_id)

    rules_text = (
        "👋 *Welcome to Anonymous Chat Bot*\n\n"
        "📜 *Rules:*\n"
        "❌ No porn\n"
        "❌ No abuse\n"
        "❌ No threats\n"
        "❌ No illegal content\n\n"
        "🚨 *5 reports = warning / ban*\n\n"
        "Click below to start chatting 👇"
    )

    await update.message.reply_text(
        rules_text,
        parse_mode="Markdown",
        reply_markup=start_menu()
    )

# ================== MATCHING ==================
async def find_partner(user_id, context):
    global total_chats

    if user_id in waiting_users or user_id in active_chats:
        return

    if waiting_users:
        partner = waiting_users.pop(0)

        active_chats[user_id] = partner
        active_chats[partner] = user_id
        total_chats += 1

        await context.bot.send_message(
            partner, "✅ Partner connected!", reply_markup=chat_menu()
        )
        await context.bot.send_message(
            user_id, "✅ Partner connected!", reply_markup=chat_menu()
        )
    else:
        waiting_users.append(user_id)
        await context.bot.send_message(user_id, "⏳ Waiting for partner...")

# ================== DISCONNECT ==================
async def disconnect(user_id, context):
    if user_id in active_chats:
        partner = active_chats.pop(user_id)
        active_chats.pop(partner, None)

        await context.bot.send_message(partner, "❌ Partner left.")
        await context.bot.send_message(user_id, "❌ Disconnected.")

    elif user_id in waiting_users:
        waiting_users.remove(user_id)

# ================== BUTTON HANDLER ==================
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if query.data == "find":
        await find_partner(user_id, context)

    elif query.data == "next":
        await disconnect(user_id, context)
        await find_partner(user_id, context)

    elif query.data == "report":
        if user_id in active_chats:
            offender = active_chats[user_id]
            user_reports[offender] = user_reports.get(offender, 0) + 1

            await query.message.reply_text("🚨 User reported.")
            await disconnect(user_id, context)

            if user_reports[offender] >= 5:
                await context.bot.send_message(
                    offender,
                    "⚠️ WARNING!\nYou received 5 reports.\nFurther violations may lead to ban."
                )

# ================== MESSAGE RELAY ==================
async def relay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

    if user_id in active_chats:
        await context.bot.send_message(
            active_chats[user_id],
            update.message.text
        )

# ================== ADMIN PANEL ==================
async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        return

    uptime = int(time.time() - bot_start_time)
    hours = uptime // 3600
    minutes = (uptime % 3600) // 60

    await update.message.reply_text(
        f"👑 *Admin Panel*\n\n"
        f"👥 Total users: {len(all_users)}\n"
        f"📅 Users today: {len(today_users)}\n"
        f"💬 Active chats: {len(active_chats)//2}\n"
        f"🔁 Total chats: {total_chats}\n"
        f"⏱ Uptime: {hours}h {minutes}m",
        parse_mode="Markdown"
    )

# ================== APP ==================
app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("admin", admin))
app.add_handler(CallbackQueryHandler(button_handler))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, relay))

print("🤖 Bot running with full features...")
app.run_polling()
