from core.bot import bot, safe_reply
from database.db import db
from telebot import types
import asyncio
import random

# Game state for Connect 4
# connect4_games = { chat_id: { board: [[]], turn: 0, players: [], names: [], status: 'waiting', msg_id: int } }
connect4_games = {}

# Constants
ROWS = 6
COLS = 7

def render_board(board):
    """Visualizes the 7x6 board with emojis."""
    res = ""
    # We display from top (row 5) to bottom (row 0)
    for r in range(ROWS-1, -1, -1):
        row_str = ""
        for c in range(COLS):
            val = board[r][c]
            if val == 0: row_str += "⚪"
            elif val == 1: row_str += "🔴"
            else: row_str += "🔵"
        res += row_str + "\n"
    return res

def check_win(board, p):
    """Check if player p (1 or 2) has 4 in a row."""
    # Horizontal
    for r in range(ROWS):
        for c in range(COLS - 3):
            if board[r][c] == board[r][c+1] == board[r][c+2] == board[r][c+3] == p: return True
    # Vertical
    for r in range(ROWS - 3):
        for c in range(COLS):
            if board[r][c] == board[r+1][c] == board[r+2][c] == board[r+3][c] == p: return True
    # Diagonal Up
    for r in range(ROWS - 3):
        for c in range(COLS - 3):
            if board[r][c] == board[r+1][c+1] == board[r+2][c+2] == board[r+3][c+3] == p: return True
    # Diagonal Down
    for r in range(3, ROWS):
        for c in range(COLS - 3):
            if board[r][c] == board[r-1][c+1] == board[r-2][c+2] == board[r-3][c+3] == p: return True
    return False

@bot.message_handler(commands=['c4', 'connect4'])
async def c4_start(message):
    chat_id = message.chat.id
    if chat_id in connect4_games and connect4_games[chat_id]['status'] != 'finished':
        return await safe_reply(message, "Game sedang berjalan!")

    connect4_games[chat_id] = {
        "board": [[0 for _ in range(COLS)] for _ in range(ROWS)],
        "players": [],
        "names": [],
        "turn": 0,
        "status": "waiting",
        "msg_id": None
    }

    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("Gabung Game ⚪", callback_data=f"c4_join_{chat_id}"))
    
    msg = await bot.send_message(chat_id, "🎮 *CONNECT 4*\n\nSusun 4 koin sebaris!\nMenunggu pemain (0/2)...", 
                               parse_mode='Markdown', reply_markup=keyboard)
    connect4_games[chat_id]['msg_id'] = msg.message_id

@bot.callback_query_handler(func=lambda call: call.data.startswith('c4_'))
async def c4_callback(call):
    data = call.data.split('_')
    action = data[1]
    chat_id = int(data[2])

    if chat_id not in connect4_games:
        return await bot.answer_callback_query(call.id, "Game kadaluarsa.")

    game = connect4_games[chat_id]
    user_id = call.from_user.id
    user_name = call.from_user.first_name

    if action == 'join':
        if len(game['players']) >= 2:
            return await bot.answer_callback_query(call.id, "Game penuh.")
        if user_id in game['players']:
            return await bot.answer_callback_query(call.id, "Sudah bergabung.")

        game['players'].append(user_id)
        game['names'].append(user_name)
        
        if len(game['players']) == 1:
            await bot.edit_message_text(f"🎮 *CONNECT 4*\n\nMenunggu pemain (1/2)...\n1. {user_name}", 
                                      chat_id, game['msg_id'], parse_mode='Markdown', reply_markup=call.message.reply_markup)
        else:
            game['status'] = 'playing'
            if random.choice([True, False]):
                game['players'].reverse()
                game['names'].reverse()
            
            p1, p2 = game['names']
            msg = f"🎮 *GAME DIMULAI!*\n\n🔴: {p1}\n🔵: {p2}\n\nGiliran: 🔴 {p1}\n\n" + render_board(game['board'])
            
            keyboard = types.InlineKeyboardMarkup(row_width=7)
            buttons = [types.InlineKeyboardButton(f"{i+1}", callback_data=f"c4_drop_{chat_id}_{i}") for i in range(COLS)]
            keyboard.add(*buttons)
            
        try:
            await bot.edit_message_text(msg, chat_id, game['msg_id'], parse_mode='Markdown', reply_markup=keyboard)
        except Exception as e:
            if "message is not modified" not in str(e).lower():
                import logging
                logging.error(f"C4 Update Error: {e}")
        await bot.answer_callback_query(call.id)

    elif action == 'drop':
        if game['status'] != 'playing': return await bot.answer_callback_query(call.id)
        
        player_idx = game['turn'] % 2
        if user_id != game['players'][player_idx]:
            return await bot.answer_callback_query(call.id, "Bukan giliranmu!")

        col = int(data[3])
        # Find first empty row in column
        row = -1
        for r in range(ROWS):
            if game['board'][r][col] == 0:
                row = r
                break
        
        if row == -1:
            return await bot.answer_callback_query(call.id, "Kolom penuh!")

        p_val = player_idx + 1
        game['board'][row][col] = p_val
        game['turn'] += 1
        
        if check_win(game['board'], p_val):
            game['status'] = 'finished'
            
            # ECONOMY: Reward Winner
            user_data = db.get_user(user_id)
            user_data["coins"] = user_data.get("coins", 0) + 50
            user_data["xp"] = user_data.get("xp", 0) + 20
            db.update_user(user_id, user_data)
            
            msg = f"🏆 *PEMENANG: {user_name.upper()}!*\n🎁 Hadiah: +50 Koin, +20 XP\n\n" + render_board(game['board'])
            await bot.edit_message_text(msg, chat_id, game['msg_id'], parse_mode='Markdown', reply_markup=None)
            del connect4_games[chat_id]
        elif game['turn'] == ROWS * COLS:
            game['status'] = 'finished'
            msg = "🤝 *HASIL: SERI!*\n\n" + render_board(game['board'])
            await bot.edit_message_text(msg, chat_id, game['msg_id'], parse_mode='Markdown', reply_markup=None)
            del connect4_games[chat_id]
        else:
            next_idx = game['turn'] % 2
            next_name = game['names'][next_idx]
            next_emoji = "🔴" if next_idx == 0 else "🔵"
            p1, p2 = game['names']
            
            msg = f"🎮 *CONNECT 4*\n\n🔴: {p1}\n🔵: {p2}\n\nGiliran: {next_emoji} {next_name}\n\n" + render_board(game['board'])
            
            keyboard = types.InlineKeyboardMarkup(row_width=7)
            buttons = [types.InlineKeyboardButton(f"{i+1}", callback_data=f"c4_drop_{chat_id}_{i}") for i in range(COLS)]
            keyboard.add(*buttons)
        try:
            await bot.edit_message_text(msg, chat_id, game['msg_id'], parse_mode='Markdown', reply_markup=keyboard)
        except Exception as e:
            if "message is not modified" not in str(e).lower():
                import logging
                logging.error(f"C4 Update Error: {e}")
            
        await bot.answer_callback_query(call.id)

@bot.message_handler(commands=['stopc4'])
async def stop_c4(message):
    chat_id = message.chat.id
    if chat_id in connect4_games:
        del connect4_games[chat_id]
        await safe_reply(message, "Game Connect 4 telah dihentikan.")
    else:
        await safe_reply(message, "Tidak ada game Connect 4 yang berjalan.")
