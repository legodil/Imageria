import os
import csv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, filters
)

BOT_TOKEN = "8085608463:AAFLqDCyv0vGvtD0PpCLE0SXNiYqFrEJqLA"
UPI_ID = "93366749682@omni"
DESIGNER_ID = 1653550351  # Your Telegram ID

DP_IMAGES = os.listdir("dp_catalog")
NAME_IMAGES = os.listdir("name_catalog")
USER_STATE = {}
ORDER_LOG_FILE = "order_log.csv"

# Ensure order log file exists
if not os.path.exists(ORDER_LOG_FILE):
    with open(ORDER_LOG_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Username", "Telegram ID", "Order Type", "Design", "Custom Name", "Transaction ID"])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hello! 👋 What would you like to buy?")
    keyboard = [
        [InlineKeyboardButton("🖼 DP Design", callback_data="dp")],
        [InlineKeyboardButton("✍️ Name Customized Image", callback_data="name")]
    ]
    await update.message.reply_text("Choose an option:", reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    if USER_STATE.get(user_id) == "waiting_for_name":
        context.user_data["custom_name"] = text
        USER_STATE[user_id] = "waiting_for_payment_screenshot"
        keyboard = [[InlineKeyboardButton("✅ I've Paid", callback_data="paid_name")]]
        await update.message.reply_text(
            f"""To buy this custom image, send ₹X to:

💸 *{UPI_ID}*

After payment:
- Send screenshot here
- Send transaction ID
- Mention your Telegram ID

Then tap the button below.""",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif USER_STATE.get(user_id) == "waiting_for_payment_screenshot":
        photo_file = context.user_data.get("last_screenshot")
        order_type = context.user_data.get("order_type", "Unknown")
        design = context.user_data.get("dp_choice") if order_type == "DP" else context.user_data.get("name_sample")
        custom_name = context.user_data.get("custom_name") if order_type == "Name" else "-"

        if photo_file:
            caption = f"🆕 Payment Proof Received!\n\n👤 From: @{update.effective_user.username or update.effective_user.first_name}\n🆔 Telegram ID: {user_id}\n📦 Order Type: {order_type}\n🎨 Design: {design}\n✏️ Name: {custom_name}\n💳 Transaction ID: {text}"

            await context.bot.send_photo(
                chat_id=DESIGNER_ID,
                photo=photo_file,
                caption=caption
            )

            # Save to CSV log
            with open(ORDER_LOG_FILE, "a", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([
                    update.effective_user.username or update.effective_user.first_name,
                    user_id,
                    order_type,
                    design,
                    custom_name,
                    text
                ])

            await update.message.reply_text("✅ Your order and payment have been sent to the designer. Please wait for delivery.")
            context.user_data["last_screenshot"] = None
        else:
            await update.message.reply_text("📸 Please send screenshot first, then the transaction ID.")

    else:
        await update.message.reply_text("Please use /start to begin.")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if USER_STATE.get(user_id) == "waiting_for_payment_screenshot":
        photo_file_id = update.message.photo[-1].file_id
        context.user_data["last_screenshot"] = photo_file_id
        await update.message.reply_text("📸 Screenshot received. Now send transaction ID.")

async def handle_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "dp":
        context.user_data["order_type"] = "DP"
        for img in DP_IMAGES:
            with open(f"dp_catalog/{img}", "rb") as photo:
                await context.bot.send_photo(
                    chat_id=update.effective_chat.id,
                    photo=photo,
                    caption=f"{img}\nClick below to buy this!",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("Buy", callback_data=f"buy_dp:{img}")]
                    ])
                )

    elif query.data == "name":
        context.user_data["order_type"] = "Name"
        for img in NAME_IMAGES:
            with open(f"name_catalog/{img}", "rb") as photo:
                await context.bot.send_photo(
                    chat_id=update.effective_chat.id,
                    photo=photo,
                    caption=f"{img}\nClick below to choose this!",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("Choose", callback_data=f"buy_name:{img}")]
                    ])
                )

    elif query.data.startswith("buy_dp:"):
        filename = query.data.split(":")[1]
        context.user_data["dp_choice"] = filename
        context.user_data["order_type"] = "DP"

        keyboard = [[InlineKeyboardButton("✅ I've Paid", callback_data="paid_dp")]]
        await query.message.reply_text(
            f"""To buy this DP, send ₹X to:

💸 *{UPI_ID}*

After payment:
- Send screenshot here
- Send transaction ID
- Mention your Telegram ID

Then tap the button below.""",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        USER_STATE[query.from_user.id] = "waiting_for_payment_screenshot"

    elif query.data.startswith("buy_name:"):
        filename = query.data.split(":")[1]
        context.user_data["name_sample"] = filename
        context.user_data["order_type"] = "Name"
        USER_STATE[query.from_user.id] = "waiting_for_name"
        await query.message.reply_text("Please send the name you want on the image.")

    elif query.data == "paid_dp":
        await query.message.reply_text("✅ Your payment has been sent to the designer. Please wait for delivery.")

    elif query.data == "paid_name":
        await query.message.reply_text("✅ Thanks! Your customized image will be delivered shortly.")
        name = context.user_data.get("custom_name")
        filename = context.user_data.get("name_sample")
        await context.bot.send_message(
            DESIGNER_ID,
            f"🆕 New Order (Custom Name Image):\nFrom: @{query.from_user.username or query.from_user.first_name}\nName: {name}\nDesign: {filename}"
        )

app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(handle_choice))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
app.add_handler(MessageHandler(filters.PHOTO, handle_photo))

app.run_polling()
