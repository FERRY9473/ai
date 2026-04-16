"""
RPG Module - Aphrodite Bot
Fitur Lengkap: Adventure, Battle, Stamina (Level-based), Inventory, Shop, Class System
Version: 6.1 - Weapons/Armors Scale 3% per User Level
"""

from core.bot import bot, safe_reply
from database.db import db
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import random
import logging
from datetime import datetime, timedelta
from collections import Counter

logger = logging.getLogger("RPG_Handler")

# ==================== CONFIGURATION ====================

STAMINA_REGEN_MINUTES = 5
BASE_STAMINA = 20
STAMINA_INCREMENT = 2
STAMINA_LEVEL_INTERVAL = 10

HEAL_COST = 30
ADVENTURE_STAMINA_COST = 2
ATTACK_STAMINA_COST = 1
RUN_STAMINA_PENALTY = 1
REST_STAMINA_GAIN = 5
REST_COOLDOWN_MINUTES = 30

HP_PER_LEVEL = 10

# ==================== ACTIVE BATTLES STORAGE ====================
active_battles = {}

# ==================== MONSTER DATA (100+ Variants) ====================
MONSTERS = [
    {"name": "Slime Hijau", "min_level": 1, "hp": 30, "atk": 5, "xp": 25, "coins": 15, "loot": "Lendir Slime"},
    {"name": "Goblin Pencuri", "min_level": 1, "hp": 50, "atk": 10, "xp": 50, "coins": 40, "loot": "Belati Berkarat"},
    {"name": "Serigala Hutan", "min_level": 2, "hp": 70, "atk": 15, "xp": 70, "coins": 30, "loot": "Taring Serigala"},
    {"name": "Kelelawar Gua", "min_level": 2, "hp": 40, "atk": 12, "xp": 45, "coins": 20, "loot": "Batu Aneh"},
    {"name": "Tikus Tanah", "min_level": 1, "hp": 25, "atk": 4, "xp": 20, "coins": 10, "loot": "Lendir Slime"},
    {"name": "Kumbang Tanduk", "min_level": 3, "hp": 60, "atk": 14, "xp": 60, "coins": 35, "loot": "Batu Aneh"},
    {"name": "Orc Prajurit", "min_level": 5, "hp": 150, "atk": 25, "xp": 150, "coins": 100, "loot": "Gada Kayu Besar"},
    {"name": "Hantu Tanah", "min_level": 4, "hp": 55, "atk": 18, "xp": 80, "coins": 50, "loot": "Permata Hitam"},
    {"name": "Perampok Jalanan", "min_level": 3, "hp": 80, "atk": 20, "xp": 90, "coins": 60, "loot": "Belati Berkarat"},
    {"name": "Ular Berbisa", "min_level": 5, "hp": 90, "atk": 22, "xp": 110, "coins": 70, "loot": "Taring Serigala"},
    {"name": "Beruang Gua", "min_level": 6, "hp": 180, "atk": 30, "xp": 200, "coins": 120, "loot": "Gada Kayu Besar"},
    {"name": "Penyihir Kegelapan", "min_level": 7, "hp": 120, "atk": 35, "xp": 250, "coins": 150, "loot": "Permata Hitam"},
    {"name": "Shadow Assassin", "min_level": 8, "hp": 200, "atk": 45, "xp": 300, "coins": 250, "loot": "Permata Hitam"},
    {"name": "Elemental Batu", "min_level": 10, "hp": 300, "atk": 50, "xp": 500, "coins": 300, "loot": "Batu Aneh"},
    {"name": "Naga Api", "min_level": 15, "hp": 800, "atk": 80, "xp": 2000, "coins": 1500, "loot": "Sisik Naga"},
]

def generate_monsters():
    monsters = []
    base_names = ["Golem", "Hantu", "Bandit", "Elemental", "Naga", "Orc", "Troll", "Siluman", "Penyihir", "Prajurit", "Pemanah", "Kesatria", "Monster", "Makhluk"]
    loots = ["Batu Aneh", "Permata Hitam", "Taring Serigala", "Lendir Slime", "Belati Berkarat", "Gada Kayu Besar", "Sisik Naga"]
    for i in range(1, 90):
        level = random.randint(1, 30)
        name = f"{random.choice(base_names)} Level {level}"
        hp = 50 + (level * 20) + random.randint(-10, 30)
        atk = 8 + (level * 3) + random.randint(-2, 5)
        xp = 30 + (level * 15) + random.randint(-10, 20)
        coins = 20 + (level * 10) + random.randint(-5, 15)
        loot = random.choice(loots)
        monsters.append({"name": name, "min_level": max(1, level-2), "hp": hp, "atk": atk, "xp": xp, "coins": coins, "loot": loot})
    return monsters

MONSTERS.extend(generate_monsters())

STORY_TEMPLATES = [
    "Di tengah hutan yang sunyi, tiba-tiba {monster} melompat dari balik semak!",
    "Saat kamu beristirahat di dekat sungai, {monster} muncul dengan raungan mengerikan.",
    "Dalam perjalanan menuju desa, kamu dihadang oleh {monster} yang kelaparan.",
    "Dari dalam gua yang gelap, {monster} keluar dan siap menyerang!",
    "Angin berhembus kencang, dan {monster} tiba-tiba sudah berdiri di hadapanmu.",
]

# ==================== ITEM CONFIG ====================
BASE_HEAL_PRICE = 60
BASE_HEAL_EFFECT = 50
BASE_ENERGY_PRICE = 50
BASE_ENERGY_EFFECT = 10

def get_potion_prices_and_effects(level):
    heal_price = BASE_HEAL_PRICE + (level * 2)
    heal_effect = BASE_HEAL_EFFECT + (level * 2)
    energy_price = BASE_ENERGY_PRICE + (level * 3)
    energy_effect = BASE_ENERGY_EFFECT + (level // 5)
    return heal_price, heal_effect, energy_price, energy_effect

ITEM_CONFIG = {
    "Lendir Slime": {"type": "material", "usable": False, "buy_price": 0, "sell_price": 20, "emoji": "🟢"},
    "Taring Serigala": {"type": "material", "usable": False, "buy_price": 0, "sell_price": 40, "emoji": "🐺"},
    "Batu Aneh": {"type": "material", "usable": False, "buy_price": 0, "sell_price": 50, "emoji": "💎"},
    "Belati Berkarat": {"type": "material", "usable": False, "buy_price": 0, "sell_price": 60, "emoji": "🗡"},
    "Gada Kayu Besar": {"type": "material", "usable": False, "buy_price": 0, "sell_price": 100, "emoji": "🔨"},
    "Permata Hitam": {"type": "material", "usable": False, "buy_price": 0, "sell_price": 200, "emoji": "🖤"},
    "Sisik Naga": {"type": "material", "usable": False, "buy_price": 0, "sell_price": 500, "emoji": "🐉"},
}

# ==================== UNIFIED WEAPONS & ARMORS (BASE STATS) ====================
_BASE_WEAPONS = [
    {"id": "wp_steel", "name": "Pedang Baja", "base_price": 300, "base_atk": 15, "tier": 1},
    {"id": "wp_greatsword", "name": "Greatsword", "base_price": 800, "base_atk": 35, "tier": 2, "req_level": 5},
    {"id": "wp_dragonblade", "name": "Dragon Blade", "base_price": 2500, "base_atk": 75, "tier": 3, "req_level": 15},
    {"id": "wp_staff", "name": "Tongkat Ajaib", "base_price": 300, "base_atk": 20, "tier": 1},
    {"id": "wp_grimoire", "name": "Grimoire Api", "base_price": 800, "base_atk": 40, "tier": 2, "req_level": 5, "effect": "double_damage"},
    {"id": "wp_archmage", "name": "Archmage Staff", "base_price": 2500, "base_atk": 80, "tier": 3, "req_level": 15, "effect": "freeze"},
    {"id": "wp_dagger", "name": "Belati Tajam", "base_price": 300, "base_atk": 12, "tier": 1},
    {"id": "wp_crossbow", "name": "Crossbow", "base_price": 800, "base_atk": 30, "tier": 2, "req_level": 5, "effect": "ranged"},
    {"id": "wp_shadowbane", "name": "Shadowbane", "base_price": 2500, "base_atk": 70, "tier": 3, "req_level": 15, "effect": "critical"},
]

_BASE_ARMORS = [
    {"id": "ar_iron", "name": "Zirah Besi", "base_price": 200, "base_def": 10, "tier": 1},
    {"id": "ar_plate", "name": "Plate Armor", "base_price": 600, "base_def": 25, "tier": 2, "req_level": 5},
    {"id": "ar_titan", "name": "Titan Plate", "base_price": 2000, "base_def": 60, "tier": 3, "req_level": 15},
    {"id": "ar_robe", "name": "Jubah Sihir", "base_price": 200, "base_def": 5, "tier": 1},
    {"id": "ar_masterrobe", "name": "Master Robe", "base_price": 600, "base_def": 10, "tier": 2, "req_level": 5},
    {"id": "ar_archrobe", "name": "Archmage Robe", "base_price": 2000, "base_def": 25, "tier": 3, "req_level": 15},
    {"id": "ar_leather", "name": "Jaket Kulit", "base_price": 200, "base_def": 8, "tier": 1},
    {"id": "ar_shadow", "name": "Shadow Garb", "base_price": 600, "base_def": 15, "tier": 2, "req_level": 5},
    {"id": "ar_nightshade", "name": "Nightshade Vest", "base_price": 2000, "base_def": 40, "tier": 3, "req_level": 15},
]

def get_scaled_weapon(base_wp, user_level):
    """Menghasilkan senjata dengan harga dan ATK yang diskala 3% per level user"""
    scale = 1.0 + (user_level * 0.03)
    wp = base_wp.copy()
    wp["price"] = int(base_wp["base_price"] * scale)
    wp["atk"] = int(base_wp["base_atk"] * scale)
    return wp

def get_scaled_armor(base_ar, user_level):
    """Menghasilkan armor dengan harga dan DEF yang diskala 3% per level user"""
    scale = 1.0 + (user_level * 0.03)
    ar = base_ar.copy()
    ar["price"] = int(base_ar["base_price"] * scale)
    ar["def"] = int(base_ar["base_def"] * scale)
    return ar

# Untuk kompatibilitas
ALL_WEAPONS = _BASE_WEAPONS
ALL_ARMORS = _BASE_ARMORS
CLASS_WEAPONS = {}
CLASS_ARMORS = {}

# ==================== HELPER FUNCTIONS ====================

def clean_text(text):
    if not text:
        return ""
    for char in "_*`[]()~>#+=|{}.!-":
        text = text.replace(char, "")
    return text.strip()

def get_progress_bar(current, total, length=8):
    try:
        if total <= 0:
            return "⬜" * length
        progress = int((current / total) * length)
        progress = max(0, min(length, progress))
        return "🟩" * progress + "⬜" * (length - progress)
    except:
        return "⬜" * length

def get_max_stamina(level):
    tier = (level - 1) // STAMINA_LEVEL_INTERVAL
    return BASE_STAMINA + (tier * STAMINA_INCREMENT)

def get_player_stats(user_data):
    lvl = user_data.get("level", 1)
    base_atk = user_data.get("atk", 10)
    base_def = user_data.get("def", 5)
    
    weapon = user_data.get("weapon") or {}
    armor = user_data.get("armor") or {}
    
    wp_atk = weapon.get("atk", 0)
    wp_def = weapon.get("def", 0)
    ar_def = armor.get("def", 0)
    
    total_atk = base_atk + (lvl * 2) + wp_atk
    total_def = base_def + (lvl * 1) + ar_def + wp_def
    
    return total_atk, total_def

def check_and_regen_stamina(user_data):
    try:
        level = user_data.get("level", 1)
        max_stamina = get_max_stamina(level)
        
        if "stamina" not in user_data:
            user_data["stamina"] = max_stamina
            user_data["last_stamina_update"] = datetime.now().isoformat()
            return user_data
        
        user_data["max_stamina"] = max_stamina
        
        last_update = user_data.get("last_stamina_update")
        current_stamina = user_data.get("stamina", max_stamina)
        
        if last_update and current_stamina < max_stamina:
            last_time = datetime.fromisoformat(last_update)
            now = datetime.now()
            diff_minutes = (now - last_time).total_seconds() / 60
            
            regen_amount = int(diff_minutes // STAMINA_REGEN_MINUTES)
            if regen_amount > 0:
                new_stamina = min(max_stamina, current_stamina + regen_amount)
                user_data["stamina"] = new_stamina
                user_data["last_stamina_update"] = now.isoformat()
        
        return user_data
    except Exception as e:
        logger.error(f"Error regen stamina: {e}")
        return user_data

def consume_stamina(user_data, amount=1):
    user_data = check_and_regen_stamina(user_data)
    current = user_data.get("stamina", 0)
    max_stamina = user_data.get("max_stamina", BASE_STAMINA)
    
    if current >= amount:
        user_data["stamina"] = current - amount
        user_data["last_stamina_update"] = datetime.now().isoformat()
        return True, user_data
    else:
        return False, user_data

def get_stamina_text(user_data):
    stamina = user_data.get("stamina", 0)
    max_stamina = user_data.get("max_stamina", BASE_STAMINA)
    bar = get_progress_bar(stamina, max_stamina, 8)
    return f"⚡ Stamina: {stamina}/{max_stamina} {bar}"

def get_item_emoji(item_name):
    config = ITEM_CONFIG.get(item_name, {})
    return config.get("emoji", "📦")

async def safe_edit_message(chat_id, message_id, text, reply_markup=None):
    try:
        return await bot.edit_message_text(
            text, chat_id, message_id,
            reply_markup=reply_markup
        )
    except Exception as e:
        error_msg = str(e).lower()
        if "message is not modified" in error_msg:
            return None
        elif "there is no text" in error_msg:
            try:
                return await bot.edit_message_caption(
                    chat_id=chat_id, message_id=message_id,
                    caption=text, reply_markup=reply_markup
                )
            except:
                return await bot.send_message(chat_id, text, reply_markup=reply_markup)
        else:
            logger.error(f"Edit failed: {e}")
            return await bot.send_message(chat_id, text, reply_markup=reply_markup)

def check_level_up(user_data):
    xp = user_data.get("xp", 0)
    current_level = user_data.get("level", 1)
    new_level = (xp // 200) + 1   # <-- XP dibagi 100 + 1
    
    leveled_up = False
    while new_level > current_level:
        current_level += 1
        leveled_up = True
        user_data["max_hp"] = user_data.get("max_hp", 100) + HP_PER_LEVEL
        user_data["max_stamina"] = get_max_stamina(current_level)
    
    if leveled_up:
        user_data["level"] = current_level
        user_data["hp"] = user_data["max_hp"]
        user_data["stamina"] = user_data["max_stamina"]
        user_data["last_stamina_update"] = datetime.now().isoformat()
        return True, current_level
    
    return False, current_level

def get_random_monster(user_level):
    base = random.choice(MONSTERS).copy()
    
    # Target stats untuk level user
    target_hp = 100 + (user_level * 6)      # Sedikit di atas user (user +10/lvl)
    target_atk = 10 + (user_level * 2.5)     # Sedikit di atas user (user +2/lvl)
    
    # Hitung scale berdasarkan monster dasar
    hp_scale = target_hp / base["hp"]
    atk_scale = target_atk / base["atk"]
    
    # Gunakan scale rata-rata agar proporsional
    scale = (hp_scale + atk_scale) / 2
    
    # Batasi scale agar tidak terlalu ekstrem di level rendah
    scale = max(0.3, min(scale, 50.0))
    
    # Terapkan scaling
    base["hp"] = int(base["hp"] * scale)
    base["atk"] = int(base["atk"] * scale)
    base["xp"] = int(base["xp"] * scale)
    base["coins"] = int(base["coins"] * scale)
    base["max_hp"] = base["hp"]
    
    # Beri indikator level
    if scale > 1.2:
        base["name"] = f"{base['name']} ⚡Lv.{user_level}"
    
    return base

def generate_story(monster_name):
    template = random.choice(STORY_TEMPLATES)
    return template.format(monster=monster_name)

# ==================== BATTLE SCREEN ====================

async def show_battle_screen(chat_id, message_id, user_id, user_data, monster_name, last_dmg_player=0, last_dmg_monster=0):
    if user_id not in active_battles:
        return
    
    battle = active_battles[user_id]
    monster = battle["monster"]
    monster_hp = battle["monster_hp"]
    monster_max_hp = monster["max_hp"]
    
    monster_hp_bar = get_progress_bar(monster_hp, monster_max_hp, 10)
    player_hp_bar = get_progress_bar(user_data.get("hp", 0), user_data.get("max_hp", 100), 10)
    
    battle_info = ""
    if last_dmg_player > 0:
        battle_info = f"⚔️ Kamu: -{last_dmg_monster} | Musuh: -{last_dmg_player}\n\n"
    
    msg = (
        f"🤺 BATTLE: {monster_name}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"👾 Musuh: {monster_name}\n"
        f"❤️ HP Musuh: {monster_hp}/{monster_max_hp}\n{monster_hp_bar}\n\n"
        f"👤 Kamu: {clean_text(user_data.get('name', 'Hero'))}\n"
        f"❤️ HP Kamu: {user_data.get('hp', 0)}/{user_data.get('max_hp', 100)}\n{player_hp_bar}\n"
        f"{get_stamina_text(user_data)}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"{battle_info}"
    )
    
    markup = InlineKeyboardMarkup(row_width=3)
    markup.add(
        InlineKeyboardButton("⚔️ Serang", callback_data=f"rpg_atk_{monster_name}"),
        InlineKeyboardButton("🧪 Potion", callback_data="rpg_use_potion_quick"),
        InlineKeyboardButton("🏃 Lari", callback_data="rpg_run")
    )
    
    await safe_edit_message(chat_id, message_id, msg, reply_markup=markup)

# ==================== PROFILE SCREEN ====================

async def show_profile(chat_id, user_id, first_name, message_id=None, is_callback=False):
    user_data = db.get_user(user_id)
    user_data = check_and_regen_stamina(user_data)
    user_data["name"] = first_name
    db.update_user(user_id, user_data)
    
    rpg_class = user_data.get("rpg_class", "Novice")
    level = user_data.get("level", 1)
    coins = user_data.get("coins", 0)
    kills = user_data.get("kills", 0)
    deaths = user_data.get("deaths", 0)
    
    hp = user_data.get("hp", 0)
    max_hp = user_data.get("max_hp", 100)
    hp_bar = get_progress_bar(hp, max_hp, 10)
    
    xp = user_data.get("xp", 0)
    xp_target = 100
    current_xp = xp % xp_target
    xp_bar = get_progress_bar(current_xp, xp_target, 10)
    
    atk, defense = get_player_stats(user_data)
    
    weapon = user_data.get("weapon") or {}
    armor = user_data.get("armor") or {}
    weapon_name = weapon.get("name", "Tidak ada")
    armor_name = armor.get("name", "Tidak ada")
    
    stamina_text = get_stamina_text(user_data)
    
    in_battle = user_id in active_battles
    battle_status = "⚔️ SEDANG BATTLE!" if in_battle else "🛖 Di Kota"
    
    msg = (
        f"👤 PROFIL HERO: {clean_text(first_name)}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🎖 Class: {rpg_class}\n"
        f"📊 Lvl: {level} | 💰 {coins} Koin\n"
        f"☠️ Kills: {kills} | 💀 Deaths: {deaths}\n"
        f"📍 Status: {battle_status}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"❤️ HP: {hp}/{max_hp}\n{hp_bar}\n"
        f"🌟 XP: {current_xp}/{xp_target}\n{xp_bar}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"⚔️ ATK: {atk} | 🛡 DEF: {defense}\n"
        f"{stamina_text}\n"
        f"🗡 Weapon: {clean_text(weapon_name)}\n"
        f"🛡 Armor: {clean_text(armor_name)}\n"
        f"━━━━━━━━━━━━━━━━━━━━"
    )
    
    markup = InlineKeyboardMarkup(row_width=2)
    
    if in_battle:
        battle = active_battles[user_id]
        monster_name = battle["monster"]["name"]
        markup.add(InlineKeyboardButton("⚔️ LANJUTKAN BATTLE", callback_data=f"rpg_atk_{monster_name}"))
    else:
        markup.add(InlineKeyboardButton("🏃 ADVENTURE", callback_data="rpg_adventure_start"))
    
    markup.add(
        InlineKeyboardButton("🎒 Inventory", callback_data="rpg_inv"),
        InlineKeyboardButton("🛒 Shop", callback_data="rpg_shop_open")
    )
    markup.add(
        InlineKeyboardButton("💤 Istirahat", callback_data="rpg_rest"),
        InlineKeyboardButton(f"🏥 Heal ({HEAL_COST}💰)", callback_data="rpg_heal")
    )
    
    if message_id and is_callback:
        await safe_edit_message(chat_id, message_id, msg, reply_markup=markup)
    else:
        await bot.send_message(chat_id, msg, reply_markup=markup)

# ==================== COMMAND HANDLERS ====================

@bot.message_handler(commands=['adventure'])
async def adventure_command(message):
    user_id = message.from_user.id
    user_data = db.get_user(user_id)
    
    if not user_data.get("rpg_class"):
        markup = InlineKeyboardMarkup(row_width=2)
        markup.add(
            InlineKeyboardButton("🛡 Warrior", callback_data="set_warrior"),
            InlineKeyboardButton("🔮 Mage", callback_data="set_mage"),
            InlineKeyboardButton("🗡 Rogue", callback_data="set_rogue")
        )
        msg = (
            "🎭 PILIH CLASS HERO\n\n"
            "🛡 Warrior: HP 150 | ATK 12 | DEF 8\n"
            "🔮 Mage: HP 80 | ATK 25 | DEF 3\n"
            "🗡 Rogue: HP 100 | ATK 18 | DEF 5"
        )
        return await bot.send_message(message.chat.id, msg, reply_markup=markup)
    
    user_data = check_and_regen_stamina(user_data)
    
    if user_data.get("hp", 0) <= 0:
        markup = InlineKeyboardMarkup()
        markup.add(
            InlineKeyboardButton(f"🏥 Heal ({HEAL_COST}💰)", callback_data="rpg_heal"),
            InlineKeyboardButton("📊 Profil", callback_data="rpg_back_stats")
        )
        return await bot.send_message(
            message.chat.id,
            "💀 HP KAMU 0!\nKamu terlalu luka untuk bertualang.",
            reply_markup=markup
        )
    
    if user_id in active_battles:
        battle = active_battles[user_id]
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("⚔️ Lanjutkan Battle", callback_data=f"rpg_atk_{battle['monster']['name']}"))
        return await bot.send_message(
            message.chat.id,
            f"⚠️ Kamu sedang melawan {battle['monster']['name']}!",
            reply_markup=markup
        )
    
    stamina_ok, user_data = consume_stamina(user_data, ADVENTURE_STAMINA_COST)
    if not stamina_ok:
        markup = InlineKeyboardMarkup()
        markup.add(
            InlineKeyboardButton("💤 Istirahat", callback_data="rpg_rest"),
            InlineKeyboardButton("📊 Profil", callback_data="rpg_back_stats")
        )
        stamina_text = get_stamina_text(user_data)
        return await bot.send_message(
            message.chat.id,
            f"😫 STAMINA HABIS!\n\n{stamina_text}",
            reply_markup=markup
        )
    
    db.update_user(user_id, user_data)
    
    monster = get_random_monster(user_data.get("level", 1))
    monster["max_hp"] = monster["hp"]
    
    active_battles[user_id] = {
        "monster": monster,
        "monster_hp": monster["hp"],
        "chat_id": message.chat.id,
        "message_id": None,
        "start_time": datetime.now()
    }
    
    story = generate_story(monster["name"])
    
    monster_hp_bar = get_progress_bar(monster["hp"], monster["max_hp"], 10)
    player_hp_bar = get_progress_bar(user_data.get("hp", 0), user_data.get("max_hp", 100), 10)
    
    msg = (
        f"🏃 ADVENTURE DIMULAI!\n\n"
        f"{story}\n\n"
        f"🤺 BATTLE: {monster['name']}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"👾 Musuh: {monster['name']}\n"
        f"❤️ HP Musuh: {monster['hp']}/{monster['max_hp']}\n{monster_hp_bar}\n\n"
        f"👤 Kamu: {clean_text(message.from_user.first_name)}\n"
        f"❤️ HP Kamu: {user_data.get('hp', 0)}/{user_data.get('max_hp', 100)}\n{player_hp_bar}\n"
        f"{get_stamina_text(user_data)}\n"
        f"━━━━━━━━━━━━━━━━━━━━"
    )
    
    markup = InlineKeyboardMarkup(row_width=3)
    markup.add(
        InlineKeyboardButton("⚔️ Serang", callback_data=f"rpg_atk_{monster['name']}"),
        InlineKeyboardButton("🧪 Potion", callback_data="rpg_use_potion_quick"),
        InlineKeyboardButton("🏃 Lari", callback_data="rpg_run")
    )
    
    sent_msg = await bot.send_message(message.chat.id, msg, reply_markup=markup)
    active_battles[user_id]["message_id"] = sent_msg.message_id

@bot.message_handler(commands=['rpg', 'profil', 'stats'])
async def profile_command(message):
    user_id = message.from_user.id
    user_data = db.get_user(user_id)
    
    if not user_data.get("rpg_class"):
        markup = InlineKeyboardMarkup(row_width=2)
        markup.add(
            InlineKeyboardButton("🛡 Warrior", callback_data="set_warrior"),
            InlineKeyboardButton("🔮 Mage", callback_data="set_mage"),
            InlineKeyboardButton("🗡 Rogue", callback_data="set_rogue")
        )
        msg = (
            "🎭 PILIH CLASS HERO\n\n"
            "🛡 Warrior: HP 150 | ATK 12 | DEF 8\n"
            "🔮 Mage: HP 80 | ATK 25 | DEF 3\n"
            "🗡 Rogue: HP 100 | ATK 18 | DEF 5"
        )
        return await bot.send_message(message.chat.id, msg, reply_markup=markup)
    
    await show_profile(message.chat.id, user_id, message.from_user.first_name)

@bot.message_handler(commands=['class'])
async def class_command(message):
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("🛡 Warrior", callback_data="set_warrior"),
        InlineKeyboardButton("🔮 Mage", callback_data="set_mage"),
        InlineKeyboardButton("🗡 Rogue", callback_data="set_rogue")
    )
    msg = (
        "🎭 PILIH CLASS HERO\n\n"
        "🛡 Warrior: HP 150 | ATK 12 | DEF 8\n"
        "🔮 Mage: HP 80 | ATK 25 | DEF 3\n"
        "🗡 Rogue: HP 100 | ATK 18 | DEF 5"
    )
    await bot.send_message(message.chat.id, msg, reply_markup=markup)

@bot.message_handler(commands=['rest', 'istirahat'])
async def rest_command(message):
    user_id = message.from_user.id
    user_data = db.get_user(user_id)
    if not user_data.get("rpg_class"):
        return await safe_reply(message, "⚠️ Pilih class dulu dengan /class")
    
    user_data = check_and_regen_stamina(user_data)
    last_rest = user_data.get("last_rest")
    now = datetime.now()
    
    if last_rest:
        last_time = datetime.fromisoformat(last_rest)
        if now < last_time + timedelta(minutes=REST_COOLDOWN_MINUTES):
            remaining = (last_time + timedelta(minutes=REST_COOLDOWN_MINUTES)) - now
            minutes = remaining.seconds // 60
            return await safe_reply(message, f"⏳ Bisa istirahat lagi dalam {minutes} menit")
    
    max_stamina = user_data.get("max_stamina", BASE_STAMINA)
    user_data["stamina"] = min(max_stamina, user_data.get("stamina", 0) + REST_STAMINA_GAIN)
    user_data["last_rest"] = now.isoformat()
    user_data["last_stamina_update"] = now.isoformat()
    db.update_user(user_id, user_data)
    
    await safe_reply(message, f"💤 Kamu beristirahat dan memulihkan {REST_STAMINA_GAIN} stamina!\n{get_stamina_text(user_data)}")

# ==================== MAIN CALLBACK HANDLER ====================

last_callback_time = {}

@bot.callback_query_handler(func=lambda call: True)
async def main_callback_handler(call):
    user_id = call.from_user.id
    now = datetime.now()
    
    if user_id in last_callback_time:
        diff = (now - last_callback_time[user_id]).total_seconds()
        if diff < 0.5:
            await bot.answer_callback_query(call.id, "⏳ Tunggu sebentar...")
            return
    last_callback_time[user_id] = now
    
    logger.info(f"CALLBACK: {call.data} from {user_id}")
    
    data = call.data
    chat_id = call.message.chat.id
    msg_id = call.message.message_id
    
    try:
        # ========== CLASS SELECTION ==========
        if data.startswith("set_"):
            choice = data.replace("set_", "")
            user_data = db.get_user(user_id)
            now_str = datetime.now().isoformat()
            
            class_stats = {
                "warrior": {"max_hp": 150, "hp": 150, "atk": 12, "def": 8},
                "mage": {"max_hp": 80, "hp": 80, "atk": 25, "def": 3},
                "rogue": {"max_hp": 100, "hp": 100, "atk": 18, "def": 5}
            }
            stats = class_stats.get(choice, class_stats["warrior"])
            max_stamina = get_max_stamina(1)
            
            user_data.update({
                "rpg_class": choice.capitalize(),
                "max_hp": stats["max_hp"], "hp": stats["hp"],
                "atk": stats["atk"], "def": stats["def"],
                "stamina": max_stamina, "max_stamina": max_stamina,
                "last_stamina_update": now_str,
                "level": 1, "xp": 0, "coins": 100,
                "kills": 0, "deaths": 0
            })
            db.update_user(user_id, user_data)
            await bot.answer_callback_query(call.id, f"✅ Kamu memilih {choice.capitalize()}!")
            await bot.edit_message_text(
                f"✨ Kamu memilih {choice.capitalize()}!\n\nGunakan /adventure untuk mulai.",
                chat_id, msg_id
            )
            return
        
        # ========== KEMBALI KE PROFIL ==========
        elif data == "rpg_back_stats":
            await show_profile(chat_id, user_id, call.from_user.first_name, msg_id, is_callback=True)
            await bot.answer_callback_query(call.id)
            return
        
        # ========== MULAI ADVENTURE ==========
        elif data == "rpg_adventure_start":
            user_data = db.get_user(user_id)
            user_data = check_and_regen_stamina(user_data)
            
            if user_data.get("hp", 0) <= 0:
                await bot.answer_callback_query(call.id, "❌ HP kamu 0! Heal dulu.", show_alert=True)
                return
            if user_id in active_battles:
                battle = active_battles[user_id]
                await bot.answer_callback_query(call.id, f"⚔️ Kamu sedang melawan {battle['monster']['name']}!", show_alert=True)
                return
            
            stamina_ok, user_data = consume_stamina(user_data, ADVENTURE_STAMINA_COST)
            if not stamina_ok:
                await bot.answer_callback_query(call.id, "❌ Stamina tidak cukup!", show_alert=True)
                return
            
            db.update_user(user_id, user_data)
            monster = get_random_monster(user_data.get("level", 1))
            monster["max_hp"] = monster["hp"]
            
            active_battles[user_id] = {
                "monster": monster,
                "monster_hp": monster["hp"],
                "chat_id": chat_id,
                "message_id": msg_id,
                "start_time": now
            }
            await bot.answer_callback_query(call.id, "🏃 Adventure dimulai!")
            await show_battle_screen(chat_id, msg_id, user_id, user_data, monster["name"])
            return
        
        # ========== SERANG ==========
        elif data.startswith("rpg_atk_"):
            monster_name = data.replace("rpg_atk_", "")
            if user_id not in active_battles:
                await bot.answer_callback_query(call.id, "❌ Battle sudah selesai!", show_alert=True)
                await show_profile(chat_id, user_id, call.from_user.first_name, msg_id, is_callback=True)
                return
            
            battle = active_battles[user_id]
            user_data = db.get_user(user_id)
            
            stamina_ok, user_data = consume_stamina(user_data, ATTACK_STAMINA_COST)
            if not stamina_ok:
                await bot.answer_callback_query(call.id, "❌ Stamina habis!", show_alert=True)
                return
            
            monster = battle["monster"]
            p_atk, p_def = get_player_stats(user_data)
            
            dmg_multiplier = 1
            weapon = user_data.get("weapon") or {}
            if weapon.get("effect") == "double_damage" and random.random() < 0.2:
                dmg_multiplier = 2
            elif weapon.get("effect") == "critical" and random.random() < 0.25:
                dmg_multiplier = 1.5
            
            dmg_to_monster = int((p_atk + random.randint(1, 10)) * dmg_multiplier)
            
            if weapon.get("effect") == "freeze" and random.random() < 0.15:
                dmg_to_player = 0
            elif weapon.get("effect") == "ranged":
                dmg_to_player = max(1, monster["atk"] - (p_def // 2)) // 2
            else:
                dmg_to_player = max(1, monster["atk"] - (p_def // 2))
            
            battle["monster_hp"] = max(0, battle["monster_hp"] - dmg_to_monster)
            user_data["hp"] = max(0, user_data["hp"] - dmg_to_player)
            
            if user_data["hp"] <= 0:
                loss = int(user_data.get("coins", 0) * 0.1)
                user_data["coins"] = max(0, user_data["coins"] - loss)
                user_data["deaths"] = user_data.get("deaths", 0) + 1
                db.update_user(user_id, user_data)
                del active_battles[user_id]
                await bot.answer_callback_query(call.id, "💀 Kamu tewas!")
                msg = f"💀 TEWAS!\n\nDikalahkan oleh {monster['name']}.\n💸 Kehilangan {loss} koin."
                await safe_edit_message(chat_id, msg_id, msg)
                return
            
            elif battle["monster_hp"] <= 0:
                user_data["xp"] = user_data.get("xp", 0) + monster["xp"]
                user_data["coins"] = user_data.get("coins", 0) + monster["coins"]
                user_data["kills"] = user_data.get("kills", 0) + 1
                
                loot_msg = ""
                if random.random() < 0.4:
                    loot_item = monster.get("loot", "Batu Aneh")
                    inv = user_data.get("inventory", [])
                    inv.append(loot_item)
                    user_data["inventory"] = inv
                    loot_msg = f"\n📦 Loot: {loot_item}"
                
                leveled_up, new_level = check_level_up(user_data)
                level_msg = f"\n🎉 LEVEL UP! Sekarang Level {new_level}!" if leveled_up else ""
                
                user_data["last_stamina_update"] = datetime.now().isoformat()
                db.update_user(user_id, user_data)
                del active_battles[user_id]
                
                await bot.answer_callback_query(call.id, "✅ Menang!")
                msg = (
                    f"✅ MENANG!\n\nMengalahkan {monster['name']}!\n"
                    f"💰 +{monster['coins']} Koin\n🌟 +{monster['xp']} XP"
                    f"{loot_msg}{level_msg}"
                )
                await safe_edit_message(chat_id, msg_id, msg)
                return
            else:
                db.update_user(user_id, user_data)
                await bot.answer_callback_query(call.id, f"⚔️ Serangan: -{dmg_to_monster}")
                await show_battle_screen(chat_id, msg_id, user_id, user_data, monster_name,
                                         last_dmg_player=dmg_to_player, last_dmg_monster=dmg_to_monster)
                return
        
        # ========== LARI DARI BATTLE ==========
        elif data == "rpg_run":
            if user_id not in active_battles:
                await bot.answer_callback_query(call.id, "❌ Tidak ada battle!", show_alert=True)
                return
            battle = active_battles[user_id]
            del active_battles[user_id]
            user_data = db.get_user(user_id)
            max_stamina = user_data.get("max_stamina", BASE_STAMINA)
            user_data["stamina"] = max(0, user_data.get("stamina", max_stamina) - RUN_STAMINA_PENALTY)
            user_data["last_stamina_update"] = datetime.now().isoformat()
            db.update_user(user_id, user_data)
            await bot.answer_callback_query(call.id, "🏃 Kamu kabur!")
            msg = f"🏃 Kamu kabur dari {battle['monster']['name']}!\nKehilangan {RUN_STAMINA_PENALTY} stamina."
            await safe_edit_message(chat_id, msg_id, msg)
            return
        
        # ========== POTION SAAT BATTLE ==========
        elif data == "rpg_use_potion_quick":
            user_data = db.get_user(user_id)
            level = user_data.get("level", 1)
            inventory = user_data.get("inventory", [])
            if "Healing Potion" not in inventory:
                await bot.answer_callback_query(call.id, "❌ Tidak punya Potion!", show_alert=True)
                if user_id in active_battles:
                    battle = active_battles[user_id]
                    await show_battle_screen(chat_id, msg_id, user_id, user_data, battle["monster"]["name"])
                return
            
            _, heal_effect, _, _ = get_potion_prices_and_effects(level)
            inventory.remove("Healing Potion")
            user_data["inventory"] = inventory
            user_data["hp"] = min(user_data.get("max_hp", 100), user_data.get("hp", 0) + heal_effect)
            db.update_user(user_id, user_data)
            await bot.answer_callback_query(call.id, f"🧪 +{heal_effect} HP!")
            if user_id in active_battles:
                battle = active_battles[user_id]
                await show_battle_screen(chat_id, msg_id, user_id, user_data, battle["monster"]["name"])
            else:
                await bot.send_message(chat_id, f"🧪 GULP! HP Sekarang: {user_data['hp']}/{user_data['max_hp']}")
            return
        
        # ========== HEAL ==========
        elif data == "rpg_heal":
            user_data = db.get_user(user_id)
            if user_data.get("coins", 0) >= HEAL_COST:
                user_data["coins"] -= HEAL_COST
                user_data["hp"] = user_data.get("max_hp", 100)
                db.update_user(user_id, user_data)
                await bot.answer_callback_query(call.id, "💖 HP Pulih!")
                await show_profile(chat_id, user_id, call.from_user.first_name, msg_id, is_callback=True)
            else:
                await bot.answer_callback_query(call.id, "❌ Koin tidak cukup!", show_alert=True)
            return
        
        # ========== ISTIRAHAT ==========
        elif data == "rpg_rest":
            user_data = db.get_user(user_id)
            user_data = check_and_regen_stamina(user_data)
            last_rest = user_data.get("last_rest")
            if last_rest:
                last_time = datetime.fromisoformat(last_rest)
                if now < last_time + timedelta(minutes=REST_COOLDOWN_MINUTES):
                    remaining = (last_time + timedelta(minutes=REST_COOLDOWN_MINUTES)) - now
                    minutes = remaining.seconds // 60
                    await bot.answer_callback_query(call.id, f"⏳ Tunggu {minutes} menit", show_alert=True)
                    return
            max_stamina = user_data.get("max_stamina", BASE_STAMINA)
            user_data["stamina"] = min(max_stamina, user_data.get("stamina", 0) + REST_STAMINA_GAIN)
            user_data["last_rest"] = now.isoformat()
            user_data["last_stamina_update"] = now.isoformat()
            db.update_user(user_id, user_data)
            await bot.answer_callback_query(call.id, f"💤 +{REST_STAMINA_GAIN} Stamina!")
            await show_profile(chat_id, user_id, call.from_user.first_name, msg_id, is_callback=True)
            return
        
        # ========== INVENTORY ==========
        elif data == "rpg_inv":
            user_data = db.get_user(user_id)
            inventory = user_data.get("inventory", [])
            item_counts = Counter(inventory)
            safe_name = clean_text(call.from_user.first_name)
            
            weapon = user_data.get("weapon") or {}
            armor = user_data.get("armor") or {}
            weapon_name = weapon.get("name", "Tidak ada")
            armor_name = armor.get("name", "Tidak ada")
            
            msg = (
                f"🎒 INVENTORY: {safe_name}\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"💰 Koin: {user_data.get('coins', 0)}\n"
                f"🗡 Weapon terpasang: {clean_text(weapon_name)}\n"
                f"🛡 Armor terpasang: {clean_text(armor_name)}\n"
                f"━━━━━━━━━━━━━━━━━━━━\n\n"
            )
            if not inventory:
                msg += "(Kosong)"
            else:
                for item, count in item_counts.items():
                    emoji = get_item_emoji(item) if item in ITEM_CONFIG else "🧪" if item == "Healing Potion" else "⚡"
                    if item == "Healing Potion":
                        sell_price = int((BASE_HEAL_PRICE + user_data.get("level", 1)*2) * 0.8)
                    elif item == "Energy Drink":
                        sell_price = int((BASE_ENERGY_PRICE + user_data.get("level", 1)*3) * 0.8)
                    else:
                        config = ITEM_CONFIG.get(item, {})
                        sell_price = config.get("sell_price", 0)
                    safe_item = clean_text(item)
                    msg += f"{emoji} {safe_item} (x{count}) - Jual: {sell_price}💰\n"
            
            markup = InlineKeyboardMarkup(row_width=3)
            for item in item_counts.keys():
                safe_item = clean_text(item)
                if item in ["Healing Potion", "Energy Drink"]:
                    markup.add(InlineKeyboardButton(f"🧪 Pakai {safe_item}", callback_data=f"use_{item}"))
                markup.add(
                    InlineKeyboardButton(f"💰 Jual 1", callback_data=f"sell_{item}_1"),
                    InlineKeyboardButton(f"💰 Jual Semua", callback_data=f"sell_{item}_all")
                )
            markup.add(
                InlineKeyboardButton("🔄 Ganti Senjata", callback_data="rpg_equip_weapon"),
                InlineKeyboardButton("🔄 Ganti Armor", callback_data="rpg_equip_armor")
            )
            markup.add(InlineKeyboardButton("⬅️ Kembali ke Profil", callback_data="rpg_back_stats"))
            
            await safe_edit_message(chat_id, msg_id, msg, reply_markup=markup)
            await bot.answer_callback_query(call.id)
            return
        
        # ========== EQUIP WEAPON ==========
        elif data == "rpg_equip_weapon":
            user_data = db.get_user(user_id)
            inventory = user_data.get("inventory", [])
            available = [wp for wp in _BASE_WEAPONS if wp["name"] in inventory]
            if not available:
                await bot.answer_callback_query(call.id, "❌ Tidak ada senjata di inventory!", show_alert=True)
                return
            
            markup = InlineKeyboardMarkup(row_width=1)
            for wp in available:
                scaled_wp = get_scaled_weapon(wp, user_data.get("level", 1))
                markup.add(InlineKeyboardButton(f"{wp['name']} (ATK +{scaled_wp['atk']})", callback_data=f"equip_wp_{wp['id']}"))
            markup.add(InlineKeyboardButton("⬅️ Kembali", callback_data="rpg_inv"))
            await safe_edit_message(chat_id, msg_id, "🗡 Pilih senjata yang ingin dipasang:", reply_markup=markup)
            await bot.answer_callback_query(call.id)
            return
        
        elif data.startswith("equip_wp_"):
            wp_id = data.replace("equip_wp_", "")
            user_data = db.get_user(user_id)
            for wp in _BASE_WEAPONS:
                if wp["id"] == wp_id:
                    inventory = user_data.get("inventory", [])
                    if wp["name"] not in inventory:
                        await bot.answer_callback_query(call.id, "❌ Senjata tidak ada!", show_alert=True)
                        return
                    old_weapon = user_data.get("weapon")
                    scaled_wp = get_scaled_weapon(wp, user_data.get("level", 1))
                    user_data["weapon"] = {"name": wp["name"], "atk": scaled_wp["atk"]}
                    if wp.get("effect"):
                        user_data["weapon"]["effect"] = wp["effect"]
                    if old_weapon and old_weapon.get("name") != "Tidak ada":
                        inventory.append(old_weapon["name"])
                    inventory.remove(wp["name"])
                    user_data["inventory"] = inventory
                    db.update_user(user_id, user_data)
                    await bot.answer_callback_query(call.id, f"✅ Memasang {wp['name']}!")
                    break
            await main_callback_handler(call)
            return
        
        # ========== EQUIP ARMOR ==========
        elif data == "rpg_equip_armor":
            user_data = db.get_user(user_id)
            inventory = user_data.get("inventory", [])
            available = [ar for ar in _BASE_ARMORS if ar["name"] in inventory]
            if not available:
                await bot.answer_callback_query(call.id, "❌ Tidak ada armor di inventory!", show_alert=True)
                return
            
            markup = InlineKeyboardMarkup(row_width=1)
            for ar in available:
                scaled_ar = get_scaled_armor(ar, user_data.get("level", 1))
                markup.add(InlineKeyboardButton(f"{ar['name']} (DEF +{scaled_ar['def']})", callback_data=f"equip_ar_{ar['id']}"))
            markup.add(InlineKeyboardButton("⬅️ Kembali", callback_data="rpg_inv"))
            await safe_edit_message(chat_id, msg_id, "🛡 Pilih armor yang ingin dipasang:", reply_markup=markup)
            await bot.answer_callback_query(call.id)
            return
        
        elif data.startswith("equip_ar_"):
            ar_id = data.replace("equip_ar_", "")
            user_data = db.get_user(user_id)
            for ar in _BASE_ARMORS:
                if ar["id"] == ar_id:
                    inventory = user_data.get("inventory", [])
                    if ar["name"] not in inventory:
                        await bot.answer_callback_query(call.id, "❌ Armor tidak ada!", show_alert=True)
                        return
                    old_armor = user_data.get("armor")
                    scaled_ar = get_scaled_armor(ar, user_data.get("level", 1))
                    user_data["armor"] = {"name": ar["name"], "def": scaled_ar["def"]}
                    if old_armor and old_armor.get("name") != "Tidak ada":
                        inventory.append(old_armor["name"])
                    inventory.remove(ar["name"])
                    user_data["inventory"] = inventory
                    db.update_user(user_id, user_data)
                    await bot.answer_callback_query(call.id, f"✅ Memasang {ar['name']}!")
                    break
            await main_callback_handler(call)
            return
        
        # ========== JUAL ITEM ==========
        elif data.startswith("sell_"):
            parts = data.split("_")
            item_name = "_".join(parts[1:-1])
            quantity = parts[-1]
            user_data = db.get_user(user_id)
            level = user_data.get("level", 1)
            inventory = user_data.get("inventory", [])
            
            if item_name == "Healing Potion":
                sell_price = int((BASE_HEAL_PRICE + level*2) * 0.8)
            elif item_name == "Energy Drink":
                sell_price = int((BASE_ENERGY_PRICE + level*3) * 0.8)
            else:
                config = ITEM_CONFIG.get(item_name, {})
                sell_price = config.get("sell_price", 0)
            
            if item_name not in inventory:
                await bot.answer_callback_query(call.id, f"❌ Tidak ada {clean_text(item_name)}!", show_alert=True)
                return
            
            if quantity == "1":
                inventory.remove(item_name)
                total_sell = sell_price
                await bot.answer_callback_query(call.id, f"✅ Menjual 1 {clean_text(item_name)} seharga {total_sell} koin!")
            else:
                count = inventory.count(item_name)
                inventory = [i for i in inventory if i != item_name]
                total_sell = sell_price * count
                await bot.answer_callback_query(call.id, f"✅ Menjual {count} {clean_text(item_name)} seharga {total_sell} koin!")
            
            user_data["inventory"] = inventory
            user_data["coins"] = user_data.get("coins", 0) + total_sell
            db.update_user(user_id, user_data)
            await main_callback_handler(call)
            return
        
        # ========== GUNAKAN ITEM ==========
        elif data.startswith("use_"):
            item_name = data.replace("use_", "")
            user_data = db.get_user(user_id)
            level = user_data.get("level", 1)
            inventory = user_data.get("inventory", [])
            
            if item_name not in inventory:
                await bot.answer_callback_query(call.id, f"❌ Tidak ada {clean_text(item_name)}!", show_alert=True)
                return
            
            if item_name == "Healing Potion":
                if user_data.get("hp", 0) >= user_data.get("max_hp", 100):
                    await bot.answer_callback_query(call.id, "❌ HP sudah penuh!", show_alert=True)
                    return
                _, heal_effect, _, _ = get_potion_prices_and_effects(level)
                inventory.remove(item_name)
                user_data["inventory"] = inventory
                user_data["hp"] = min(user_data.get("max_hp", 100), user_data.get("hp", 0) + heal_effect)
                db.update_user(user_id, user_data)
                await bot.answer_callback_query(call.id, f"🧪 +{heal_effect} HP!")
            elif item_name == "Energy Drink":
                max_stamina = user_data.get("max_stamina", BASE_STAMINA)
                if user_data.get("stamina", 0) >= max_stamina:
                    await bot.answer_callback_query(call.id, "❌ Stamina sudah penuh!", show_alert=True)
                    return
                _, _, _, energy_effect = get_potion_prices_and_effects(level)
                inventory.remove(item_name)
                user_data["inventory"] = inventory
                user_data["stamina"] = min(max_stamina, user_data.get("stamina", 0) + energy_effect)
                user_data["last_stamina_update"] = datetime.now().isoformat()
                db.update_user(user_id, user_data)
                await bot.answer_callback_query(call.id, f"⚡ +{energy_effect} Stamina!")
            else:
                await bot.answer_callback_query(call.id, "❌ Item tidak bisa digunakan!", show_alert=True)
                return
            
            await main_callback_handler(call)
            return
        
        # ========== SHOP OPEN ==========
        elif data == "rpg_shop_open":
            user_data = db.get_user(user_id)
            coins = user_data.get("coins", 0)
            level = user_data.get("level", 1)
            
            heal_price, heal_effect, energy_price, energy_effect = get_potion_prices_and_effects(level)
            
            msg = f"🛒 SHOP (Level {level})\n━━━━━━━━━━━━━━━━━━━━\n💰 Koin: {coins}\n\n⚔️ SEMUA SENJATA:\n"
            markup = InlineKeyboardMarkup(row_width=1)
            
            # Urutkan senjata berdasarkan tier lalu harga
            sorted_weapons = sorted(_BASE_WEAPONS, key=lambda x: (x.get("tier", 1), x["base_price"]))
            for base_wp in sorted_weapons:
                req = base_wp.get("req_level", 1)
                if level >= req:
                    scaled_wp = get_scaled_weapon(base_wp, level)
                    msg += f"🗡 {base_wp['name']} - {scaled_wp['price']}💰 (+{scaled_wp['atk']} ATK)\n"
                    markup.add(InlineKeyboardButton(f"Beli {base_wp['name']} ({scaled_wp['price']})", callback_data=f"rpgbuy_wp_{base_wp['id']}"))
                else:
                    msg += f"🔒 {base_wp['name']} - Level {req}\n"
            
            msg += "\n🛡 SEMUA ARMOR:\n"
            sorted_armors = sorted(_BASE_ARMORS, key=lambda x: (x.get("tier", 1), x["base_price"]))
            for base_ar in sorted_armors:
                req = base_ar.get("req_level", 1)
                if level >= req:
                    scaled_ar = get_scaled_armor(base_ar, level)
                    msg += f"🛡 {base_ar['name']} - {scaled_ar['price']}💰 (+{scaled_ar['def']} DEF)\n"
                    markup.add(InlineKeyboardButton(f"Beli {base_ar['name']} ({scaled_ar['price']})", callback_data=f"rpgbuy_ar_{base_ar['id']}"))
                else:
                    msg += f"🔒 {base_ar['name']} - Level {req}\n"
            
            msg += f"\n🧪 ITEM KONSUMSI:\n"
            msg += f"🧪 Healing Potion: +{heal_effect} HP - {heal_price}💰\n"
            msg += f"⚡ Energy Drink: +{energy_effect} Stamina - {energy_price}💰"
            markup.add(
                InlineKeyboardButton(f"Beli Potion ({heal_price})", callback_data="rpgbuy_pot_heal"),
                InlineKeyboardButton(f"Beli Energy ({energy_price})", callback_data="rpgbuy_pot_stamina")
            )
            markup.add(InlineKeyboardButton("⬅️ Kembali ke Profil", callback_data="rpg_back_stats"))
            
            await safe_edit_message(chat_id, msg_id, msg, reply_markup=markup)
            await bot.answer_callback_query(call.id)
            return
        
        # ========== BELI ITEM RPG ==========
        elif data.startswith("rpgbuy_"):
            user_data = db.get_user(user_id)
            level = user_data.get("level", 1)
            item = data.replace("rpgbuy_", "")
            
            if item == "pot_heal":
                heal_price, heal_effect, _, _ = get_potion_prices_and_effects(level)
                if user_data.get("coins", 0) >= heal_price:
                    user_data["coins"] -= heal_price
                    inv = user_data.get("inventory", [])
                    inv.append("Healing Potion")
                    user_data["inventory"] = inv
                    db.update_user(user_id, user_data)
                    await bot.answer_callback_query(call.id, f"✅ Membeli Healing Potion (+{heal_effect} HP)!")
                else:
                    await bot.answer_callback_query(call.id, "❌ Koin tidak cukup!", show_alert=True)
            elif item == "pot_stamina":
                _, _, energy_price, energy_effect = get_potion_prices_and_effects(level)
                if user_data.get("coins", 0) >= energy_price:
                    user_data["coins"] -= energy_price
                    inv = user_data.get("inventory", [])
                    inv.append("Energy Drink")
                    user_data["inventory"] = inv
                    db.update_user(user_id, user_data)
                    await bot.answer_callback_query(call.id, f"✅ Membeli Energy Drink (+{energy_effect} Stamina)!")
                else:
                    await bot.answer_callback_query(call.id, "❌ Koin tidak cukup!", show_alert=True)
            elif item.startswith("wp_"):
                wp_id = item
                found = False
                for base_wp in _BASE_WEAPONS:
                    if base_wp["id"] == wp_id:
                        found = True
                        scaled_wp = get_scaled_weapon(base_wp, level)
                        if user_data.get("coins", 0) >= scaled_wp["price"]:
                            user_data["coins"] -= scaled_wp["price"]
                            inv = user_data.get("inventory", [])
                            inv.append(base_wp["name"])
                            user_data["inventory"] = inv
                            db.update_user(user_id, user_data)
                            await bot.answer_callback_query(call.id, f"✅ Membeli {base_wp['name']}! Cek inventory.")
                        else:
                            await bot.answer_callback_query(call.id, "❌ Koin tidak cukup!", show_alert=True)
                        break
                if not found:
                    await bot.answer_callback_query(call.id, "❌ Item tidak tersedia!", show_alert=True)
            elif item.startswith("ar_"):
                ar_id = item
                found = False
                for base_ar in _BASE_ARMORS:
                    if base_ar["id"] == ar_id:
                        found = True
                        scaled_ar = get_scaled_armor(base_ar, level)
                        if user_data.get("coins", 0) >= scaled_ar["price"]:
                            user_data["coins"] -= scaled_ar["price"]
                            inv = user_data.get("inventory", [])
                            inv.append(base_ar["name"])
                            user_data["inventory"] = inv
                            db.update_user(user_id, user_data)
                            await bot.answer_callback_query(call.id, f"✅ Membeli {base_ar['name']}! Cek inventory.")
                        else:
                            await bot.answer_callback_query(call.id, "❌ Koin tidak cukup!", show_alert=True)
                        break
                if not found:
                    await bot.answer_callback_query(call.id, "❌ Item tidak tersedia!", show_alert=True)
            
            await main_callback_handler(call)
            return
        
    except Exception as e:
        logger.error(f"Error in callback: {e}")
        await bot.answer_callback_query(call.id, "❌ Error!", show_alert=True)

print("✅ RPG Module v6.1 - Weapons/Armors Scale 3% per User Level")