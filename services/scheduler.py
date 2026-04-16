import asyncio
import logging
from datetime import datetime
import pytz
import httpx
from core.bot import bot
from database.db import db
from config import TZ

logger = logging.getLogger("Scheduler")

# Cache to store prayer times for cities
prayer_cache = {}
# Track last sent to avoid duplicates in the same minute
last_sent_cache = {}

async def check_prayer_times():
    """Background task to check and send prayer reminders (Async version)"""
    logger.info("Prayer Scheduler background task started.")
    
    async with httpx.AsyncClient() as client:
        while True:
            try:
                now = datetime.now(pytz.timezone(TZ))
                current_time = now.strftime("%H:%M")
                today = now.strftime("%Y-%m-%d")
                
                # 1. Process Groups
                for chat_id, data in db.groups.items():
                    if data.get("sholat_remind"):
                        city = data.get("city", "jakarta")
                        await process_reminder(client, chat_id, city, current_time, today)
                
                # 2. Process Users
                for user_id, data in db.users.items():
                    if data.get("sholat_remind"):
                        city = data.get("city", "jakarta")
                        await process_reminder(client, user_id, city, current_time, today)
                        
            except Exception as e:
                logger.error(f"Scheduler Loop Error: {e}")
                
            # Wait 30 seconds for next check (more frequent but safe with last_sent_cache)
            await asyncio.sleep(30)

async def process_reminder(client, chat_id, city, current_time, today):
    cache_key = f"{city}_{today}"
    
    # Get or update cache asynchronously
    if cache_key not in prayer_cache:
        try:
            # API: Aladhan
            url = f"https://api.aladhan.com/v1/timingsByCity/{datetime.now().strftime('%d-%m-%Y')}?city={city}&country=Indonesia&method=2"
            r = await client.get(url, timeout=10)
            if r.status_code == 200:
                prayer_cache[cache_key] = r.json().get("data", {}).get("timings", {})
            else:
                logger.error(f"API Error {r.status_code} for {city}")
                return
        except Exception as e:
            logger.error(f"Failed to fetch prayer times for {city}: {e}")
            return

    timings = prayer_cache.get(cache_key, {})
    
    # Check for Subuh, Dzuhur, Ashar, Maghrib, Isya
    prayers = ["Fajr", "Dhuhr", "Asr", "Maghrib", "Isha"]
    names = {"Fajr": "Subuh", "Dhuhr": "Dzuhur", "Asr": "Ashar", "Maghrib": "Maghrib", "Isha": "Isya"}
    
    for p in prayers:
        t = timings.get(p)
        if t == current_time:
            # Check if already sent for this specific prayer today
            sent_key = f"{chat_id}_{today}_{p}"
            if last_sent_cache.get(sent_key):
                continue

            msg = (
                f"🕌 *WAKTU SHOLAT {names[p].upper()} TELAH TIBA!*\n\n"
                f"Wilayah: *{city.upper()}*\n"
                f"Jam: `{t}`\n\n"
                f"Mari sejenak hentikan aktivitas dan tunaikan kewajiban sholat tepat waktu. 🙏"
            )
            try:
                await bot.send_message(chat_id, msg, parse_mode='Markdown')
                logger.info(f"Sent prayer reminder to {chat_id} for {names[p]}")
                last_sent_cache[sent_key] = True
                
                # Cleanup old cache entries (naive cleanup)
                if len(last_sent_cache) > 1000:
                    last_sent_cache.clear()
                    
            except Exception as e:
                logger.error(f"Failed to send reminder to {chat_id}: {e}")

def start_scheduler():
    # Create the task in the existing loop
    asyncio.create_task(check_prayer_times())
