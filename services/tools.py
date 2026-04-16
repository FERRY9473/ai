import httpx
import urllib.parse
import logging
from datetime import datetime

logger = logging.getLogger("ToolsAPI")

async def search_wiki(query):
    """Search Wikipedia Indonesia with fuzzy/search logic (Async)"""
    headers = {"User-Agent": "AphroditeBot/12.0 (https://t.me/myaipersonality_bot)"}
    try:
        async with httpx.AsyncClient(headers=headers, follow_redirects=True) as client:
            search_url = f"https://id.wikipedia.org/w/api.php?action=query&list=search&srsearch={urllib.parse.quote(query)}&format=json"
            s_resp = await client.get(search_url, timeout=10)
            
            if s_resp.status_code != 200:
                return f"❌ Gagal mencari di Wikipedia (HTTP {s_resp.status_code})."
                
            try:
                s_data = s_resp.json()
            except Exception:
                logger.error(f"Wiki Search JSON Error: {s_resp.text[:100]}")
                return "❌ Gagal mengurai data pencarian Wikipedia."
            search_results = s_data.get("query", {}).get("search", [])
            
            if not search_results:
                return f"❌ Tidak ada hasil untuk '{query}' di Wikipedia Indonesia."
            
            best_title = search_results[0]['title']
            safe_title = best_title.replace(" ", "_")
            encoded_title = urllib.parse.quote(safe_title)
            url = f"https://id.wikipedia.org/api/rest_v1/page/summary/{encoded_title}"
            
            r = await client.get(url, timeout=15)
            if r.status_code == 200:
                data = r.json()
                title = data.get("displaytitle") or data.get("title")
                extract = data.get("extract")
                link = data.get("content_urls", {}).get("desktop", {}).get("page")
                
                if not extract: return f"❌ Ringkasan tidak tersedia untuk '{title}'."
                if len(extract) > 1000: extract = extract[:1000] + "..."
                
                return f"📖 *WIKIPEDIA: {title}*\n\n{extract}\n\n🔗 [Baca selengkapnya]({link})"
            
            return f"❌ Gagal mengambil ringkasan untuk '{best_title}' (HTTP {r.status_code})."
    except Exception as e:
        logger.error(f"Wiki Error: {e}")
        return f"❌ Terjadi kesalahan: {str(e)}"

async def get_kbbi(query):
    """Search KBBI (via Wiktionary Indonesia as alternative) (Async)"""
    encoded_query = urllib.parse.quote(query)
    url = f"https://id.wiktionary.org/w/api.php?action=query&titles={encoded_query}&format=json&prop=extracts&explaintext=1"
    headers = {"User-Agent": "AphroditeBot/12.0"}
    try:
        async with httpx.AsyncClient(headers=headers, follow_redirects=True) as client:
            r = await client.get(url, timeout=15)
            if r.status_code == 200:
                data = r.json()
                pages = data.get("query", {}).get("pages", {})
                page_id = next(iter(pages))
                if page_id == "-1": return "❌ Kata tidak ditemukan di Wiktionary/KBBI."
                
                extract = pages[page_id].get("extract", "")
                if "== Bahasa Indonesia ==" in extract:
                    extract = extract.split("== Bahasa Indonesia ==")[1].split("==")[0].strip()
                
                extract = extract.replace("Definisi dari istilah ini memerlukan penerangan lebih lanjut (jangan salin tempel KBBI). Tolong bantu tambahkan definisinya, kemudian hapus teks {{rfdef}}.", "").strip()
                if not extract: return "❌ Definisi tidak tersedia."
                
                return f"📚 *ARTI KATA: {query.upper()}*\n\n{extract[:1000]}"
            return f"❌ Gagal menghubungi server (HTTP {r.status_code})."
    except Exception as e:
        logger.error(f"KBBI Error: {e}")
        return f"❌ Terjadi kesalahan saat mencari arti kata."

async def get_weather(city):
    """Get current weather and 3-day forecast via Open-Meteo (Async)"""
    encoded_city = urllib.parse.quote(city)
    geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={encoded_city}&count=1&language=id&format=json"
    try:
        async with httpx.AsyncClient(follow_redirects=True) as client:
            gr_resp = await client.get(geo_url, timeout=15)
            if gr_resp.status_code != 200:
                return f"❌ Gagal mencari lokasi '{city}' (HTTP {gr_resp.status_code})."
            
            gr = gr_resp.json()
            if not gr.get("results"): return f"❌ Kota '{city}' tidak ditemukan."
            res = gr["results"][0]
            lat, lon = res["latitude"], res["longitude"]
            name = res["name"]
            admin1 = res.get("admin1", "")
            country = res.get("country", "")
            
            wx_url = (
                f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
                f"&current=temperature_2m,relative_humidity_2m,apparent_temperature,weather_code,wind_speed_10m"
                f"&daily=weather_code,temperature_2m_max,temperature_2m_min&timezone=auto&forecast_days=3"
            )
            wr_resp = await client.get(wx_url, timeout=15)
            if wr_resp.status_code != 200:
                return f"❌ Gagal mengambil data cuaca (HTTP {wr_resp.status_code})."
                
            wr = wr_resp.json()
            curr = wr["current"]
            daily = wr["daily"]
            
            def get_condition(code):
                mapping = {
                    0: "Cerah ☀️", 1: "Cerah Berawan 🌤", 2: "Berawan ⛅", 3: "Mendung ☁️",
                    45: "Berkabut 🌫", 48: "Rime Fog 🌫",
                    51: "Gerimis Ringan 🌦", 53: "Gerimis Sedang 🌦", 55: "Gerimis Lebat 🌦",
                    61: "Hujan Ringan 🌧", 63: "Hujan Sedang 🌧", 65: "Hujan Lebat 🌧",
                    71: "Salju Ringan ❄️", 73: "Salju Sedang ❄️", 75: "Salju Lebat ❄️",
                    80: "Hujan Showers Ringan 🌦", 81: "Hujan Showers Sedang 🌦", 82: "Hujan Showers Kuat 🌧",
                    95: "Badai Petir ⛈", 96: "Badai Petir & Es ⛈", 99: "Badai Petir Berat ⛈"
                }
                return mapping.get(code, "Tidak diketahui")

            temp = curr["temperature_2m"]
            feel = curr["apparent_temperature"]
            hum = curr["relative_humidity_2m"]
            wind = curr["wind_speed_10m"]
            condition = get_condition(curr["weather_code"])
            
            location_str = f"{name}"
            if admin1: location_str += f", {admin1}"
            if country: location_str += f", {country}"

            msg = (
                f"🌡 *CUACA SAAT INI: {name.upper()}*\n"
                f"📍 _{location_str}_\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"☁️ *Kondisi:* {condition}\n"
                f"🌡 *Suhu:* {temp}°C (Terasa {feel}°C)\n"
                f"💧 *Kelembapan:* {hum}%\n"
                f"💨 *Angin:* {wind} km/jam\n\n"
                f"📅 *PRAKIRAAN 3 HARI KE DEPAN:*\n"
            )
            
            for i in range(len(daily["time"])):
                date = daily["time"][i]
                try:
                    dt_obj = datetime.strptime(date, "%Y-%m-%d")
                    date_str = dt_obj.strftime("%d %b")
                except:
                    date_str = date
                d_cond = get_condition(daily["weather_code"][i])
                d_max = daily["temperature_2m_max"][i]
                d_min = daily["temperature_2m_min"][i]
                msg += f"├ {date_str}: {d_cond} ({d_min}° - {d_max}°)\n"
            msg += "━━━━━━━━━━━━━━━━━━━━"
            return msg
    except Exception as e:
        logger.error(f"Weather Error: {e}")
        return f"❌ Gagal mengambil data cuaca: {e}"
