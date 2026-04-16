from core.bot import bot, safe_reply
from database.db import db
from datetime import datetime, timedelta
import random

@bot.message_handler(commands=['claim', 'daily', 'harian'])
async def daily_claim(message):
    """Claim daily rewards (Cooldown 24h)"""
    user_id = message.from_user.id
    user_data = db.get_user(user_id)
    
    # Check cooldown
    last_claim_str = user_data.get("last_claim")
    now = datetime.now()
    
    if last_claim_str:
        last_claim = datetime.fromisoformat(last_claim_str)
        if now < last_claim + timedelta(days=1):
            remaining = (last_claim + timedelta(days=1)) - now
            hours, remainder = divmod(int(remaining.total_seconds()), 3600)
            minutes, _ = divmod(remainder, 60)
            return await safe_reply(message, f"❌ *SALAH COOLDOWN*\n\nKamu sudah klaim hari ini. Tunggu `{hours} jam {minutes} menit` lagi ya!")

    # Reward
    coin_reward = random.randint(100, 500)
    xp_reward = random.randint(20, 100)
    
    user_data["coins"] = user_data.get("coins", 0) + coin_reward
    user_data["xp"] = user_data.get("xp", 0) + xp_reward
    user_data["last_claim"] = now.isoformat()
    
    # Level Up Check
    new_level = (user_data["xp"] // 100) + 1
    old_level = user_data.get("level", 1)
    user_data["level"] = new_level
    
    db.update_user(user_id, user_data)
    
    msg = f"""
🎁 *HADIAH HARIAN*
━━━━━━━━━━━━━━━━━━━━

Berhasil mengklaim:
💰 +`{coin_reward}` Koin
✨ +`{xp_reward}` XP

Saldo sekarang: `{user_data['coins']}` Koin
XP Anda: `{user_data['xp']}`
"""
    if new_level > old_level:
        msg += f"\n🎉 *LEVEL UP!* Anda sekarang Level `{new_level}`!"
        
    await safe_reply(message, msg, parse_mode="Markdown")
