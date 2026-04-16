import httpx
import logging

logger = logging.getLogger("BMKG")

async def get_gempa():
    """Get latest earthquake info from BMKG"""
    url = "https://data.bmkg.go.id/DataMKG/TEWS/autogempa.json"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        async with httpx.AsyncClient(follow_redirects=True, verify=False) as client:
            r = await client.get(url, headers=headers, timeout=15)
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
                    f"━━━━━━━━━━━━━━━━━━━━\n"
                    f"✨ _Sumber: BMKG Indonesia_"
                )
                shakemap_name = data.get('Shakemap')
                image_url = f"https://data.bmkg.go.id/DataMKG/TEWS/{shakemap_name}" if shakemap_name else None
                return {"message": msg, "image": image_url}
            return {"error": "❌ Gagal mengambil data gempa BMKG."}
    except Exception as e:
        logger.error(f"BMKG Gempa Error: {e}")
        return {"error": "⚠️ API Gempa BMKG sedang bermasalah."}

def get_wind_dir(deg):
    """Convert wind degree to direction string"""
    directions = ["Utara", "Timur Laut", "Timur", "Tenggara", "Selatan", "Barat Daya", "Barat", "Barat Laut"]
    idx = int((deg + 22.5) / 45) % 8
    return directions[idx]

async def get_weather(city_name):
    """Get highly detailed weather forecast for Indonesia only"""
    city = city_name.lower().strip()
    
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=25) as client:
            # 1. Geocoding
            geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=5&language=id&format=json"
            geo_resp = await client.get(geo_url)
            geo_data = geo_resp.json()
            
            results = geo_data.get("results", [])
            area_found = None
            for res in results:
                if res.get("country_code") == "ID":
                    area_found = res
                    break
            
            if not area_found:
                return {"error": f"❌ Kota '{city_name}' tidak ditemukan di wilayah Indonesia."}
            
            lat, lon = area_found["latitude"], area_found["longitude"]
            full_name = f"{area_found.get('name')}, {area_found.get('admin1', '')} 🇮🇩"

            # 2. Detailed Weather API Call
            params = [
                "temperature_2m", "relative_humidity_2m", "apparent_temperature",
                "is_day", "precipitation", "rain", "showers", "snowfall",
                "weather_code", "cloud_cover", "pressure_msl", "surface_pressure",
                "wind_speed_10m", "wind_direction_10m", "wind_gusts_10m"
            ]
            weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current={','.join(params)}&timezone=auto"
            w_resp = await client.get(weather_url)
            w_data = w_resp.json()
            
            c = w_data.get("current", {})
            
            # Weather Code Mapping
            weather_codes = {
                0: "Cerah ☀️", 1: "Cerah Berawan 🌤", 2: "Berawan ⛅", 3: "Mendung ☁️",
                45: "Kabut 🌫", 48: "Kabut Rime 🌫",
                51: "Gerimis Ringan 🌦", 53: "Gerimis Sedang 🌦", 55: "Gerimis Lebat 🌦",
                61: "Hujan Ringan 🌧", 63: "Hujan Sedang 🌧", 65: "Hujan Lebat 🌧",
                80: "Hujan Lokal 🌦", 81: "Hujan Lokal Lebat 🌦", 82: "Hujan Badai ⛈",
                95: "Hujan Petir ⚡", 96: "Hujan Petir Ringan ⚡", 99: "Hujan Petir Lebat ⚡"
            }
            condition = weather_codes.get(c.get("weather_code"), "Berawan ☁️")
            day_night = "Siang Hari ☀️" if c.get("is_day") else "Malam Hari 🌙"
            wind_dir = get_wind_dir(c.get("wind_direction_10m", 0))

            msg = (
                f"🇮🇩 *DETAIL CUACA INDONESIA*\n"
                f"📍 *Lokasi:* {full_name}\n"
                f"🕒 *Waktu:* {day_night}\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"🌡 *Suhu Sekarang:* `{c.get('temperature_2m')}°C` \n"
                f"🤔 *Terasa Seperti:* `{c.get('apparent_temperature')}°C` \n"
                f"☁️ *Kondisi:* {condition}\n"
                f"💧 *Kelembaban:* `{c.get('relative_humidity_2m')}%` \n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"🌬 *Detail Angin & Udara:*\n"
                f"├ *Kecepatan:* `{c.get('wind_speed_10m')} km/jam` \n"
                f"├ *Hembusan:* `{c.get('wind_gusts_10m')} km/jam` \n"
                f"├ *Arah:* `{wind_dir} ({c.get('wind_direction_10m')}°)` \n"
                f"└ *Tekanan:* `{c.get('surface_pressure')} hPa` \n\n"
                f"🌧 *Detail Presipitasi:*\n"
                f"├ *Curah Hujan:* `{c.get('precipitation')} mm` \n"
                f"└ *Tutupan Awan:* `{c.get('cloud_cover')}%` \n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"✨ _Data real-time Open-Meteo & Satelit._"
            )
            return {"message": msg}

    except Exception as e:
        logger.error(f"Weather Detailed Error: {e}")
        return {"error": "⚠️ Gagal mengambil detail cuaca. Coba lagi nanti."}
