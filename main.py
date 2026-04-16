import logging
import sys
import os
import asyncio

from core.bot import bot
from config import BOT_NAME, VERSION
from database.db import db
from datetime import datetime
from telebot.asyncio_handler_backends import BaseMiddleware

# Import all handlers to register them
import handlers.general
import handlers.games
import handlers.games_new
import handlers.ludo
import handlers.connect4
import handlers.blackjack
import handlers.ai_chat
import handlers.group_management
import handlers.leaderboard
import handlers.shop
import handlers.quests
import handlers.features
import handlers.admin
import handlers.rpg

# Middleware to track users and groups (Async version)
class UserTrackerMiddleware(BaseMiddleware):
    def __init__(self):
        super().__init__()
        self.update_types = ['message']

    async def pre_process(self, message, data):
        if not message.from_user or message.from_user.is_bot:
            return

        user_id = message.from_user.id
        chat_id = message.chat.id
        user_name = message.from_user.first_name

        # Track User
        user_data = db.get_user(user_id)
        user_data["messages"] = user_data.get("messages", 0) + 1
        user_data["last_seen"] = datetime.now().isoformat()
        user_data["first_name"] = user_name
        
        # Give some XP for every message
        xp_gain = 2
        user_data["xp"] = user_data.get("xp", 0) + xp_gain
        
        # Level Up Check - Linear formula: 100 XP per level
        # level 1: 0-99 XP
        # level 2: 100-199 XP
        # level 3: 200-299 XP
        new_level = (user_data["xp"] // 100) + 1
        old_level = user_data.get("level", 1)
        
        if new_level > old_level:
             user_data["level"] = new_level
             # We could send a level up message here if we wanted
             
        db.update_user(user_id, user_data)

        # Track Group and User association
        if message.chat.type in ['group', 'supergroup']:
            # Track group data
            group_data = db.get_group(chat_id)
            group_data["last_seen"] = datetime.now().isoformat()
            group_data["title"] = message.chat.title
            db.update_group(chat_id, group_data)
            
            # Track user in this group
            group_id_str = str(chat_id)
            # Use a set to avoid duplicates and handle efficiently
            group_users = set(db.group_users.get(group_id_str, []))
            if user_id not in group_users:
                group_users.add(user_id)
                db.group_users[group_id_str] = list(group_users)

    async def post_process(self, message, data, exception):
        pass

# Register Middleware
bot.setup_middleware(UserTrackerMiddleware())


from logging.handlers import RotatingFileHandler

# Configure Logging with Rotation
log_handler = RotatingFileHandler(
    "ai/bot.log", 
    maxBytes=10*1024*1024, # 10 MB per file
    backupCount=5,         # Simpan hingga 5 file lama
    encoding='utf-8'
)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(levelname)s] - %(name)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        log_handler
    ]
)
logger = logging.getLogger(BOT_NAME)

from services.scheduler import start_scheduler

async def main():
    logger.info(f"Starting {BOT_NAME} v{VERSION} (Async)...")
    try:
        # Start Prayer Scheduler (Async task)
        start_scheduler()
        
        # Get Bot Info
        me = await bot.get_me()
        logger.info(f"Bot @{me.username} is running.")
        
        # Start Polling
        await bot.polling(non_stop=True, skip_pending=True)
    except Exception as e:
        logger.error(f"Critical error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
