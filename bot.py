import os
import logging
from telegram.ext import Updater, CommandHandler, MessageHandler
from telegram.utils.request import Request
from telegram import Bot, Update
from pymongo import MongoClient
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Enable logging
logging.basicConfig(level=logging.INFO)

# MongoDB connection
MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client["terabox_downloader"]
collection = db["downloads"]

# Telegram Bot Token
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Create a Telegram Bot instance
bot = Bot(BOT_TOKEN)

# Define a function to handle the /start command
def start(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Welcome to Terabox Downloader Bot!")

# Define a function to handle the /download command
def download(update, context):
    # Get the file URL from the user
    file_url = context.args[0]

    # Download the file using Terabox API
    try:
        response = requests.get(file_url, stream=True)
        response.raise_for_status()
        file_name = file_url.split("/")[-1]
        with open(file_name, "wb") as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
        # Save the file to MongoDB
        collection.insert_one({"file_url": file_url, "status": "downloaded"})
        # Send a message to the user
        context.bot.send_message(chat_id=update.effective_chat.id, text="File downloaded successfully!")
    except Exception as e:
        # Save the file to MongoDB
        collection.insert_one({"file_url": file_url, "status": "failed"})
        # Send a message to the user
        context.bot.send_message(chat_id=update.effective_chat.id, text="Failed to download file!")

# Define a function to handle the /status command
def status(update, context):
    # Get the file URL from the user
    file_url = context.args[0]

    # Check the status of the file in MongoDB
    file_status = collection.find_one({"file_url": file_url})

    # Send a message to the user
    if file_status:
        context.bot.send_message(chat_id=update.effective_chat.id, text=f"File status: {file_status['status']}")
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text="File not found!")

# Create a Telegram Updater instance
updater = Updater(BOT_TOKEN, use_context=True)

# Add handlers for the /start, /download, and /status commands
updater.dispatcher.add_handler(CommandHandler("start", start))
updater.dispatcher.add_handler(CommandHandler("download", download))
updater.dispatcher.add_handler(CommandHandler("status", status))

# Start the bot
updater.start_polling()
updater.idle()
