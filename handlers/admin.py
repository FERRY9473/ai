from core.bot import bot, safe_reply
from config import OWNER_ID, ADMIN_ID
from database.db import db
import asyncio
import logging

def is_owner(user_id):
    return user_id in [OWNER_ID, ADMIN_ID]

@bot.message_handler(commands=['stats'])
async def stats_handler(message):
    if not is_owner(message.from_user.id):
        return
    
    try:
        user_count = len(db.users)
        group_count = len(db.groups)
        
        msg = (
            f"📊 *STATISTIK BOT*\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 *Total User:* {user_count}\n"
            f"👥 *Total Grup:* {group_count}\n"
            f"━━━━━━━━━━━━━━━━━━━━"
        )
        await safe_reply(message, msg)
    except Exception as e:
        logging.error(f"Stats Error: {e}")
        await safe_reply(message, f"❌ Gagal mengambil statistik: {e}")

@bot.message_handler(commands=['broadcast', 'bc'])
async def broadcast_handler(message):
    if not is_owner(message.from_user.id):
        return
    
    # Check if this is a reply broadcast or a text broadcast
    reply = message.reply_to_message
    text = None
    if not reply:
        query = message.text.split(maxsplit=1)
        if len(query) < 2:
            return await safe_reply(message, "📢 *Gunakan:* `/bc <pesan>` atau Balas sebuah pesan/foto dengan `/bc` untuk membroadcast-nya.")
        text = f"📢 *PENGUMUMAN OWNER*\n━━━━━━━━━━━━━━━━━━━━\n\n{query[1]}\n\n━━━━━━━━━━━━━━━━━━━━"
    
    m = await safe_reply(message, "🚀 *Memulai broadcast massal...*")
    
    success = 0
    fail = 0
    
    # Broadcast to Users (Private)
    user_ids = list(db.users.keys())
    # Broadcast to Groups
    group_ids = list(db.groups.keys())
    
    targets = list(set(user_ids + group_ids)) # Unique list of IDs
    
    for target_id in targets:
        try:
            if reply:
                # Copy message with media support
                await bot.copy_message(target_id, message.chat.id, reply.message_id)
            else:
                await bot.send_message(target_id, text, parse_mode='Markdown')
            
            success += 1
            # Rate limiting: 20 messages per second (Telegram limit is roughly 30)
            await asyncio.sleep(0.05)
        except Exception:
            fail += 1
            
    if m:
        await bot.edit_message_text(f"✅ *Broadcast Selesai!*\n\n🟢 Berhasil: {success}\n🔴 Gagal: {fail}", m.chat.id, m.message_id, parse_mode='Markdown')

@bot.message_handler(commands=['addcoin'])
async def add_coin_handler(message):
    """Owner command to add coins to a user"""
    if not is_owner(message.from_user.id):
        return
    
    args = message.text.split()
    target_id = None
    amount = 0
    
    if message.reply_to_message:
        target_id = message.reply_to_message.from_user.id
        if len(args) > 1 and args[1].lstrip('-').isdigit():
            amount = int(args[1])
    elif len(args) == 2 and args[1].lstrip('-').isdigit():
        target_id = message.from_user.id
        amount = int(args[1])
    elif len(args) == 3 and args[2].lstrip('-').isdigit():
        target_id = args[1]
        amount = int(args[2])
        
    if not target_id or amount == 0:
        return await safe_reply(message, "❌ *Gunakan:* `/addcoin [jumlah]` (balas pesan) atau `/addcoin [user_id] [jumlah]`")

    user_data = db.get_user(target_id)
    user_data["coins"] = user_data.get("coins", 0) + amount
    db.update_user(target_id, user_data)
    
    name = user_data.get("first_name") or f"User {target_id}"
    await safe_reply(message, f"✅ Berhasil menambahkan `{amount}` koin ke *{name}*.\n💰 Saldo sekarang: `{user_data['coins']}`")

@bot.message_handler(commands=['setcoin'])
async def set_coin_handler(message):
    """Owner command to set exact coin balance"""
    if not is_owner(message.from_user.id):
        return
    
    args = message.text.split()
    target_id = None
    amount = 0
    
    if message.reply_to_message:
        target_id = message.reply_to_message.from_user.id
        if len(args) > 1 and args[1].isdigit():
            amount = int(args[1])
    elif len(args) == 2 and args[1].isdigit():
        target_id = message.from_user.id
        amount = int(args[1])
    elif len(args) == 3 and args[2].isdigit():
        target_id = args[1]
        amount = int(args[2])
        
    if not target_id:
        return await safe_reply(message, "❌ *Gunakan:* `/setcoin [jumlah]` (balas pesan) atau `/setcoin [user_id] [jumlah]`")

    user_data = db.get_user(target_id)
    user_data["coins"] = amount
    db.update_user(target_id, user_data)
    
    name = user_data.get("first_name") or f"User {target_id}"
    await safe_reply(message, f"✅ Berhasil mengatur saldo *{name}* menjadi `{amount}` koin.")
