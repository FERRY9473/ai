import requests

def translate(text, target="id"):
    """Translate text via MyMemory API (free, no key needed for small use)"""
    url = f"https://api.mymemory.translated.net/get?q={requests.utils.quote(text)}&langpair=en|{target}"
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            return r.json().get("responseData", {}).get("translatedText")
        return "❌ Gagal menterjemahkan teks."
    except:
        return "❌ Terjadi kesalahan saat menterjemahkan."

def get_crypto(symbol="btc"):
    """Get crypto price from CoinGecko"""
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={symbol.lower()}&vs_currencies=idr,usd"
    # Mapping for common names
    mapping = {"btc": "bitcoin", "eth": "ethereum", "sol": "solana", "doge": "dogecoin"}
    symbol = mapping.get(symbol.lower(), symbol.lower())
    
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            data = r.json().get(symbol)
            if not data: return f"❌ Aset '{symbol}' tidak ditemukan."
            idr = data.get("idr")
            usd = data.get("usd")
            return f"💰 *HARGA {symbol.upper()}*\n\n💵 *USD:* ${usd:,.2f}\n🇮🇩 *IDR:* Rp{idr:,.0f}"
        return "❌ Gagal mengambil data crypto."
    except Exception as e:
        return f"❌ Terjadi kesalahan: {e}"
