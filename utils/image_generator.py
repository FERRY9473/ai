from PIL import Image, ImageDraw, ImageFont, ImageOps
import io
import os
import httpx
import asyncio
from pilmoji import Pilmoji
from functools import partial

# Path font Noto Sans
FONT_PATH = "/root/ai/database/fonts/NotoSans-Bold.ttf"
if not os.path.exists(FONT_PATH):
    FONT_PATH = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"

# Cache & Client Optimization
bg_cache = {}
http_client = httpx.AsyncClient(timeout=15)

async def get_background(url, width, height):
    """Fetch background image from URL with caching and optimization"""
    if url in bg_cache:
        return bg_cache[url].copy()
    try:
        resp = await http_client.get(url)
        if resp.status_code == 200:
            def process():
                img = Image.open(io.BytesIO(resp.content)).convert("RGB")
                img = ImageOps.fit(img, (width, height), centering=(0.5, 0.5))
                overlay = Image.new('RGBA', (width, height), (0, 0, 0, 100))
                img.paste(overlay, (0, 0), overlay)
                return img
            img = await asyncio.to_thread(process)
            bg_cache[url] = img
            return img.copy()
    except Exception as e:
        print(f"Error fetching background: {e}")
    return Image.new('RGB', (width, height), color='#0F172A')

def _draw_profile_sync(base, user_name, level, xp, next_level_xp, coins, rank, profile_photo_bytes, is_premium, rpg_data):
    """Synchronous part of profile card generation with RPG stats (updated)"""
    width, height = base.size
    overlay = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    
    accent_color = '#00D2FF'
    gold_color = '#FFD700'
    text_main = '#FFFFFF'
    text_sub = '#94A3B8'
    hp_color = '#FF4B2B'
    
    box_padding = 30
    overlay_draw.rounded_rectangle([box_padding, box_padding, width - box_padding, height - box_padding], radius=25, fill=(15, 23, 42, 200))
    
    base = Image.alpha_composite(base.convert('RGBA'), overlay)
    
    try:
        font_name = ImageFont.truetype(FONT_PATH, 38)
        font_stats = ImageFont.truetype(FONT_PATH, 20)
        font_level_val = ImageFont.truetype(FONT_PATH, 55)
        font_label = ImageFont.truetype(FONT_PATH, 14)
    except:
        font_name = font_stats = font_level_val = font_label = ImageFont.load_default()

    with Pilmoji(base) as pilmoji:
        pfp_size = 150
        pfp_x, pfp_y = box_padding + 30, box_padding + 30
        content_x = pfp_x + pfp_size + 30
        
        # User Name & Rank
        pilmoji.text((content_x, pfp_y), user_name[:15], font=font_name, fill=text_main)
        pilmoji.text((content_x, pfp_y + 45), f"RANK #{rank}", font=font_stats, fill=gold_color)
        
        # RPG Class Badge
        r_class = rpg_data.get("class", "Novice").upper()
        badge_w, badge_h = 120, 25
        pilmoji.draw.rounded_rectangle([content_x, pfp_y + 80, content_x+badge_w, pfp_y+80+badge_h], radius=5, fill=accent_color)
        pilmoji.text((content_x + badge_w//2, pfp_y + 80 + badge_h//2), r_class, font=font_stats, fill='black', anchor="mm")

        # Level Info (Right Side)
        level_x = width - box_padding - 80
        pilmoji.text((level_x, pfp_y + 15), "LEVEL", font=font_label, fill=text_sub, anchor="mm")
        pilmoji.text((level_x, pfp_y + 65), str(level), font=font_level_val, fill=accent_color, anchor="mm")
        pilmoji.text((level_x, pfp_y + 115), f"💰 {coins}", font=font_stats, fill=gold_color, anchor="mm")

        # --- PROGRESS BARS (HP & XP) ---
        bar_x = pfp_x
        bar_w = width - (box_padding * 2) - 60
        
        # HP Bar
        hp_y = pfp_y + pfp_size + 30
        hp_cur, hp_max = rpg_data.get("hp", 100), rpg_data.get("max_hp", 100)
        hp_ratio = min(1, hp_cur / hp_max) if hp_max > 0 else 0
        pilmoji.text((bar_x, hp_y - 20), f"HEALTH: {hp_cur}/{hp_max}", font=font_label, fill=text_sub)
        pilmoji.draw.rounded_rectangle([bar_x, hp_y, bar_x+bar_w, hp_y+15], radius=8, fill=(30, 41, 59, 150))
        if hp_ratio > 0:
            pilmoji.draw.rounded_rectangle([bar_x, hp_y, bar_x + (bar_w * hp_ratio), hp_y+15], radius=8, fill=hp_color)

        # XP Bar
        xp_y = hp_y + 50
        xp_ratio = min(1, xp / next_level_xp) if next_level_xp > 0 else 0
        pilmoji.text((bar_x, xp_y - 20), f"EXPERIENCE: {xp}/{next_level_xp}", font=font_label, fill=text_sub)
        pilmoji.draw.rounded_rectangle([bar_x, xp_y, bar_x+bar_w, xp_y+15], radius=8, fill=(30, 41, 59, 150))
        if xp_ratio > 0:
            pilmoji.draw.rounded_rectangle([bar_x, xp_y, bar_x + (bar_w * xp_ratio), xp_y+15], radius=8, fill=accent_color)

        # ATK, DEF, STAMINA (Bottom) – gunakan final values jika tersedia
        stats_y = xp_y + 40
        # Final stats (sudah termasuk equipment dan level) dikirim oleh caller
        final_atk = rpg_data.get("final_atk", rpg_data.get("atk", 0))
        final_def = rpg_data.get("final_def", rpg_data.get("def", 0))
        stamina_val = rpg_data.get("stamina", 0)
        max_stamina = rpg_data.get("max_stamina", 20)  # Dinamis sesuai level
        
        pilmoji.text((bar_x, stats_y), f"⚔️ ATK: {final_atk}", font=font_stats, fill=text_main)
        pilmoji.text((bar_x + 180, stats_y), f"🛡️ DEF: {final_def}", font=font_stats, fill=text_main)
        pilmoji.text((bar_x + 360, stats_y), f"⚡ STAMINA: {stamina_val}/{max_stamina}", font=font_stats, fill=text_main)

    # Profile Picture
    draw = ImageDraw.Draw(base)
    draw.ellipse([pfp_x-3, pfp_y-3, pfp_x+pfp_size+3, pfp_y+pfp_size+3], outline=accent_color, width=3)
    if profile_photo_bytes:
        try:
            pfp = Image.open(io.BytesIO(profile_photo_bytes)).convert("RGBA")
            pfp = ImageOps.fit(pfp, (pfp_size, pfp_size), centering=(0.5, 0.5))
            mask = Image.new('L', (pfp_size, pfp_size), 0)
            ImageDraw.Draw(mask).ellipse((0, 0, pfp_size, pfp_size), fill=255)
            output_pfp = Image.new('RGBA', (pfp_size, pfp_size), (0, 0, 0, 0))
            output_pfp.paste(pfp, (0, 0), mask=mask)
            base.paste(output_pfp, (pfp_x, pfp_y), output_pfp)
        except:
            draw.ellipse([pfp_x, pfp_y, pfp_x+pfp_size, pfp_y+pfp_size], fill='#1E293B')
    else:
        draw.ellipse([pfp_x, pfp_y, pfp_x+pfp_size, pfp_y+pfp_size], fill='#1E293B')

    base = base.convert('RGB')
    img_byte_arr = io.BytesIO()
    base.save(img_byte_arr, format='PNG', optimize=True)
    img_byte_arr.seek(0)
    return img_byte_arr

async def generate_profile_card(user_name, level, xp, next_level_xp, coins, rank, profile_photo_bytes=None, is_premium=False, rpg_data=None):
    if rpg_data is None:
        rpg_data = {"class": "Novice", "hp": 100, "max_hp": 100, "atk": 10, "def": 5, "stamina": 20, "max_stamina": 20}
    # Pastikan max_stamina ada (fallback)
    if "max_stamina" not in rpg_data:
        rpg_data["max_stamina"] = 20
    
    bg_url = "https://beeimg.com/images/u31580380724.jpg"
    base = await get_background(bg_url, 800, 500)
    return await asyncio.to_thread(_draw_profile_sync, base, user_name, level, xp, next_level_xp, coins, rank, profile_photo_bytes, is_premium, rpg_data)

# ========== WELCOME & GOODBYE (TIDAK BERUBAH) ==========
async def generate_welcome_image(user_name, group_name, profile_photo_bytes=None):
    bg_url = "https://images.unsplash.com/photo-1614850523459-c2f4c699c52e?q=80&w=800&h=450&auto=format&fit=crop"
    base = await get_background(bg_url, 800, 450)
    return await asyncio.to_thread(_draw_welcome_sync, base, user_name, group_name, profile_photo_bytes)

def _draw_welcome_sync(base, user_name, group_name, profile_photo_bytes):
    width, height = base.size
    accent_color = '#00D2FF'
    text_main = '#FFFFFF'
    text_sub = '#94A3B8'
    overlay = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    box_padding = 40
    overlay_draw.rounded_rectangle([box_padding, box_padding, width - box_padding, height - box_padding], radius=25, fill=(15, 23, 42, 200))
    base = Image.alpha_composite(base.convert('RGBA'), overlay)
    try:
        font_welcome = ImageFont.truetype(FONT_PATH, 24); font_name = ImageFont.truetype(FONT_PATH, 48); font_group = ImageFont.truetype(FONT_PATH, 20)
    except:
        font_welcome = font_name = font_group = ImageFont.load_default()
    with Pilmoji(base) as pilmoji:
        pilmoji.text((width//2, 85), "WELCOME TO", font=font_welcome, fill=text_sub, anchor="mm")
        pilmoji.text((width//2, 125), group_name.upper(), font=font_group, fill=accent_color, anchor="mm")
        pilmoji.text((width//2, 375), user_name, font=font_name, fill=text_main, anchor="mm")
    pfp_size = 170; pfp_x, pfp_y = width//2 - pfp_size//2, 160
    draw = ImageDraw.Draw(base)
    draw.ellipse([pfp_x-4, pfp_y-4, pfp_x+pfp_size+4, pfp_y+pfp_size+4], outline=accent_color, width=3)
    if profile_photo_bytes:
        try:
            pfp = Image.open(io.BytesIO(profile_photo_bytes)).convert("RGBA")
            pfp = ImageOps.fit(pfp, (pfp_size, pfp_size), centering=(0.5, 0.5))
            mask = Image.new('L', (pfp_size, pfp_size), 0); ImageDraw.Draw(mask).ellipse((0, 0, pfp_size, pfp_size), fill=255)
            output_pfp = Image.new('RGBA', (pfp_size, pfp_size), (0, 0, 0, 0)); output_pfp.paste(pfp, (0, 0), mask=mask)
            base.paste(output_pfp, (pfp_x, pfp_y), output_pfp)
        except: draw.ellipse([pfp_x, pfp_y, pfp_x+pfp_size, pfp_y+pfp_size], fill='#1E293B')
    else: draw.ellipse([pfp_x, pfp_y, pfp_x+pfp_size, pfp_y+pfp_size], fill='#1E293B')
    base = base.convert('RGB'); img_byte_arr = io.BytesIO(); base.save(img_byte_arr, format='PNG'); img_byte_arr.seek(0)
    return img_byte_arr

async def generate_goodbye_image(user_name, group_name, profile_photo_bytes=None):
    bg_url = "https://images.unsplash.com/photo-1470770903676-69b98201ea1c?q=80&w=800&h=450&auto=format&fit=crop"
    base = await get_background(bg_url, 800, 450)
    return await asyncio.to_thread(_draw_goodbye_sync, base, user_name, group_name, profile_photo_bytes)

def _draw_goodbye_sync(base, user_name, group_name, profile_photo_bytes):
    width, height = base.size; base = ImageOps.grayscale(base).convert('RGB')
    overlay = Image.new('RGBA', (width, height), (0, 0, 0, 0)); overlay_draw = ImageDraw.Draw(overlay)
    box_padding = 40; overlay_draw.rounded_rectangle([box_padding, box_padding, width - box_padding, height - box_padding], radius=25, fill=(15, 23, 42, 220))
    base = Image.alpha_composite(base.convert('RGBA'), overlay)
    try:
        font_goodbye = ImageFont.truetype(FONT_PATH, 24); font_name = ImageFont.truetype(FONT_PATH, 48); font_group = ImageFont.truetype(FONT_PATH, 20)
    except: font_goodbye = font_name = font_group = ImageFont.load_default()
    with Pilmoji(base) as pilmoji:
        pilmoji.text((width//2, 85), "FAREWELL FROM", font=font_goodbye, fill='#64748B', anchor="mm")
        pilmoji.text((width//2, 125), group_name.upper(), font=font_group, fill='#94A3B8', anchor="mm")
        pilmoji.text((width//2, 375), user_name, font=font_name, fill='#FFFFFF', anchor="mm")
    pfp_size = 170; pfp_x, pfp_y = width//2 - pfp_size//2, 160
    draw = ImageDraw.Draw(base); draw.ellipse([pfp_x-4, pfp_y-4, pfp_x+pfp_size+4, pfp_y+pfp_size+4], outline='#94A3B8', width=3)
    if profile_photo_bytes:
        try:
            pfp = Image.open(io.BytesIO(profile_photo_bytes)).convert("RGBA"); pfp = ImageOps.fit(pfp, (pfp_size, pfp_size), centering=(0.5, 0.5)); pfp = ImageOps.grayscale(pfp).convert('RGBA')
            mask = Image.new('L', (pfp_size, pfp_size), 0); ImageDraw.Draw(mask).ellipse((0, 0, pfp_size, pfp_size), fill=255)
            output_pfp = Image.new('RGBA', (pfp_size, pfp_size), (0, 0, 0, 0)); output_pfp.paste(pfp, (0, 0), mask=mask); base.paste(output_pfp, (pfp_x, pfp_y), output_pfp)
        except: draw.ellipse([pfp_x, pfp_y, pfp_x+pfp_size, pfp_y+pfp_size], fill='#1E293B')
    else: draw.ellipse([pfp_x, pfp_y, pfp_x+pfp_size, pfp_y+pfp_size], fill='#1E293B')
    base = base.convert('RGB'); img_byte_arr = io.BytesIO(); base.save(img_byte_arr, format='PNG'); img_byte_arr.seek(0)
    return img_byte_arr