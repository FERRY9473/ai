from core.bot import bot, safe_reply
from database.db import db
from telebot import types
import asyncio

def get_rank_emoji(rank):
    if rank == 1: return "🥇"
    if rank == 2: return "🥈"
    if rank == 3: return "🥉"
    return f"{rank}."

def generate_leaderboard_text(users_list, metric, title, my_rank=None):
    text = f"🌍 *{title}* ({metric.upper()})\n\n"
    if not users_list:
        text += "_Belum ada data._"
        return text

    for i, user in enumerate(users_list[:10], 1):
        emoji = get_rank_emoji(i)
        text += f"{emoji} *{user['name']}* — `{user['val']}`\n"
    
    if my_rank:
        text += f"\n──────────────\n👤 *Rank Anda:* `{my_rank}`"
    
    return text

def get_leaderboard_markup(scope="global"):
    markup = types.InlineKeyboardMarkup()
    btn_xp = types.InlineKeyboardButton("✨ XP", callback_data=f"lb_{scope}_xp")
    btn_coins = types.InlineKeyboardButton("💰 Coins", callback_data=f"lb_{scope}_coins")
    btn_level = types.InlineKeyboardButton("⭐️ Level", callback_data=f"lb_{scope}_level")
    markup.row(btn_xp, btn_coins, btn_level)
    return markup

@bot.message_handler(commands=['top', 'leaderboard'])
async def global_leaderboard(message):
    """Global leaderboard with interactive buttons"""
    args = message.text.split()
    metric = "xp"
    if len(args) > 1:
        if args[1].lower() in ["xp", "coins", "level"]:
            metric = args[1].lower()

    all_users = []
    for user_id, user_data in db.users.items():
        name = user_data.get("first_name") or f"User {user_id}"
        all_users.append({
            "id": user_id,
            "name": name,
            "val": user_data.get(metric, 0)
        })

    all_users.sort(key=lambda x: x['val'], reverse=True)
    
    my_rank = 0
    for i, u in enumerate(all_users, 1):
        if str(u['id']) == str(message.from_user.id):
            my_rank = i
            break

    text = generate_leaderboard_text(all_users, metric, "PAPAN PERINGKAT GLOBAL", my_rank)
    await safe_reply(message, text, reply_markup=get_leaderboard_markup("global"), parse_mode="Markdown")

@bot.message_handler(commands=['topgroup', 'leaderboardgroup'])
async def group_leaderboard(message):
    """Group leaderboard with interactive buttons"""
    if message.chat.type == 'private':
        return await safe_reply(message, "Gunakan perintah ini di grup!")

    chat_id = message.chat.id
    group_id_str = str(chat_id)
    args = message.text.split()
    metric = "xp"
    if len(args) > 1:
        if args[1].lower() in ["xp", "coins", "level"]:
            metric = args[1].lower()

    user_ids = db.group_users.get(group_id_str, [])
    group_users = []
    for uid in user_ids:
        user_data = db.get_user(uid)
        name = user_data.get("first_name") or f"User {uid}"
        group_users.append({
            "id": uid,
            "name": name,
            "val": user_data.get(metric, 0)
        })

    group_users.sort(key=lambda x: x['val'], reverse=True)
    
    my_rank = 0
    for i, u in enumerate(group_users, 1):
        if str(u['id']) == str(message.from_user.id):
            my_rank = i
            break

    text = generate_leaderboard_text(group_users, metric, "PAPAN PERINGKAT GRUP", my_rank)
    await safe_reply(message, text, reply_markup=get_leaderboard_markup("group"), parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith("lb_"))
async def leaderboard_callback(call):
    """Handle metric switching via callback buttons"""
    try:
        _, scope, metric = call.data.split("_")
        
        if scope == "global":
            all_users = []
            for user_id, user_data in db.users.items():
                name = user_data.get("first_name") or f"User {user_id}"
                all_users.append({
                    "id": user_id,
                    "name": name,
                    "val": user_data.get(metric, 0)
                })
            all_users.sort(key=lambda x: x['val'], reverse=True)
            my_rank = 0
            for i, u in enumerate(all_users, 1):
                if str(u['id']) == str(call.from_user.id):
                    my_rank = i
                    break
            text = generate_leaderboard_text(all_users, metric, "PAPAN PERINGKAT GLOBAL", my_rank)
        else:
            chat_id = call.message.chat.id
            group_id_str = str(chat_id)
            user_ids = db.group_users.get(group_id_str, [])
            group_users = []
            for uid in user_ids:
                user_data = db.get_user(uid)
                name = user_data.get("first_name") or f"User {uid}"
                group_users.append({
                    "id": uid,
                    "name": name,
                    "val": user_data.get(metric, 0)
                })
            group_users.sort(key=lambda x: x['val'], reverse=True)
            my_rank = 0
            for i, u in enumerate(group_users, 1):
                if str(u['id']) == str(call.from_user.id):
                    my_rank = i
                    break
            text = generate_leaderboard_text(group_users, metric, "PAPAN PERINGKAT GRUP", my_rank)

        await bot.edit_message_text(
            text, 
            call.message.chat.id, 
            call.message.message_id, 
            reply_markup=get_leaderboard_markup(scope),
            parse_mode="Markdown"
        )
    except Exception as e:
        # Avoid error on repeated clicks or same content
        pass
    finally:
        await bot.answer_callback_query(call.id)

@bot.message_handler(commands=['rank', 'level', 'me', 'profile', 'id'])
async def show_rank(message):
    """Show current user rank and stats with visual profile card"""
    from utils.image_generator import generate_profile_card
    
    user_id = message.from_user.id
    user_data = db.get_user(user_id)
    
    xp = user_data.get("xp", 0)
    level = user_data.get("level", 1)
    coins = user_data.get("coins", 0)
    name = user_data.get("first_name") or message.from_user.first_name or "User"
    
    next_level_xp = level * 100
    
    # Calculate Global Rank
    all_users = []
    for uid, data in db.users.items():
        all_users.append({"id": uid, "xp": data.get("xp", 0)})
    all_users.sort(key=lambda x: x['xp'], reverse=True)
    
    my_rank = 0
    for i, u in enumerate(all_users, 1):
        if str(u['id']) == str(user_id):
            my_rank = i
            break

    # Send typing action
    await bot.send_chat_action(message.chat.id, 'upload_photo')

    # Try to get profile photo
    pfp_bytes = None
    try:
        photos = await bot.get_user_profile_photos(user_id, limit=1)
        if photos.total_count > 0:
            file_info = await bot.get_file(photos.photos[0][-1].file_id)
            pfp_bytes = await bot.download_file(file_info.file_path)
    except:
        pass

    # Check if user has premium badge item
    is_premium = "rank_card" in user_data.get("inventory", [])

    try:
        # Generate and Send Image
        image = await generate_profile_card(name, level, xp, next_level_xp, coins, my_rank, pfp_bytes, is_premium=is_premium)
        await bot.send_photo(message.chat.id, image)
    except Exception as e:
        # Fallback to text if image generation fails
        progress_xp = xp - ((level - 1) * 100)
        progress = max(0, min(1, progress_xp / 100))
        progress_bar = "▰" * int(progress * 10) + "▱" * (10 - int(progress * 10))
        
        text = f"👤 *PROFIL ANDA*\n\n⭐️ Level: `{level}`\n✨ XP: `{xp} / {next_level_xp}`\n💰 Koin: `{coins}`\n🏆 Rank: `#{my_rank}`\n\n`{progress_bar}` ({int(progress*100)}%)"
        await safe_reply(message, text, parse_mode="Markdown")

@bot.message_handler(commands=['pay', 'transfer'])
async def pay_coins(message):
    """Transfer coins to another user"""
    sender_id = message.from_user.id
    args = message.text.split()
    
    # 1. Determine target user and amount
    target_user_id = None
    amount = 0
    
    if message.reply_to_message:
        target_user_id = message.reply_to_message.from_user.id
        if len(args) > 1 and args[1].isdigit():
            amount = int(args[1])
    elif len(args) > 2 and args[2].isdigit():
        # Try to find user by username (this is hard without a username-to-id mapping)
        # For now, we only support Reply or ID if we want to be safe
        # Or we can just support /pay [id] [amount]
        if args[1].isdigit():
            target_user_id = int(args[1])
            amount = int(args[2])
    
    if not target_user_id or amount <= 0:
        return await safe_reply(message, "Gunakan: Balas pesan target dengan `/pay [jumlah]` atau gunakan `/pay [user_id] [jumlah]`")

    if target_user_id == sender_id:
        return await safe_reply(message, "Kamu tidak bisa mengirim koin ke diri sendiri!")

    # 2. Check sender balance
    sender_data = db.get_user(sender_id)
    if sender_data.get("coins", 0) < amount:
        return await safe_reply(message, f"Koin tidak cukup! Saldo: `{sender_data.get('coins', 0)}`")

    # 3. Perform transfer
    target_data = db.get_user(target_user_id)
    
    sender_data["coins"] -= amount
    target_data["coins"] = target_data.get("coins", 0) + amount
    
    db.update_user(sender_id, sender_data)
    db.update_user(target_user_id, target_data)
    
    target_name = target_data.get("first_name") or f"User {target_user_id}"
    await safe_reply(message, f"✅ Berhasil mengirim `{amount}` koin ke *{target_name}*!")

