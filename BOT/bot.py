# Telegram Bot for Selling DP & Name Customized Images

import os
import csv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, filters
)

BOT_TOKEN = os.getenv("BOT_TOKEN")
UPI_ID = os.getenv("UPI_ID")
DESIGNER_ID = 1653550351  # Your Telegram ID

DP_IMAGES = os.listdir("dp_catalog")
NAME_IMAGES = os.listdir("name_catalog")
USER_STATE = {}
ORDER_LOG_FILE = "order_log.csv"

if not os.path.exists(ORDER_LOG_FILE):
    with open(ORDER_LOG_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Username", "Telegram ID", "Order Type", "Design", "Custom Name", "Transaction ID"])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Welcome! What would you like to buy?")
    keyboard = [
        [InlineKeyboardButton("🖼 DP Design", callback_data="dp")],
        [InlineKeyboardButton("✍️ Name Image", callback_data="name")]
    ]
    await update.message.reply_text("Choose an option:", reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    if USER_STATE.get(user_id) == "waiting_for_name":
        context.user_data["custom_name"] = text
        USER_STATE[user_id] = "waiting_for_payment_screenshot"
        await send_payment_instructions(update, context, "paid_name")

    elif USER_STATE.get(user_id) == "waiting_for_payment_screenshot":
        if context.user_data.get("last_screenshot"):
            await forward_order(update, context, text)
        else:
            await update.message.reply_text("📸 Please send screenshot first, then transaction ID.")

    else:
        await update.message.reply_text("Please use /start to begin.")

async def send_payment_instructions(update: Update, context: ContextTypes.DEFAULT_TYPE, paid_callback):
    keyboard = [[InlineKeyboardButton("✅ I've Paid", callback_data=paid_callback)]]
    await update.message.reply_text(
        f"To buy, send ₹X to:\n\n💸 *{UPI_ID}*\n\nAfter payment:\n- Send screenshot here\n- Send transaction ID\n\nThen tap the button below.",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def forward_order(update: Update, context: ContextTypes.DEFAULT_TYPE, transaction_id):
    user_id = update.effective_user.id
    order_type = context.user_data.get("order_type")
    design = context.user_data.get("dp_choice") if order_type == "DP" else context.user_data.get("name_sample")
    name = context.user_data.get("custom_name") if order_type == "Name" else "-"
    photo_file = context.user_data.get("last_screenshot")

    caption = f"🆕 Order Received!\n👤 @{update.effective_user.username or update.effective_user.first_name}\n🆔 {user_id}\n📦 {order_type}\n🎨 {design}\n✏️ {name}\n💳 {transaction_id}"

    await context.bot.send_photo(chat_id=DESIGNER_ID, photo=photo_file, caption=caption)

    with open(ORDER_LOG_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([update.effective_user.username or update.effective_user.first_name, user_id, order_type, design, name, transaction_id])

    await update.message.reply_text("✅ Your order has been sent to the designer.")
    context.user_data.clear()
    USER_STATE.pop(user_id, None)

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if USER_STATE.get(update.effective_user.id) == "waiting_for_payment_screenshot":
        context.user_data["last_screenshot"] = update.message.photo[-1].file_id
        await update.message.reply_text("📸 Screenshot received. Now send transaction ID.")

async def handle_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "dp":
        context.user_data["order_type"] = "DP"
        for img in DP_IMAGES:
            with open(f"dp_catalog/{img}", "rb") as photo:
                await context.bot.send_photo(
                    chat_id=query.message.chat.id,
                    photo=photo,
                    caption=f"{img}\nClick below to buy this!",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Buy", callback_data=f"buy_dp:{img}")]])
                )

    elif query.data == "name":
        context.user_data["order_type"] = "Name"
        for img in NAME_IMAGES:
            with open(f"name_catalog/{img}", "rb") as photo:
                await context.bot.send_photo(
                    chat_id=query.message.chat.id,
                    photo=photo,
                    caption=f"{img}\nClick below to choose this!",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Choose", callback_data=f"buy_name:{img}")]])
                )

    elif query.data.startswith("buy_dp:"):
        context.user_data["dp_choice"] = query.data.split(":")[1]
        USER_STATE[query.from_user.id] = "waiting_for_payment_screenshot"
        await send_payment_instructions(query.message, context, "paid_dp")

    elif query.data.startswith("buy_name:"):
        context.user_data["name_sample"] = query.data.split(":")[1]
        USER_STATE[query.from_user.id] = "waiting_for_name"
        await query.message.reply_text("Please send the name you want on the image.")

    elif query.data == "paid_dp":
        await query.message.reply_text("✅ Thanks! Your DP order has been submitted.")

    elif query.data == "paid_name":
        await query.message.reply_text("✅ Thanks! Your name-customized image will be delivered soon.")
        await context.bot.send_message(
            chat_id=DESIGNER_ID,
            text=f"🆕 Name Order: @{query.from_user.username or query.from_user.first_name}\nName: {context.user_data.get('custom_name')}\nDesign: {context.user_data.get('name_sample')}"
        )

# Bot setup
app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(handle_choice))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
app.add_handler(MessageHandler(filters.PHOTO, handle_photo))

app.run_polling()
