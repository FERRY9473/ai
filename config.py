import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
ADMIN_ID = int(os.getenv("ADMIN_CHAT_ID", "1803063423"))
OWNER_ID = int(os.getenv("OWNER_ID", "1803063423"))
TZ = os.getenv("TZ", "Asia/Jakarta")

# Other Configurations
VERSION = "12.0.0"
BOT_NAME = "Aphrodite"
DATABASE_PATH = "ai/database/aphrodite.db"

# Group Management Defaults
DEFAULT_WELCOME_MESSAGE = "Halo {name}! Selamat datang di grup {group_name}!"
DEFAULT_GOODBYE_MESSAGE = "Selamat jalan {name}!"
