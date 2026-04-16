from core.bot import bot, safe_reply
from telebot import types
import asyncio
import random
import time
from database.db import db

# Game states
math_games = {}
dice_battles = {}
typing_games = {}

# --- HELPER FUNCTIONS ---
def update_coins(user_id, amount, xp=0):
    user_data = db.get_user(user_id)
    user_data["coins"] = user_data.get("coins", 0) + amount
    if xp > 0:
        user_data["xp"] = user_data.get("xp", 0) + xp
        # Level Up Check
        new_level = (user_data["xp"] // 100) + 1
        user_data["level"] = new_level
    db.update_user(user_id, user_data)
    return user_data["coins"]

# --- 1. SLOT MACHINE ---
@bot.message_handler(commands=['slots', 'slot'])
async def slot_machine(message):
    user_id = message.from_user.id
    args = message.text.split()
    
    bet = 10
    if len(args) > 1 and args[1].isdigit():
        bet = int(args[1])
    
    if bet < 10:
        return await safe_reply(message, "❌ Minimal taruhan adalah 10 koin.")
    
    user_data = db.get_user(user_id)
    if user_data.get("coins", 0) < bet:
        return await safe_reply(message, f"❌ Koin tidak cukup! Saldo: `{user_data.get('coins', 0)}`")

    # Deduct bet first
    update_coins(user_id, -bet)
    
    # Send slot animation
    msg = await bot.send_dice(message.chat.id, emoji='🎰')
    value = msg.dice.value
    
    # Telegram Slot values (1-64)
    # Win conditions for slots (777 is 64, but there are other combinations)
    # 1, 22, 43, 64 are jackpots (777)
    jackpots = [1, 22, 43, 64]
    wins = [7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, # Some other combos
            28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42]
    
    await asyncio.sleep(4) # Wait for animation
    
    if value in jackpots:
        reward = bet * 10
        new_bal = update_coins(user_id, reward, xp=100)
        await bot.reply_to(message, f"🎰 **JACKPOT 777!!** 🎰\n\nSelamat! Kamu menang besar!\n💰 Hadiah: +`{reward}` koin\n✨ XP: +100\nSaldo sekarang: `{new_bal}`")
    elif value in [2, 3, 4, 5, 6]: # Small wins
        reward = bet * 2
        new_bal = update_coins(user_id, reward, xp=20)
        await bot.reply_to(message, f"🎰 **MENANG!**\n\nLumayan nih!\n💰 Hadiah: +`{reward}` koin\nSaldo sekarang: `{new_bal}`")
    else:
        await bot.reply_to(message, f"🎰 **KALAH!**\n\nJangan menyerah, coba lagi!\n💸 Kamu kehilangan `{bet}` koin.")

# --- 2. MATH CHALLENGE ---
@bot.message_handler(commands=['hitung', 'math'])
async def math_start(message):
    chat_id = message.chat.id
    if chat_id in math_games:
        return await safe_reply(message, "Masih ada soal yang belum terjawab!")

    a = random.randint(1, 50)
    b = random.randint(1, 50)
    op = random.choice(['+', '-', '*'])
    
    if op == '+': result = a + b
    elif op == '-': result = a - b
    else: 
        a = random.randint(1, 15)
        b = random.randint(1, 10)
        result = a * b

    bet = 20 # Standard bet
    math_games[chat_id] = {
        "result": result,
        "bet": bet,
        "time": time.time()
    }
    
    await safe_reply(message, f"🔢 **MATH CHALLENGE**\n\nBerapa hasil dari:\n`{a} {op} {b} = ?` \n\nWaktu: 15 detik! (Taruhan: {bet} koin)")
    
    await asyncio.sleep(15)
    if chat_id in math_games:
        del math_games[chat_id]
        await bot.send_message(chat_id, f"⏰ **WAKTU HABIS!**\nJawabannya adalah `{result}`. Tidak ada yang menang.")

@bot.message_handler(func=lambda m: m.chat.id in math_games and m.text and m.text.lstrip('-').isdigit())
async def handle_math_answer(message):
    chat_id = message.chat.id
    game = math_games[chat_id]
    
    if int(message.text) == game['result']:
        user_id = message.from_user.id
        user_name = message.from_user.first_name
        
        user_data = db.get_user(user_id)
        if user_data.get("coins", 0) < game['bet']:
            # If they don't have coins but answered right, they still get a small reward
            reward = 5
        else:
            reward = game['bet']
            
        new_bal = update_coins(user_id, reward, xp=40)
        del math_games[chat_id]
        await safe_reply(message, f"✅ **BENAR!**\n\n*{user_name}* sangat cepat!\n💰 Hadiah: +`{reward}` koin\n✨ XP: +40")
    else:
        # Penalize for wrong answer?
        user_id = message.from_user.id
        update_coins(user_id, -5) # Lose 5 coins for wrong answer
        # Don't delete game, let others try

# --- 3. DICE BATTLE ---
@bot.message_handler(commands=['dice', 'dadu', 'duel'])
async def dice_battle(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    args = message.text.split()
    
    bet = 50
    if len(args) > 1 and args[1].isdigit():
        bet = int(args[1])
        
    user_data = db.get_user(user_id)
    if user_data.get("coins", 0) < bet:
        return await safe_reply(message, f"❌ Koin tidak cukup! Min: `{bet}`")

    if message.reply_to_message:
        target_id = message.reply_to_message.from_user.id
        if target_id == user_id: return
        if message.reply_to_message.from_user.is_bot:
             # Lawan Bot
             my_dice = await bot.send_dice(chat_id)
             await asyncio.sleep(3)
             bot_dice = await bot.send_dice(chat_id)
             await asyncio.sleep(3)
             
             if my_dice.dice.value > bot_dice.dice.value:
                 new_bal = update_coins(user_id, bet, xp=30)
                 await bot.reply_to(message, f"🏆 **KAMU MENANG!**\n\nKamu: `{my_dice.dice.value}` vs Bot: `{bot_dice.dice.value}`\n💰 Hadiah: +`{bet}` koin")
             elif my_dice.dice.value < bot_dice.dice.value:
                 new_bal = update_coins(user_id, -bet)
                 await bot.reply_to(message, f"💀 **KAMU KALAH!**\n\nKamu: `{my_dice.dice.value}` vs Bot: `{bot_dice.dice.value}`\n💸 Kehilangan: `{bet}` koin")
             else:
                 await bot.reply_to(message, "🤝 **SERI!**\nKoin dikembalikan.")
             return

        # Pvp Battle Request
        target_name = message.reply_to_message.from_user.first_name
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("Terima Tantangan 🤝", callback_data=f"dice_acc_{user_id}_{target_id}_{bet}"))
        
        await bot.send_message(chat_id, f"🎲 **TANTANGAN DUEL DADU**\n\n*{message.from_user.first_name}* menantang *{target_name}* bertaruh `{bet}` koin!\nApakah berani?", reply_markup=markup)
    else:
        # Solo vs Bot
        my_dice = await bot.send_dice(chat_id)
        await asyncio.sleep(3)
        bot_dice = await bot.send_dice(chat_id)
        await asyncio.sleep(3)
        
        if my_dice.dice.value > bot_dice.dice.value:
            new_bal = update_coins(user_id, bet, xp=30)
            await bot.reply_to(message, f"🏆 **MENANG!**\n\nKamu: `{my_dice.dice.value}` vs Bot: `{bot_dice.dice.value}`\n💰 Hadiah: +`{bet}` koin")
        elif my_dice.dice.value < bot_dice.dice.value:
            new_bal = update_coins(user_id, -bet)
            await bot.reply_to(message, f"💀 **KALAH!**\n\nKamu: `{my_dice.dice.value}` vs Bot: `{bot_dice.dice.value}`\n💸 Kehilangan: `{bet}` koin")
        else:
            await bot.reply_to(message, "🤝 **SERI!**")

@bot.callback_query_handler(func=lambda call: call.data.startswith("dice_acc_"))
async def dice_callback(call):
    _, _, challenger_id, target_id, bet = call.data.split("_")
    challenger_id = int(challenger_id)
    target_id = int(target_id)
    bet = int(bet)
    
    if call.from_user.id != target_id:
        return await bot.answer_callback_query(call.id, "Bukan kamu yang ditantang!", show_alert=True)
    
    # Check both balances
    c_data = db.get_user(challenger_id)
    t_data = db.get_user(target_id)
    
    if c_data.get("coins", 0) < bet or t_data.get("coins", 0) < bet:
        return await bot.answer_callback_query(call.id, "Koin salah satu pemain tidak cukup!", show_alert=True)

    await bot.edit_message_text("🎲 **DUEL DIMULAI!** Melempar dadu...", call.message.chat.id, call.message.message_id)
    
    d1 = await bot.send_dice(call.message.chat.id)
    await asyncio.sleep(3)
    d2 = await bot.send_dice(call.message.chat.id)
    await asyncio.sleep(3)
    
    v1, v2 = d1.dice.value, d2.dice.value
    
    if v1 > v2:
        update_coins(challenger_id, bet, xp=50)
        update_coins(target_id, -bet)
        winner = c_data.get("first_name", "Challenger")
    elif v2 > v1:
        update_coins(target_id, bet, xp=50)
        update_coins(challenger_id, -bet)
        winner = t_data.get("first_name", "Target")
    else:
        winner = None # Draw
        
    if winner:
        await bot.send_message(call.message.chat.id, f"🏆 **{winner} MENANG!**\n\nSkor: `{v1}` vs `{v2}`\n💰 Mendapatkan `{bet}` koin dari lawan!")
    else:
        await bot.send_message(call.message.chat.id, f"🤝 **HASIL SERI!** `{v1}` vs `{v2}`\nTidak ada koin yang berpindah.")

# --- 4. TYPING RACE ---
SENTENCES = [
    "Kucing yang sedang tidur di atas kursi itu sangat lucu sekali.",
    "Bekerja keras di masa muda akan membuahkan hasil manis di masa tua.",
    "Teknologi kecerdasan buatan berkembang sangat pesat tahun ini.",
    "Jangan pernah menyerah sebelum mencoba yang terbaik setiap hari.",
    "Pergi ke pasar membeli sayur dan buah untuk dimasak ibu nanti malam."
]

@bot.message_handler(commands=['ketik', 'type', 'race'])
async def typing_start(message):
    chat_id = message.chat.id
    if chat_id in typing_games: return
    
    sentence = random.choice(SENTENCES)
    bet = 30
    typing_games[chat_id] = {"text": sentence, "bet": bet}
    
    await bot.send_message(chat_id, f"⌨️ **TYPING RACE**\n\nKetik kalimat di bawah ini secepat mungkin!\n\n`{sentence}`\n\n🎁 Hadiah: {bet} koin & 60 XP")
    
    await asyncio.sleep(30)
    if chat_id in typing_games:
        del typing_games[chat_id]
        await bot.send_message(chat_id, "⏰ **WAKTU HABIS!** Tidak ada yang berhasil mengetik tepat waktu.")

@bot.message_handler(func=lambda m: m.chat.id in typing_games and m.text)
async def handle_typing_answer(message):
    chat_id = message.chat.id
    game = typing_games[chat_id]
    
    if message.text.strip() == game['text']:
        user_id = message.from_user.id
        user_name = message.from_user.first_name
        
        reward = game['bet']
        new_bal = update_coins(user_id, reward, xp=60)
        del typing_games[chat_id]
        await safe_reply(message, f"🏆 **PEMENANG!**\n\n*{user_name}* menang adu mengetik!\n💰 Hadiah: +`{reward}` koin\n✨ XP: +60")
    # No penalty for typing race to keep it fun
