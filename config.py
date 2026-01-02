import os
from dotenv import load_dotenv

load_dotenv()

# Telegram Bot Token
TOKEN = os.getenv(
    "BOT_TOKEN",
    "8036904861:AAHCKR3meY3EG2nxSlTGp4E0RoN_3RtnZbg"
)

# Database settings
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_PORT = os.getenv("DB_PORT")

