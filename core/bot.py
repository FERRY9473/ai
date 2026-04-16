import telebot
import logging
import asyncio
from telebot.async_telebot import AsyncTeleBot
from telebot import apihelper, types
from config import TOKEN

# Enable middleware support
apihelper.ENABLE_MIDDLEWARE = True

# Initialize AsyncBot instance
bot = AsyncTeleBot(TOKEN, parse_mode='Markdown')

logger = logging.getLogger("Aphrodite")

async def safe_reply(message, text, **kwargs):
    """Safely reply to a message asynchronously, falling back to send_message if the original is deleted."""
    try:
        return await bot.reply_to(message, text, **kwargs)
    except telebot.apihelper.ApiTelegramException as e:
        if "message to be replied not found" in str(e).lower():
            # If reply fails because original message is gone, just send to the chat
            return await bot.send_message(message.chat.id, text, **kwargs)
        logger.error(f"Telegram API Error in safe_reply: {e}")
        raise e
    except Exception as e:
        logger.error(f"Unexpected error in safe_reply: {e}")
        return None

# Export bot instance and safe_reply
__all__ = ['bot', 'safe_reply']
