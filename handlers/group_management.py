from core.bot import bot, safe_reply
from database.db import db
from config import ADMIN_ID, OWNER_ID
from functools import wraps
import asyncio
from utils.image_generator import generate_welcome_image, generate_goodbye_image

async def is_admin(chat_id, user_id):
    """Check if a user is an admin in a chat"""
    try:
        if user_id in [ADMIN_ID, OWNER_ID]: return True
        admins = await bot.get_chat_administrators(chat_id)
        for admin in admins:
            if admin.user.id == user_id:
                return True
    except:
        pass
    return False

def group_only(func):
    @wraps(func)
    async def wrapper(message, *args, **kwargs):
        if message.chat.type == 'private':
            return await safe_reply(message, "❌ *FITUR KHUSUS GRUP*\n\nMaaf, fitur ini hanya dapat digunakan di dalam grup.", parse_mode="Markdown")
        return await func(message, *args, **kwargs)
    return wrapper

# Helper for auto-deletion
async def delete_after_delay(chat_id, msg_id, delay=60):
    await asyncio.sleep(delay)
    try:
        await bot.delete_message(chat_id, msg_id)
    except:
        pass

# ══════════════════════════════════════════════
#  WELCOME / GOODBYE
# ══════════════════════════════════════════════
@bot.message_handler(content_types=['new_chat_members'])
async def welcome(message):
    for user in message.new_chat_members:
        if user.is_bot: continue
        
        name = user.first_name
        group_name = message.chat.title
        group_data = db.get_group(message.chat.id)
        
        if group_data.get("welcome_enabled", True):
            # Try to get user profile photo
            pfp_bytes = None
            try:
                photos = await bot.get_user_profile_photos(user.id, limit=1)
                if photos.total_count > 0:
                    file_info = await bot.get_file(photos.photos[0][-1].file_id)
                    pfp_bytes = await bot.download_file(file_info.file_path)
            except:
                pass

            # Generate Image (Async)
            image = await generate_welcome_image(name, group_name, pfp_bytes)

            custom_msg = group_data.get("welcome_msg")
            if custom_msg:
                final_msg = custom_msg.replace("{name}", name).replace("{group}", group_name)
            else:
                final_msg = (
                    f"🏛️ *RESIDENSI BARU: {group_name.upper()}*\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n\n"
                    f"Selamat datang, *{name}*.\n"
                    f"Kehadiranmu telah tercatat dalam sistem kami.\n\n"
                    f"Demi menjaga ketertiban, harap patuhi `/rules` yang berlaku.\n"
                    f"Kontribusi dan integritasmu sangat kami hargai. ✨"
                )

            sent_msg = await bot.send_photo(message.chat.id, image, caption=final_msg, parse_mode="Markdown")
            asyncio.create_task(delete_after_delay(message.chat.id, sent_msg.message_id))

@bot.message_handler(content_types=['left_chat_member'])
async def goodbye(message):
    user = message.left_chat_member
    if user.is_bot: return
    
    name = user.first_name
    group_name = message.chat.title
    
    # Try to get user profile photo
    pfp_bytes = None
    try:
        photos = await bot.get_user_profile_photos(user.id, limit=1)
        if photos.total_count > 0:
            file_info = await bot.get_file(photos.photos[0][-1].file_id)
            pfp_bytes = await bot.download_file(file_info.file_path)
    except:
        pass

    # Generate Goodbye Image (Async)
    image = await generate_goodbye_image(name, group_name, pfp_bytes)
    
    final_msg = (
        f"🍂 *DEPARTUR: {group_name.upper()}*\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"Selamat jalan, *{name}*.\n"
        f"Satu entitas telah meninggalkan sistem kami.\n\n"
        f"Semoga tenang dialam sana. 🕊️"
    )
    
    sent_msg = await bot.send_photo(message.chat.id, image, caption=final_msg, parse_mode="Markdown")
    asyncio.create_task(delete_after_delay(message.chat.id, sent_msg.message_id))

# ══════════════════════════════════════════════
#  ADMIN COMMANDS
# ══════════════════════════════════════════════
@bot.message_handler(commands=['kick'])
@group_only
async def kick_user(message):
    if not await is_admin(message.chat.id, message.from_user.id):
        return await safe_reply(message, "Bukan admin.")
    
    if not message.reply_to_message:
        return await safe_reply(message, "Reply target.")
    
    target_user = message.reply_to_message.from_user
    user_id = target_user.id
    
    # Check if user has protection shield in inventory
    user_data = db.get_user(user_id)
    inventory = user_data.get("inventory", [])
    
    if "protection" in inventory:
        # Remove 1 protection item
        inventory.remove("protection")
        user_data["inventory"] = inventory
        db.update_user(user_id, user_data)
        
        return await safe_reply(message, f"🛡️ *SHIELD AKTIF!*\n\n*{target_user.first_name}* terlindungi oleh _Anti-Kick Shield_. Item telah digunakan dan hancur.", parse_mode="Markdown")

    try:
        await bot.kick_chat_member(message.chat.id, user_id)
        await safe_reply(message, f"{target_user.first_name} ditendang.")
    except Exception as e:
        await safe_reply(message, f"Gagal: {e}")

@bot.message_handler(commands=['ban'])
@group_only
async def ban_user(message):
    if not await is_admin(message.chat.id, message.from_user.id):
        return await safe_reply(message, "Bukan admin.")
    
    if not message.reply_to_message:
        return await safe_reply(message, "Reply target.")
    
    user_id = message.reply_to_message.from_user.id
    try:
        await bot.ban_chat_member(message.chat.id, user_id)
        await safe_reply(message, f"{message.reply_to_message.from_user.first_name} diblokir.")
    except Exception as e:
        await safe_reply(message, f"Gagal: {e}")

@bot.message_handler(commands=['mute'])
@group_only
async def mute_user(message):
    if not await is_admin(message.chat.id, message.from_user.id):
        return await safe_reply(message, "Bukan admin.")
    
    if not message.reply_to_message:
        return await safe_reply(message, "Reply target.")
    
    user_id = message.reply_to_message.from_user.id
    try:
        await bot.restrict_chat_member(message.chat.id, user_id, can_send_messages=False)
        await safe_reply(message, f"{message.reply_to_message.from_user.first_name} dibungkam.")
    except Exception as e:
        await safe_reply(message, f"Gagal: {e}")

@bot.message_handler(commands=['unmute'])
@group_only
async def unmute_user(message):
    if not await is_admin(message.chat.id, message.from_user.id):
        return await safe_reply(message, "Bukan admin.")
    
    if not message.reply_to_message:
        return await safe_reply(message, "Reply target.")
    
    user_id = message.reply_to_message.from_user.id
    try:
        await bot.restrict_chat_member(message.chat.id, user_id, 
                                 can_send_messages=True, 
                                 can_send_media_messages=True, 
                                 can_send_other_messages=True, 
                                 can_add_web_page_previews=True)
        await safe_reply(message, f"{message.reply_to_message.from_user.first_name} dilepas.")
    except Exception as e:
        await safe_reply(message, f"Gagal: {e}")

@bot.message_handler(commands=['warn'])
@group_only
async def warn_user(message):
    if not await is_admin(message.chat.id, message.from_user.id):
        return await safe_reply(message, "Bukan admin.")
    
    if not message.reply_to_message:
        return await safe_reply(message, "Reply target.")
    
    user_id = message.reply_to_message.from_user.id
    user_data = db.get_user(user_id)
    user_data["warns"] = user_data.get("warns", 0) + 1
    db.update_user(user_id, user_data)
    
    if user_data["warns"] >= 3:
        try:
            await bot.ban_chat_member(message.chat.id, user_id)
            await safe_reply(message, f"{message.reply_to_message.from_user.first_name} kena 3 peringatan. Blokir.")
            user_data["warns"] = 0
            db.update_user(user_id, user_data)
        except Exception as e:
            await safe_reply(message, f"Gagal: {e}")
    else:
        await safe_reply(message, f"Peringatan {user_data['warns']}/3 untuk {message.reply_to_message.from_user.first_name}.")

# ══════════════════════════════════════════════
#  GROUP SETTINGS
# ══════════════════════════════════════════════

@bot.message_handler(commands=['setrules'])
@group_only
async def set_rules(message):
    if not await is_admin(message.chat.id, message.from_user.id):
        return await safe_reply(message, "Hanya admin yang bisa mengatur peraturan.")
    
    query = message.text.split(maxsplit=1)
    if len(query) < 2:
        return await safe_reply(message, "Gunakan: /setrules [teks peraturan]")
    
    rules_text = query[1]
    group_data = db.get_group(message.chat.id)
    group_data["rules"] = rules_text
    db.update_group(message.chat.id, group_data)
    
    await safe_reply(message, "Peraturan grup berhasil diperbarui.")

@bot.message_handler(commands=['rules'])
@group_only
async def show_rules(message):
    group_data = db.get_group(message.chat.id)
    rules = group_data.get("rules", "Belum ada peraturan di grup ini.")
    
    msg = f"📜 *PERATURAN GRUP*\n\n{rules}"
    await safe_reply(message, msg)

@bot.message_handler(commands=['setwelcome'])
@group_only
async def set_welcome(message):
    if not await is_admin(message.chat.id, message.from_user.id):
        return await safe_reply(message, "Hanya admin yang bisa mengatur pesan sambutan.")
    
    query = message.text.split(maxsplit=1)
    if len(query) < 2:
        return await safe_reply(message, "Gunakan: /setwelcome [teks]\n\nGunakan {name} untuk nama user dan {group} untuk nama grup.")
    
    welcome_text = query[1]
    group_data = db.get_group(message.chat.id)
    group_data["welcome_msg"] = welcome_text
    db.update_group(message.chat.id, group_data)
    
    await safe_reply(message, "Pesan sambutan berhasil diperbarui.")

@bot.message_handler(commands=['staff', 'admins', 'adminlist'])
@group_only
async def staff_handler(message):
    try:
        admins = await bot.get_chat_administrators(message.chat.id)
        msg = f"👮 *STAFF GRUP {message.chat.title}*\n\n"
        for admin in admins:
            status = "Owner" if admin.status == "creator" else "Admin"
            name = admin.user.first_name
            msg += f"├ {name} ({status})\n"
        await safe_reply(message, msg)
    except Exception as e:
        await safe_reply(message, f"Gagal mengambil daftar staff: {e}")

@bot.message_handler(commands=['pin'])
@group_only
async def pin_message(message):
    if not await is_admin(message.chat.id, message.from_user.id):
        return await safe_reply(message, "Hanya admin yang bisa menyematkan pesan.")
    
    if not message.reply_to_message:
        return await safe_reply(message, "Balas pesan yang ingin disematkan.")
    
    try:
        await bot.pin_chat_message(message.chat.id, message.reply_to_message.message_id)
        await safe_reply(message, "Pesan berhasil disematkan.")
    except Exception as e:
        await safe_reply(message, f"Gagal menyematkan pesan: {e}")

@bot.message_handler(commands=['unpin'])
@group_only
async def unpin_message(message):
    if not await is_admin(message.chat.id, message.from_user.id):
        return await safe_reply(message, "Hanya admin yang bisa melepas sematan pesan.")
    
    try:
        await bot.unpin_chat_message(message.chat.id)
        await safe_reply(message, "Pesan terakhir berhasil dilepas dari sematan.")
    except Exception as e:
        await safe_reply(message, f"Gagal melepas sematan: {e}")
