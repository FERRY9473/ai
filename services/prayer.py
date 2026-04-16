import httpx
import urllib.parse
from utils.formatting import get_now
import logging
from datetime import datetime

logger = logging.getLogger("PrayerAPI")

async def get_jadwal_sholat(city="jakarta"):
    """Get prayer times from Aladhan API (Async version)"""
    now = get_now()
    encoded_city = urllib.parse.quote(city)
    url = f"https://api.aladhan.com/v1/timingsByCity/{now.strftime('%d-%m-%Y')}?city={encoded_city}&country=Indonesia&method=2"
    try:
        async with httpx.AsyncClient() as client:
            r = await client.get(url, timeout=15)
            if r.status_code == 200:
                data = r.json().get("data", {}).get("timings", {})
                if not data:
                    return {"error": f"❌ Data jadwal sholat untuk '{city}' tidak ditemukan."}
                
                msg = (
                    f"🕌 *JADWAL SHOLAT - {city.upper()}*\n"
                    f"📅 *Tanggal:* {now.strftime('%d %B %Y')}\n\n"
                    f"🌅 *Imsak:* `{data.get('Imsak')}`\n"
                    f"⛅ *Subuh:* `{data.get('Fajr')}`\n"
                    f"☀️ *Terbit:* `{data.get('Sunrise')}`\n"
                    f"🕛 *Dzuhur:* `{data.get('Dhuhr')}`\n"
                    f"🕒 *Ashar:* `{data.get('Asr')}`\n"
                    f"🌇 *Maghrib:* `{data.get('Maghrib')}`\n"
                    f"🌃 *Isya:* `{data.get('Isha')}`\n\n"
                    f"✨ _Semoga amal ibadah kita diterima Allah SWT. Amin. 🙏_"
                )
                return {"message": msg}
            else:
                logger.error(f"Prayer API error {r.status_code}: {r.text}")
                return {"error": f"❌ Gagal mengambil jadwal sholat (HTTP {r.status_code})."}
    except Exception as e:
        logger.error(f"Prayer API Exception: {e}")
        return {"error": f"⚠️ Kesalahan koneksi: {e}"}
