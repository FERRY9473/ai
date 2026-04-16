from core.bot import bot, safe_reply
from database.db import db
import requests
import random
import logging
from services.prayer import get_jadwal_sholat
from services.bmkg import get_gempa
from services.tools import get_weather, search_wiki
from handlers.group_management import is_admin

@bot.message_handler(commands=['ayat', 'quran'])
async def ayat_handler(message):
    try:
        # Get random verse (1-6236)
        verse_num = random.randint(1, 6236)
        # Using Al-Quran Cloud API
        url = f"https://api.alquran.cloud/v1/ayah/{verse_num}/editions/quran-simple,id.indonesian"
        r = requests.get(url, timeout=5).json()
        
        if r['code'] == 200:
            data = r['data']
            arabic = data[0]['text']
            indo = data[1]['text']
            surah = data[0]['surah']['englishName']
            num_in_surah = data[0]['numberInSurah']
            
            msg = (
                f"📖 *AYAT HARI INI*\n\n"
                f"{arabic}\n\n"
                f"✨ *Artinya:* \"{indo}\"\n\n"
                f"📌 *QS. {surah}: {num_in_surah}*"
            )
            await safe_reply(message, msg)
        else:
            await safe_reply(message, "❌ Gagal mengambil ayat. Coba lagi nanti.")
    except Exception as e:
        logging.error(f"Ayat Error: {e}")
        await safe_reply(message, "⚠️ Sedang ada gangguan koneksi.")

@bot.message_handler(commands=['sholat', 'jadwal'])
async def sholat_handler(message):
    chat_id = message.chat.id
    is_group = message.chat.type in ['group', 'supergroup']
    
    query = message.text.split(maxsplit=1)
    if len(query) > 1:
        city = query[1]
    else:
        # Get city from DB
        data = db.get_group(chat_id) if is_group else db.get_user(chat_id)
        city = data.get("city", "jakarta")
    
    # FIXED: Added await
    res = await get_jadwal_sholat(city)
    if "error" in res:
        await safe_reply(message, res["error"])
    else:
        await safe_reply(message, res["message"])

@bot.message_handler(commands=['gempa'])
async def gempa_handler(message):
    res = await get_gempa()
    if "error" in res:
        await safe_reply(message, res["error"])
    else:
        if res.get("image"):
            await bot.send_photo(message.chat.id, res["image"], caption=res["message"], parse_mode='Markdown')
        else:
            await safe_reply(message, res["message"])

@bot.message_handler(commands=['cuaca', 'weather'])
async def cuaca_handler(message):
    chat_id = message.chat.id
    is_group = message.chat.type in ['group', 'supergroup']
    
    query = message.text.split(maxsplit=1)
    if len(query) > 1:
        city = query[1]
    else:
        # Get city from DB
        data = db.get_group(chat_id) if is_group else db.get_user(chat_id)
        city = data.get("city")
        if not city:
            return await safe_reply(message, "📍 Ketik nama kota. Contoh: `/cuaca Jakarta`\nAtau atur kota utama dengan `/setcity <kota>`")
    
    # FIXED: Added await
    res = await get_weather(city)
    await safe_reply(message, res)

@bot.message_handler(commands=['wiki', 'wikipedia'])
async def wiki_handler(message):
    query = message.text.split(maxsplit=1)
    if len(query) < 2:
        return await safe_reply(message, "🔍 Ketik apa yang ingin dicari. Contoh: `/wiki Indonesia`")
    
    res = await search_wiki(query[1])
    await safe_reply(message, res)

@bot.message_handler(commands=['remindsholat', 'remind'])
async def toggle_remind_sholat(message):
    chat_id = message.chat.id
    is_group = message.chat.type in ['group', 'supergroup']
    
    # If group, must be admin
    if is_group:
        if not await is_admin(chat_id, message.from_user.id):
            return await safe_reply(message, "❌ Hanya admin grup yang bisa mengatur pengingat sholat.")

    query = message.text.split(maxsplit=1)
    if len(query) < 2:
        status = "aktif" if (db.get_group(chat_id) if is_group else db.get_user(chat_id)).get("sholat_remind") else "nonaktif"
        return await safe_reply(message, f"🔔 Pengingat sholat saat ini: *{status.upper()}*\n\nGunakan `/remindsholat on` atau `/remindsholat off` untuk mengubah.")

    cmd = query[1].lower()
    enable = cmd == "on"
    
    if is_group:
        data = db.get_group(chat_id)
        data["sholat_remind"] = enable
        db.update_group(chat_id, data)
    else:
        data = db.get_user(chat_id)
        data["sholat_remind"] = enable
        db.update_user(chat_id, data)
    
    status_text = "DIAKTIFKAN ✅" if enable else "DINONAKTIFKAN ❌"
    await safe_reply(message, f"🔔 Pengingat sholat berhasil {status_text}.\n\nPastikan kota sudah diatur dengan `/setcity <nama_kota>` agar jadwal akurat.")

@bot.message_handler(commands=['setcity', 'setkota'])
async def set_city_handler(message):
    chat_id = message.chat.id
    is_group = message.chat.type in ['group', 'supergroup']
    
    if is_group:
        if not await is_admin(chat_id, message.from_user.id):
            return await safe_reply(message, "❌ Hanya admin grup yang bisa mengatur kota.")

    query = message.text.split(maxsplit=1)
    if len(query) < 2:
        current_city = (db.get_group(chat_id) if is_group else db.get_user(chat_id)).get("city", "jakarta")
        return await safe_reply(message, f"📍 Kota saat ini: *{current_city.upper()}*\n\nGunakan `/setcity <nama_kota>` untuk mengubah.")

    new_city = query[1].lower()
    
    if is_group:
        data = db.get_group(chat_id)
        data["city"] = new_city
        db.update_group(chat_id, data)
    else:
        data = db.get_user(chat_id)
        data["city"] = new_city
        db.update_user(chat_id, data)
    
    await safe_reply(message, f"✅ Kota berhasil diatur ke: *{new_city.upper()}*\nJadwal sholat akan menyesuaikan wilayah ini.")
