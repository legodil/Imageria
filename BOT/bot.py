import os
import csv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)

import logging

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))  # Add admin ID in environment variable

DP_PATH = "BOT/dp_catalog"
ORDER_LOG_FILE = "order_log.csv"
USER_STATE = {}

logging.basicConfig(level=logging.INFO)

def get_dp_keyboard():
    buttons = []
    for img in os.listdir(DP_PATH):
        buttons.append([InlineKeyboardButton(img, callback_data=f"buy_{img}")])
    return InlineKeyboardMarkup(buttons)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome to Imageria!\nClick below to view and buy a DP image.",
        reply_markup=get_dp_keyboard()
    )

async def buy_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    img_name = query.data.split("_", 1)[1]
    USER_STATE[query.from_user.id] = img_name

    with open(os.path.join(DP_PATH, img_name), "rb") as img_file:
        await query.message.reply_photo(
            photo=InputFile(img_file),
            caption="This is your selected DP.\nSend your UPI Transaction ID & Screenshot below."
        )

async def handle_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    img_name = USER_STATE.get(user_id)

    if not img_name:
        await update.message.reply_text("❌ You haven't selected any DP image yet.")
        return

    txn_id = update.message.caption or update.message.text
    photo = update.message.photo[-1].file_id if update.message.photo else None

    await update.message.reply_text("✅ Payment proof received. Please wait for manual verification.")

    msg = f"🧾 Payment Proof\nUser: @{update.message.from_user.username} ({user_id})\nSelected: {img_name}\nTransaction ID: {txn_id}"

    if photo:
        await context.bot.send_photo(chat_id=ADMIN_ID, photo=photo, caption=msg)
    else:
        await context.bot.send_message(chat_id=ADMIN_ID, text=msg)

    # Save to log
    with open(ORDER_LOG_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([user_id, img_name, txn_id])

async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❓ Sorry, I didn't understand that. Use /start to begin.")

if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(buy_callback))
    app.add_handler(MessageHandler(filters.TEXT | filters.PHOTO, handle_payment))
    app.add_handler(MessageHandler(filters.COMMAND, unknown))

    app.run_polling()
