import requests
import xml.etree.ElementTree as ET
import logging

logger = logging.getLogger("NewsAPI")

def get_news(category="nasional"):
    """Get news from CNN Indonesia via RSS Feed"""
    # Mapping for categories if needed, for now default to nasional
    url = f"https://www.cnnindonesia.com/{category}/rss"
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, timeout=15)
        if r.status_code == 200:
            root = ET.fromstring(r.content)
            items = root.findall(".//item")[:5]
            
            if not items:
                return {"error": "Tidak ada berita ditemukan."}
            
            msg = f"📰 *BERITA TERBARU (CNN INDONESIA)*\n\n"
            for item in items:
                title = item.find("title").text
                link = item.find("link").text
                msg += f"🔹 [{title}]({link})\n\n"
            
            return {"message": msg}
        else:
            return {"error": f"Gagal mengambil berita (HTTP {r.status_code})."}
    except Exception as e:
        logger.error(f"News Error: {e}")
        return {"error": f"Terjadi kesalahan: {str(e)}"}
