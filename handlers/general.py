from core.bot import bot, safe_reply
from database.db import db
from config import BOT_NAME, VERSION, OWNER_ID
from utils.formatting import get_greeting, get_now
import time

@bot.message_handler(commands=['start', 'help'])
async def start_help(message):
    msg = (
        f"👋 *Halo {message.from_user.first_name}!*\n\n"
        f"🤖 *{BOT_NAME} v{VERSION}*\n"
        f"Saya adalah asisten AI yang siap membantu kamu dengan berbagai fitur seru.\n\n"
        f"📜 Gunakan `/menu` untuk melihat daftar perintah.\n"
        f"💬 Gunakan `/ai [pertanyaan]` untuk mengobrol dengan saya."
    )
    await safe_reply(message, msg)

@bot.message_handler(commands=['menu'])
async def menu_handler(message):
    msg = (
        f"🛠️ *MENU UTAMA {BOT_NAME.upper()}*\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🧠 *Kecerdasan Buatan*\n"
        f"├ `/ai <tanya>` - Tanya AI (LLM)\n"
        f"├ `/resetai` - Hapus memori AI\n"
        f"├ `/setprompt` - Atur Sifat AI\n"
        f"└ `/rank` - Cek Level & XP\n\n"
        f"💰 *Ekonomi & Toko*\n"
        f"├ `/claim` - Klaim Hadiah Harian\n"
        f"├ `/shop` - Toko Item & Booster\n"
        f"├ `/inventory` - Tas Barang Anda\n"
        f"├ `/pay <jumlah>` - Transfer Koin\n"
        f"└ `/top` - Papan Peringkat Global\n\n"
        f"🎮 *Game Seru*\n"
        f"├ `/adventure` - Petualangan RPG (New) ⚔️\n"
        f"├ `/stats` - Profil Hero & Equip 👤\n"
        f"├ `/class` - Pilih Pekerjaan Hero 🎭\n"
        f"├ `/slots <bet>` - Judi Slot 🎰\n"
        f"├ `/dice <bet>` - Duel Dadu 🎲\n"
        f"├ `/hitung` - Cepat Tepat Angka 🧮\n"
        f"├ `/ketik` - Balap Ketik Kalimat ⌨️\n"
        f"├ `/ttt` - Tic Tac Toe\n"
        f"├ `/bj` - Blackjack 🃏\n"
        f"├ `/ludo` - Balap Ludo\n"
        f"└ `/tebakkata` - Susun Kata (+Clue)\n\n"
        f"🎭 *Info & Hiburan*\n"
        f"├ `/gempa` - Info Gempa BMKG\n"
        f"└ `/cuaca <kota>` - Cek Cuaca\n\n"
        f"🕌 *Fitur Islami*\n"
        f"├ `/ayat` - Ayat Al-Qur'an\n"
        f"├ `/sholat <kota>` - Jadwal Sholat\n"
        f"└ `/remindsholat` - On/Off Pengingat\n\n"
        f"👮 *Grup & Admin*\n"
        f"├ `/kick /ban /mute` - Moderasi\n"
        f"├ `/warn` - Peringatan (3x=Ban)\n"
        f"├ `/setrules` - Atur Peraturan\n"
        f"├ `/setwelcome` - Atur Sambutan\n"
        f"├ `/staff` - Daftar Admin\n"
        f"└ `/bc <pesan>` - Broadcast (Owner Only)\n\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🚀 *Version:* `{VERSION}` | ⚡ `/ping`"
    )
    await safe_reply(message, msg)

@bot.message_handler(commands=['ping'])
async def ping(message):
    start = time.time()
    m = await safe_reply(message, "⚡ *Pinging...*")
    end = time.time()
    if m:
        latency = (end - start) * 1000
        await bot.edit_message_text(f"🚀 *PONG!* `{latency:.2f}ms`", m.chat.id, m.message_id, parse_mode='Markdown')

@bot.message_handler(commands=['runtime', 'uptime'])
async def runtime(message):
    await safe_reply(message, f"🕒 *Uptime:* Bot aktif sejak {get_now().strftime('%d/%m/%Y %H:%M:%S')}")
