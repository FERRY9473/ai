import httpx
import logging

logger = logging.getLogger("BMKG")

async def get_gempa():
    """Get latest earthquake info from BMKG (Async)"""
    url = "https://data.bmkg.go.id/DataMKG/TEWS/autogempa.json"
    try:
        async with httpx.AsyncClient() as client:
            r = await client.get(url, timeout=10)
            if r.status_code == 200:
                data = r.json().get("Infogempa", {}).get("gempa", {})
                msg = (
                    f"🚨 *INFO GEMPA TERBARU*\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n"
                    f"📅 *Tanggal:* {data.get('Tanggal')}\n"
                    f"⏰ *Jam:* {data.get('Jam')}\n"
                    f"📏 *Magnitudo:* `{data.get('Magnitude')}` SR\n"
                    f"🌊 *Kedalaman:* `{data.get('Kedalaman')}`\n"
                    f"📍 *Koordinat:* `{data.get('Coordinates')}`\n"
                    f"🗺 *Wilayah:* {data.get('Wilayah')}\n"
                    f"⚠️ *Potensi:* {data.get('Potensi')}\n"
                    f"🏢 *Dirasakan:* {data.get('Dirasakan') or '-'}\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n"
                    f"✨ _Tetap waspada dan stay safe ya! 🙏_"
                )
                # Image URL
                shakemap_name = data.get('Shakemap')
                image_url = f"https://data.bmkg.go.id/DataMKG/TEWS/{shakemap_name}" if shakemap_name else None
                     
                return {"message": msg, "image": image_url}
            return {"error": f"❌ Gagal mengambil data BMKG (HTTP {r.status_code})."}
    except Exception as e:
        logger.error(f"BMKG Error: {e}")
        return {"error": f"⚠️ Kesalahan API BMKG: {str(e)}"}
