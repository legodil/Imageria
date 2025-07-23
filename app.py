import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

TOKEN = "8085608463:AAFLqDCyv0vGvtD0PpCLE0SXNiYqFrEJqLA"  # Replace with your Bot Token

# Start Command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🙏 Welcome bhai! Yahan aap DP packs, notes, aur templates buy kar sakte ho.\n\n"
        "Type /shop dekhne ke liye ya /help agar kuch puchhna ho. 💬"
    )

# Shop Command
async def shop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reply_keyboard = [['Name DP Pack ₹29', 'Study Notes ₹49']]
    markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)

    await update.message.reply_text(
        "🛍️ Products Available:\n\n"
        "1. Name DP Pack - ₹29\n"
        "2. Study Notes (Class 10) - ₹49\n\n"
        "Payment UPI: 98xxxxxx00@ybl\n\n"
        "Payment ke baad screenshot bhejo yahin par 📸",
        reply_markup=markup
    )

# Payment Screenshot Response
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if message.photo:
        await message.reply_text(
            "✅ Screenshot mil gaya bhai! Jaldi se file bhej raha hoon 📦"
        )
        # Example file sending
        await message.reply_document(document=open("dp_pack.zip", "rb"))  # Change filename
    else:
        await message.reply_text("Screenshot bhejo bhai ya /shop dabao dobara.")

# Help Command
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Koi dikkat hai? Bas /start ya /shop try karo. Ya mujhe photo bhejo (screenshot).")

# Main Function
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("shop", shop))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.ALL, handle_message))

    print("Bot running...")
    app.run_polling()

if __name__ == '__main__':
    main()
