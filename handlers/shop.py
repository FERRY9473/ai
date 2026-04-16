from core.bot import bot, safe_reply
from database.db import db
from telebot import types

# Harga disesuaikan dengan ekonomi RPG
SHOP_ITEMS = {
    "xp_booster": {"name": "🚀 XP Booster (Small)", "price": 100, "desc": "+50 XP secara instan"},
    "xp_booster_large": {"name": "🔥 XP Booster (Large)", "price": 400, "desc": "+250 XP secara instan"},
    "rank_card": {"name": "💳 Premium Rank Card", "price": 1000, "desc": "Buka badge PREMIUM di kartu /rank kamu"},
    "protection": {"name": "🛡️ Anti-Kick Shield", "price": 2500, "desc": "Perlindungan otomatis dari 1x tendangan /kick"}
}

def clean_text(text):
    """Bersihkan teks dari karakter Markdown"""
    if not text:
        return ""
    for char in "_*`[]":
        text = text.replace(char, "")
    return text

@bot.message_handler(commands=['shop', 'pasar', 'toko'])
async def show_shop(message):
    user_data = db.get_user(message.from_user.id)
    balance = user_data.get("coins", 0)
    
    text = f"🏪 TOKO APHRODITE\n\nSaldo Anda: {balance} koin\n\nSilakan pilih item yang ingin dibeli:\n"
    
    markup = types.InlineKeyboardMarkup()
    for item_id, info in SHOP_ITEMS.items():
        name = clean_text(info['name'])
        text += f"\n• {info['name']}\n└ 💰 {info['price']} koin\n   {info['desc']}"
        markup.add(types.InlineKeyboardButton(f"Beli {name}", callback_data=f"buy_{item_id}"))
    
    await safe_reply(message, text, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("buy_"))
async def shop_buy(call):
    item_id = call.data.replace("buy_", "")
    if item_id not in SHOP_ITEMS:
        return await bot.answer_callback_query(call.id, "Item tidak ditemukan!")
    
    item = SHOP_ITEMS[item_id]
    user_id = call.from_user.id
    user_data = db.get_user(user_id)
    
    if user_data.get("coins", 0) < item['price']:
        return await bot.answer_callback_query(call.id, "❌ Koin tidak cukup!", show_alert=True)
    
    user_data["coins"] -= item['price']
    
    if item_id == "xp_booster":
        user_data["xp"] = user_data.get("xp", 0) + 50
        msg = f"✅ Berhasil membeli {item['name']}! XP Anda bertambah 50."
    elif item_id == "xp_booster_large":
        user_data["xp"] = user_data.get("xp", 0) + 250
        msg = f"✅ Berhasil membeli {item['name']}! XP Anda bertambah 250."
    else:
        inventory = user_data.get("inventory", [])
        inventory.append(item_id)
        user_data["inventory"] = inventory
        msg = f"✅ Berhasil membeli {item['name']}! Item telah ditambahkan ke /inventory."
    
    new_level = (user_data["xp"] // 100) + 1
    user_data["level"] = new_level
    
    db.update_user(user_id, user_data)
    
    await bot.answer_callback_query(call.id, "Pembelian Berhasil!")
    await bot.edit_message_text(
        f"{msg}\n\nSaldo sisa: {user_data['coins']} koin",
        call.message.chat.id,
        call.message.message_id
    )

@bot.message_handler(commands=['inventory', 'tas'])
async def show_inventory(message):
    user_id = message.from_user.id
    user_data = db.get_user(user_id)
    inventory = user_data.get("inventory", [])
    
    if not inventory:
        return await safe_reply(message, "🎒 TAS ANDA\n\nTas Anda kosong. Belanja di /shop yuk!")
    
    from collections import Counter
    counts = Counter(inventory)
    
    text = "🎒 TAS ANDA\n\n"
    markup = types.InlineKeyboardMarkup()
    
    for item_id, count in counts.items():
        info = SHOP_ITEMS.get(item_id, {})
        name = info.get("name", item_id)
        clean_name = clean_text(name)
        text += f"• {clean_name} (x{count})\n"
        markup.add(types.InlineKeyboardButton(f"Gunakan {clean_name}", callback_data=f"use_{item_id}"))
    
    await safe_reply(message, text, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("use_"))
async def use_item_callback(call):
    item_id = call.data.replace("use_", "")
    user_id = call.from_user.id
    user_data = db.get_user(user_id)
    inventory = user_data.get("inventory", [])
    
    if item_id not in inventory:
        return await bot.answer_callback_query(call.id, "❌ Item tidak ada di tas!", show_alert=True)
    
    info = SHOP_ITEMS.get(item_id, {})
    name = info.get("name", "Item")

    if item_id == "protection":
        await bot.answer_callback_query(call.id, "🛡️ Shield aktif otomatis saat kamu dikick!", show_alert=True)
    elif item_id == "rank_card":
        await bot.answer_callback_query(call.id, "💳 Badge Premium aktif otomatis di /rank!", show_alert=True)
    else:
        await bot.answer_callback_query(call.id, f"✅ Berhasil menggunakan {name}!", show_alert=True)

@bot.message_handler(commands=['use', 'pakai'])
async def use_item(message):
    user_id = message.from_user.id
    user_data = db.get_user(user_id)
    inventory = user_data.get("inventory", [])
    
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        return await safe_reply(message, "❌ Gunakan: /use [nama_item]")
    
    input_item = args[1].lower()
    item_to_use = None
    
    for item_id, info in SHOP_ITEMS.items():
        if input_item in info['name'].lower() or input_item == item_id:
            item_to_use = item_id
            break
            
    if not item_to_use or item_to_use not in inventory:
        return await safe_reply(message, "❌ Item tidak ditemukan di tas kamu!")

    if item_to_use == "protection":
        return await safe_reply(message, "🛡️ Anti-Kick Shield aktif secara otomatis saat kamu akan ditendang. Tidak perlu digunakan manual.")
    if item_to_use == "rank_card":
        return await safe_reply(message, "💳 Premium Rank Card aktif secara otomatis di profil kamu. Cek di /rank!")