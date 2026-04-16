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
            # Process image in a thread to keep event loop responsive
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

def _draw_welcome_sync(base, user_name, group_name, profile_photo_bytes):
    """Synchronous part of welcome image generation (runs in thread)"""
    width, height = base.size
    accent_color = '#00D2FF'
    text_main = '#FFFFFF'
    text_sub = '#94A3B8'
    
    # Create Glass Box effect
    overlay = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    box_padding = 40
    overlay_draw.rounded_rectangle(
        [box_padding, box_padding, width - box_padding, height - box_padding], 
        radius=25, fill=(15, 23, 42, 200)
    )
    overlay_draw.rounded_rectangle(
        [box_padding, box_padding, width - box_padding, height - box_padding], 
        radius=25, outline=(56, 189, 248, 60), width=2
    )
    
    base = Image.alpha_composite(base.convert('RGBA'), overlay)
    
    try:
        font_welcome = ImageFont.truetype(FONT_PATH, 24)
        font_name = ImageFont.truetype(FONT_PATH, 48)
        font_group = ImageFont.truetype(FONT_PATH, 20)
    except:
        font_welcome = font_name = font_group = ImageFont.load_default()

    with Pilmoji(base) as pilmoji:
        pilmoji.text((width//2, 85), "WELCOME TO", font=font_welcome, fill=text_sub, anchor="mm")
        pilmoji.text((width//2, 125), group_name.upper(), font=font_group, fill=accent_color, anchor="mm")
        pilmoji.text((width//2, 375), user_name, font=font_name, fill=text_main, anchor="mm")

    pfp_size = 170
    pfp_x, pfp_y = width//2 - pfp_size//2, 160
    draw = ImageDraw.Draw(base)
    draw.ellipse([pfp_x-4, pfp_y-4, pfp_x+pfp_size+4, pfp_y+pfp_size+4], outline=accent_color, width=3)

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

async def generate_welcome_image(user_name, group_name, profile_photo_bytes=None):
    bg_url = "https://images.unsplash.com/photo-1614850523459-c2f4c699c52e?q=80&w=800&h=450&auto=format&fit=crop"
    base = await get_background(bg_url, 800, 450)
    return await asyncio.to_thread(_draw_welcome_sync, base, user_name, group_name, profile_photo_bytes)

def _draw_goodbye_sync(base, user_name, group_name, profile_photo_bytes):
    """Synchronous part of goodbye image generation"""
    width, height = base.size
    base = ImageOps.grayscale(base).convert('RGB')
    
    overlay = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    accent_color = '#94A3B8'
    text_main = '#FFFFFF'
    text_sub = '#64748B'
    
    box_padding = 40
    overlay_draw.rounded_rectangle(
        [box_padding, box_padding, width - box_padding, height - box_padding], 
        radius=25, fill=(15, 23, 42, 220)
    )
    overlay_draw.rounded_rectangle(
        [box_padding, box_padding, width - box_padding, height - box_padding], 
        radius=25, outline=(148, 163, 184, 40), width=2
    )
    
    base = Image.alpha_composite(base.convert('RGBA'), overlay)
    
    try:
        font_goodbye = ImageFont.truetype(FONT_PATH, 24)
        font_name = ImageFont.truetype(FONT_PATH, 48)
        font_group = ImageFont.truetype(FONT_PATH, 20)
    except:
        font_goodbye = font_name = font_group = ImageFont.load_default()

    with Pilmoji(base) as pilmoji:
        pilmoji.text((width//2, 85), "FAREWELL FROM", font=font_goodbye, fill=text_sub, anchor="mm")
        pilmoji.text((width//2, 125), group_name.upper(), font=font_group, fill=accent_color, anchor="mm")
        pilmoji.text((width//2, 375), user_name, font=font_name, fill=text_main, anchor="mm")

    pfp_size = 170
    pfp_x, pfp_y = width//2 - pfp_size//2, 160
    draw = ImageDraw.Draw(base)
    draw.ellipse([pfp_x-4, pfp_y-4, pfp_x+pfp_size+4, pfp_y+pfp_size+4], outline=accent_color, width=3)

    if profile_photo_bytes:
        try:
            pfp = Image.open(io.BytesIO(profile_photo_bytes)).convert("RGBA")
            pfp = ImageOps.fit(pfp, (pfp_size, pfp_size), centering=(0.5, 0.5))
            pfp = ImageOps.grayscale(pfp).convert('RGBA')
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

async def generate_goodbye_image(user_name, group_name, profile_photo_bytes=None):
    bg_url = "https://images.unsplash.com/photo-1470770903676-69b98201ea1c?q=80&w=800&h=450&auto=format&fit=crop"
    base = await get_background(bg_url, 800, 450)
    return await asyncio.to_thread(_draw_goodbye_sync, base, user_name, group_name, profile_photo_bytes)

def _draw_profile_sync(base, user_name, level, xp, next_level_xp, coins, rank, profile_photo_bytes, is_premium):
    """Synchronous part of profile card generation"""
    width, height = base.size
    overlay = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    
    accent_color = '#00D2FF'
    gold_color = '#FFD700'
    text_main = '#FFFFFF'
    text_sub = '#94A3B8'
    
    box_padding = 40
    overlay_draw.rounded_rectangle([box_padding, box_padding, width - box_padding, height - box_padding], radius=25, fill=(15, 23, 42, 180))
    overlay_draw.rounded_rectangle([box_padding, box_padding, width - box_padding, height - box_padding], radius=25, outline=(56, 189, 248, 40), width=2)
    
    base = Image.alpha_composite(base.convert('RGBA'), overlay)
    
    try:
        font_name = ImageFont.truetype(FONT_PATH, 42)
        font_stats = ImageFont.truetype(FONT_PATH, 22)
        font_level_val = ImageFont.truetype(FONT_PATH, 65)
        font_label = ImageFont.truetype(FONT_PATH, 16)
        font_badge = ImageFont.truetype(FONT_PATH, 14)
    except:
        font_name = font_stats = font_level_val = font_label = font_badge = ImageFont.load_default()

    with Pilmoji(base) as pilmoji:
        pfp_size = 170
        pfp_x, pfp_y = box_padding + 30, box_padding + 30
        content_x = pfp_x + pfp_size + 40
        
        if is_premium:
            badge_w, badge_h = 90, 22
            pilmoji.draw.rounded_rectangle([content_x, pfp_y, content_x+badge_w, pfp_y+badge_h], radius=10, fill=gold_color)
            pilmoji.text((content_x + badge_w//2, pfp_y + badge_h//2), "PREMIUM", font=font_badge, fill='black', anchor="mm")
            name_y = pfp_y + 30
        else:
            name_y = pfp_y

        pilmoji.text((content_x, name_y), user_name, font=font_name, fill=text_main)
        pilmoji.text((content_x, name_y + 55), f"GLOBAL RANK #{rank}", font=font_stats, fill=gold_color)

        level_x = width - box_padding - 100
        pilmoji.text((level_x, pfp_y + 20), "LEVEL", font=font_label, fill=text_sub, anchor="mm")
        pilmoji.text((level_x, pfp_y + 80), str(level), font=font_level_val, fill=accent_color, anchor="mm")
        pilmoji.text((level_x, pfp_y + 140), f"💰 {coins}", font=font_stats, fill=gold_color, anchor="mm")

        bar_x, bar_y, bar_w, bar_h = pfp_x, box_padding + pfp_size + 70, width - (box_padding * 2) - 60, 20
        progress = min(1, xp / next_level_xp) if next_level_xp > 0 else 0
        pilmoji.text((bar_x, bar_y - 25), f"XP PROGRESS: {xp} / {next_level_xp}", font=font_label, fill=text_sub)
        
        draw = ImageDraw.Draw(base)
        draw.rounded_rectangle([bar_x, bar_y, bar_x+bar_w, bar_y+bar_h], radius=10, fill=(30, 41, 59, 150))
        if progress > 0:
            draw.rounded_rectangle([bar_x, bar_y, bar_x + (bar_w * progress), bar_y+bar_h], radius=10, fill=accent_color)

    draw = ImageDraw.Draw(base)
    draw.ellipse([pfp_x-4, pfp_y-4, pfp_x+pfp_size+4, pfp_y+pfp_size+4], outline=accent_color, width=3)
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

async def generate_profile_card(user_name, level, xp, next_level_xp, coins, rank, profile_photo_bytes=None, is_premium=False):
    bg_url = "https://beeimg.com/images/u31580380724.jpg"
    base = await get_background(bg_url, 800, 450)
    return await asyncio.to_thread(_draw_profile_sync, base, user_name, level, xp, next_level_xp, coins, rank, profile_photo_bytes, is_premium)
