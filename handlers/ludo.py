from core.bot import bot, safe_reply
from database.db import db
from telebot import types
import asyncio
import random
import logging

# Game state for Ludo
# ludo_games = { chat_id: { players: [], positions: {}, turn: 0, status: 'waiting', names: {}, msg_id: int } }
ludo_games = {}

# Constants
# Path mapping for 9x9 Plus-shaped board (32 steps to finish)
# Coordinates (row, col) from 0-8
LUDO_PATH = [
    (3,0), (3,1), (3,2), (3,3), (2,3), (1,3), (0,3), (0,4), 
    (0,5), (1,5), (2,5), (3,5), (3,6), (3,7), (3,8), (4,8), 
    (5,8), (5,7), (5,6), (5,5), (6,5), (7,5), (8,5), (8,4), 
    (8,3), (7,3), (6,3), (5,3), (5,2), (5,1), (5,0), (4,0),
    (4,4) # Finish at index 32
]

FINISH_STEP = 32
PLAYER_EMOJIS = ["🔴", "🔵", "🟢", "🟡"]
HOME_EMOJIS = ["🟥", "🟦", "🟩", "🟨"]

def render_ludo_board(game):
    """Visualizes the 9x9 grid board with colored homes and safety spots."""
    grid = [["▫️"] * 9 for _ in range(9)]
    for i, (r, c) in enumerate(LUDO_PATH):
        if i == FINISH_STEP: grid[r][c] = "🏆"
        elif i in [0, 8, 16, 24]: grid[r][c] = "✨"
        else: grid[r][c] = "⬜"
    homes = {
        (0,0): "🟥", (0,1): "🟥", (1,0): "🟥", (1,1): "🟥",
        (0,7): "🟩", (0,8): "🟩", (1,7): "🟩", (1,8): "🟩",
        (7,0): "🟦", (7,1): "🟦", (8,0): "🟦", (8,1): "🟦",
        (7,7): "🟨", (7,8): "🟨", (8,7): "🟨", (8,8): "🟨"
    }
    for (r, c), icon in homes.items(): grid[r][c] = icon
    for i, user_id in enumerate(game['players']):
        pos = game['positions'][user_id]
        r, c = LUDO_PATH[min(pos, FINISH_STEP)]
        grid[r][c] = PLAYER_EMOJIS[i]
    board_str = ""
    for row in grid: board_str += "".join(row) + "\n"
    return board_str

@bot.message_handler(commands=['ludo'])
async def ludo_start(message):
    chat_id = message.chat.id
    if chat_id in ludo_games and ludo_games[chat_id]['status'] == 'playing':
        return await safe_reply(message, "Game Ludo sedang berjalan di grup ini! Gunakan /stopludo jika ingin mengulang.")
    ludo_games[chat_id] = {"players": [], "positions": {}, "names": {}, "turn": 0, "status": "waiting", "msg_id": None}
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("Gabung Game 🎲", callback_data=f"ludo_join_{chat_id}"))
    msg = await bot.send_message(chat_id, "🎲 *LUDO GRID 9x9*\n\nKlik tombol di bawah untuk bergabung!\nMinimal 2 pemain, Maksimal 4.", reply_to_message_id=message.message_id, parse_mode='Markdown', reply_markup=keyboard)
    ludo_games[chat_id]['msg_id'] = msg.message_id

@bot.callback_query_handler(func=lambda call: call.data.startswith('ludo_'))
async def ludo_callback(call):
    data = call.data.split('_')
    action, chat_id = data[1], int(data[2])
    if chat_id not in ludo_games: return await bot.answer_callback_query(call.id, "Game sudah kadaluarsa.")
    game, user_id, user_name = ludo_games[chat_id], call.from_user.id, call.from_user.first_name
    if action == 'join':
        if game['status'] != 'waiting': return await bot.answer_callback_query(call.id, "Game sudah dimulai.")
        if user_id in game['players']: return await bot.answer_callback_query(call.id, "Kamu sudah bergabung!")
        if len(game['players']) >= 4: return await bot.answer_callback_query(call.id, "Game sudah penuh.")
        game['players'].append(user_id)
        game['names'][user_id], game['positions'][user_id] = user_name, 0
        count = len(game['players'])
        player_list = "\n".join([f"{PLAYER_EMOJIS[i]} {game['names'][pid]}" for i, pid in enumerate(game['players'])])
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton("Gabung Game 🎲", callback_data=f"ludo_join_{chat_id}"))
        if count >= 2: keyboard.add(types.InlineKeyboardButton("Mulai Game 🚀", callback_data=f"ludo_start_{chat_id}"))
        try:
            await bot.edit_message_text(f"🎲 *LUDO GRID 9x9*\n\nMenunggu pemain ({count}/4)...\n\nPemain:\n{player_list}", chat_id, game['msg_id'], parse_mode='Markdown', reply_markup=keyboard)
        except Exception as e:
            if "message is not modified" not in str(e).lower(): logging.error(f"Ludo Join Error: {e}")
        await bot.answer_callback_query(call.id, "Berhasil bergabung!")
    elif action == 'start':
        if user_id not in game['players']: return await bot.answer_callback_query(call.id, "Hanya pemain yang bisa memulai!")
        await start_ludo_game(chat_id)
        await bot.answer_callback_query(call.id, "Game dimulai!")
    elif action == 'roll':
        current_player_id = game['players'][game['turn'] % len(game['players'])]
        if user_id != current_player_id: return await bot.answer_callback_query(call.id, "Bukan giliranmu!")
        dice_msg = await bot.send_dice(chat_id)
        steps = dice_msg.dice.value
        await bot.edit_message_reply_markup(chat_id, game['msg_id'], reply_markup=None)
        await asyncio.sleep(3.5)
        old_pos = game['positions'][user_id]
        new_pos = min(old_pos + steps, FINISH_STEP)
        game['positions'][user_id] = new_pos
        kick_info = ""
        if 0 < new_pos < FINISH_STEP:
            for pid in game['players']:
                if pid != user_id and game['positions'][pid] == new_pos:
                    game['positions'][pid] = 0
                    kick_info = f"\n💥 *BOOM!* {game['names'][pid]} ditendang balik ke START!"
        try: await bot.delete_message(chat_id, dice_msg.message_id)
        except: pass
        if new_pos == FINISH_STEP:
            user_data = db.get_user(user_id)
            user_data["coins"], user_data["xp"] = user_data.get("coins", 0) + 100, user_data.get("xp", 0) + 50
            db.update_user(user_id, user_data)
            winner_name, board_view = game['names'][user_id], render_ludo_board(game)
            await bot.edit_message_text(f"🏆 *PEMENANG: {winner_name.upper()}!*\n🎁 Hadiah: +100 Koin, +50 XP\n\n{board_view}\nGame Selesai.", chat_id, game['msg_id'], parse_mode='Markdown', reply_markup=None)
            del ludo_games[chat_id]
        else:
            game['turn'] += 1
            next_idx = game['turn'] % len(game['players'])
            next_name, next_emoji, board_view = game['names'][game['players'][next_idx]], PLAYER_EMOJIS[next_idx], render_ludo_board(game)
            msg = f"🎲 *LUDO GRID 9x9*\n\n{board_view}\nTadi: {user_name} dapat angka {steps}.{kick_info}\n\nGiliran: {next_emoji} *{next_name}*"
            keyboard = types.InlineKeyboardMarkup()
            keyboard.add(types.InlineKeyboardButton(f"Kocok Dadu {next_emoji}", callback_data=f"ludo_roll_{chat_id}"))
            try:
                await bot.edit_message_text(msg, chat_id, game['msg_id'], parse_mode='Markdown', reply_markup=keyboard)
            except Exception as e:
                if "message is not modified" not in str(e).lower(): logging.error(f"Ludo Roll Error: {e}")
        await bot.answer_callback_query(call.id)

async def start_ludo_game(chat_id):
    game = ludo_games[chat_id]
    game['status'] = 'playing'
    first_name, board_view = game['names'][game['players'][0]], render_ludo_board(game)
    msg = f"🚀 *GAME DIMULAI!*\n\n{board_view}\nGiliran: {PLAYER_EMOJIS[0]} *{first_name}*"
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton(f"Kocok Dadu {PLAYER_EMOJIS[0]}", callback_data=f"ludo_roll_{chat_id}"))
    try:
        await bot.edit_message_text(msg, chat_id, game['msg_id'], parse_mode='Markdown', reply_markup=keyboard)
    except Exception as e:
        if "message is not modified" not in str(e).lower(): logging.error(f"Ludo Start Error: {e}")

@bot.message_handler(commands=['stopludo'])
async def stop_ludo(message):
    chat_id = message.chat.id
    if chat_id in ludo_games:
        del ludo_games[chat_id]
        await safe_reply(message, "Sesi Ludo telah dihentikan.")
    else:
        await safe_reply(message, "Tidak ada sesi Ludo yang sedang berjalan.")
