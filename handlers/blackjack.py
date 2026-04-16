from core.bot import bot, safe_reply
from telebot import types
import random
import asyncio
from database.db import db

# Multiplayer Blackjack state
# bj_multi = { chat_id: { players: [], hands: {}, names: {}, turn: 0, deck: [], dealer_hand: [], status: 'waiting', msg_id: int } }
bj_multi = {}

SUITS = ['♥️', '♦️', '♣️', '♠️']
RANKS = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']

def create_deck():
    deck = []
    for s in SUITS:
        for r in RANKS:
            deck.append(f"{r}{s}")
    random.shuffle(deck)
    return deck

def calculate_score(hand):
    score = 0
    aces = 0
    for card in hand:
        rank = card[:-2] if card.startswith('10') else card[0]
        if rank in ['J', 'Q', 'K']:
            score += 10
        elif rank == 'A':
            aces += 1
            score += 11
        else:
            score += int(rank)
    
    while score > 21 and aces:
        score -= 10
        aces -= 1
    return score

# Unicode Card Mapping (U+1F0A0 - U+1F0DF)
UNICODE_CARDS = {
    'S': { # Spades
        'A': '🂡', '2': '🂢', '3': '🂣', '4': '🂤', '5': '🂥', '6': '🂦', '7': '🂧', '8': '🂨', '9': '🂩', '10': '🂪', 'J': '🂫', 'Q': '🂭', 'K': '🂮'
    },
    'H': { # Hearts
        'A': '🂱', '2': '🂲', '3': '🂳', '4': '🂴', '5': '🂵', '6': '🂶', '7': '🂷', '8': '🂸', '9': '🂹', '10': '🂺', 'J': '🂻', 'Q': '🂽', 'K': '🂾'
    },
    'D': { # Diamonds
        'A': '🃁', '2': '🃂', '3': '🃃', '4': '🃄', '5': '🃅', '6': '🃆', '7': '🃇', '8': '🃈', '9': '🃉', '10': '🃊', 'J': '🃋', 'Q': '🃍', 'K': '🃎'
    },
    'C': { # Clubs
        'A': '🃑', '2': '🃒', '3': '🃓', '4': '🃔', '5': '🃕', '6': '🃖', '7': '🃗', '8': '🃘', '9': '🃙', '10': '🃚', 'J': '🃛', 'Q': '🃝', 'K': '🃞'
    }
}

SUIT_MAP = {'♠️': 'S', '♥️': 'H', '♦️': 'D', '♣️': 'C'}

def get_unicode_card(card):
    # card looks like '10♥️' or 'A♠️'
    suit_symbol = card[-2:] if card.startswith('10') else card[-2:]
    # Wait, suit emoji is actually often 2 chars in unicode (emoji + variant)
    # Let's be safer with how we extract it
    rank = card[:-2]
    suit = SUIT_MAP.get(suit_symbol, 'S')
    return UNICODE_CARDS[suit].get(rank, '🂠')

def render_hand(hand, hide_first=False):
    if hide_first:
        return f"<code> 🂠 </code>  <code> {get_unicode_card(hand[1])} </code>"
    
    res = ""
    for card in hand:
        res += f"<code> {get_unicode_card(card)} </code>  "
    return res.strip()

@bot.message_handler(commands=['blackjack', 'bj'])
async def bj_start(message):
    chat_id = message.chat.id
    if chat_id in bj_multi and bj_multi[chat_id]['status'] != 'finished':
        return await safe_reply(message, "Ada meja Blackjack yang sedang aktif! Gunakan /stopbj untuk reset.")

    bj_multi[chat_id] = {
        "players": [],
        "hands": {},
        "names": {},
        "turn": 0,
        "deck": create_deck(),
        "dealer_hand": [],
        "status": "waiting",
        "msg_id": None
    }

    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("Gabung Meja 🃏", callback_data=f"bjm_join_{chat_id}"))
    
    msg = await bot.send_message(chat_id, "🃏 <b>BLACKJACK MULTIPLAYER</b>\n\nKlik tombol di bawah buat gabung!\nMinimal 1, Maksimal 5 pemain.", 
                               parse_mode='HTML', reply_markup=keyboard)
    bj_multi[chat_id]['msg_id'] = msg.message_id

@bot.callback_query_handler(func=lambda call: call.data.startswith('bjm_'))
async def bjm_callback(call):
    data = call.data.split('_')
    action = data[1]
    chat_id = int(data[2])

    if chat_id not in bj_multi:
        return await bot.answer_callback_query(call.id, "Meja sudah bubar.")

    game = bj_multi[chat_id]
    user_id = call.from_user.id
    user_name = call.from_user.first_name

    if action == 'join':
        if game['status'] != 'waiting':
            return await bot.answer_callback_query(call.id, "Game sudah mulai.")
        if user_id in game['players']:
            return await bot.answer_callback_query(call.id, "Kamu sudah di meja.")
        if len(game['players']) >= 5:
            return await bot.answer_callback_query(call.id, "Meja penuh.")

        game['players'].append(user_id)
        game['names'][user_id] = user_name
        
        count = len(game['players'])
        player_list = "\n".join([f"👤 {game['names'][pid]}" for pid in game['players']])
        
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton("Gabung 🃏", callback_data=f"bjm_join_{chat_id}"))
        keyboard.add(types.InlineKeyboardButton("Mulai Game 🚀", callback_data=f"bjm_start_{chat_id}"))
        
        await bot.edit_message_text(
            f"🃏 <b>BLACKJACK MULTIPLAYER</b>\n\nMenunggu pemain ({count}/5)...\n\nPemain:\n{player_list}", 
            chat_id, game['msg_id'], parse_mode='HTML', reply_markup=keyboard
        )
        await bot.answer_callback_query(call.id, "Kamu bergabung ke meja!")

    elif action == 'start':
        if user_id not in game['players']:
            return await bot.answer_callback_query(call.id, "Hanya pemain yang bisa mulai.")
        
        # Start Game
        game['status'] = 'playing'
        # Deal initial cards
        for pid in game['players']:
            game['hands'][pid] = [game['deck'].pop(), game['deck'].pop()]
        game['dealer_hand'] = [game['deck'].pop(), game['deck'].pop()]
        
        await render_bj_status(chat_id)
        await bot.answer_callback_query(call.id, "Kartu dibagikan!")

    elif action == 'secret':
        if user_id not in game['hands']:
            return await bot.answer_callback_query(call.id, "Kamu tidak ikut main.", show_alert=True)
        
        hand = game['hands'][user_id]
        score = calculate_score(hand)
        cards_str = render_hand(hand)
        await bot.answer_callback_query(call.id, f"🃏 Kartu Kamu:\n{cards_str}\n\n📊 Skor: {score}", show_alert=True)

    elif action == 'hit':
        current_player = game['players'][game['turn']]
        if user_id != current_player:
            return await bot.answer_callback_query(call.id, "Bukan giliranmu!")
        
        game['hands'][user_id].append(game['deck'].pop())
        score = calculate_score(game['hands'][user_id])
        
        if score > 21:
            await bot.answer_callback_query(call.id, f"💥 BUST! Skor kamu {score}. Kamu kalah!", show_alert=True)
            await next_bj_turn(chat_id)
        else:
            await bot.answer_callback_query(call.id, f"🃏 Kartu ditambahkan! Skor: {score}", show_alert=True)
            await render_bj_status(chat_id)

    elif action == 'stand':
        current_player = game['players'][game['turn']]
        if user_id != current_player:
            return await bot.answer_callback_query(call.id, "Bukan giliranmu!")
        
        await bot.answer_callback_query(call.id, "Kamu memilih Stand.")
        await next_bj_turn(chat_id)

async def render_bj_status(chat_id):
    game = bj_multi[chat_id]
    current_player_id = game['players'][game['turn']]
    current_player_name = game['names'][current_player_id]
    
    dealer_display = render_hand(game['dealer_hand'], hide_first=True)
    
    player_list = ""
    for pid in game['players']:
        status = " (Sedang jalan...)" if pid == current_player_id else ""
        hand = game['hands'][pid]
        score = calculate_score(hand)
        if score > 21: status = " (💀 BUST)"
        player_list += f"├ {game['names'][pid]}{status}\n"

    msg = (
        "🃏 <b>MEJA BLACKJACK AKTIF</b>\n\n"
        f"Dealer: {dealer_display}\n\n"
        f"Pemain:\n{player_list}\n"
        f"👉 Giliran: <b>{current_player_name}</b>\n\n"
        "Gunakan tombol di bawah untuk melihat kartu atau beraksi!"
    )
    
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("👁‍🗨 Lihat Kartu Saya", callback_data=f"bjm_secret_{chat_id}"))
    keyboard.add(
        types.InlineKeyboardButton("Hit ➕", callback_data=f"bjm_hit_{chat_id}"),
        types.InlineKeyboardButton("Stand ✋", callback_data=f"bjm_stand_{chat_id}")
    )
    
    try:
        await bot.edit_message_text(msg, chat_id, game['msg_id'], parse_mode='HTML', reply_markup=keyboard)
    except Exception as e:
        if "message is not modified" not in str(e).lower():
            logging.error(f"BJ Status Error: {e}")

async def next_bj_turn(chat_id):
    game = bj_multi[chat_id]
    game['turn'] += 1
    
    if game['turn'] >= len(game['players']):
        await finish_bj_game(chat_id)
    else:
        # Check if next player already bust (shouldn't happen in initial deal, but for consistency)
        await render_bj_status(chat_id)

async def finish_bj_game(chat_id):
    game = bj_multi[chat_id]
    game['status'] = 'finished'
    
    # Dealer plays
    d_score = calculate_score(game['dealer_hand'])
    while d_score < 17:
        game['dealer_hand'].append(game['deck'].pop())
        d_score = calculate_score(game['dealer_hand'])
    
    dealer_cards = render_hand(game['dealer_hand'])
    
    res_msg = f"🃏 <b>BLACKJACK - HASIL AKHIR</b>\n\n"
    res_msg += f"Dealer: {dealer_cards} (Skor: {d_score})\n\n"
    
    for pid in game['players']:
        p_hand = game['hands'][pid]
        p_score = calculate_score(p_hand)
        p_name = game['names'][pid]
        cards_str = render_hand(p_hand)
        
        result = ""
        coins = 0
        if p_score > 21:
            result = "💀 <b>BUST</b>"
        elif d_score > 21 or p_score > d_score:
            result = "🏆 <b>MENANG</b>"
            coins = 50
        elif p_score < d_score:
            result = "💸 <b>KALAH</b>"
        else:
            result = "🤝 <b>SERI</b>"
            
        if coins > 0:
            u_data = db.get_user(pid)
            u_data['coins'] = u_data.get('coins', 0) + coins
            u_data['xp'] = u_data.get('xp', 0) + 20
            db.update_user(pid, u_data)
            result += " (+50 💰)"
            
        res_msg += f"├ {p_name}: {cards_str} ({p_score}) -> {result}\n"
    
    await bot.edit_message_text(res_msg, chat_id, game['msg_id'], parse_mode='HTML', reply_markup=None)
    del bj_multi[chat_id]

@bot.message_handler(commands=['stopbj'])
async def stop_bj(message):
    chat_id = message.chat.id
    if chat_id in bj_multi:
        del bj_multi[chat_id]
        await safe_reply(message, "Meja Blackjack telah dibubarkan.")
    else:
        await safe_reply(message, "Tidak ada meja Blackjack yang aktif.")
