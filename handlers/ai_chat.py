from core.bot import bot, safe_reply
from services.ai_engine import ask_ai
from services.rag_engine import rag
from database.db import db
import logging
import os

# Configuration
MAX_HISTORY = 20

@bot.message_handler(content_types=['document'])
async def handle_document(message):
    if message.document.mime_type == 'application/pdf':
        m = await safe_reply(message, "Memproses PDF...")

        # Download file
        file_info = await bot.get_file(message.document.file_id)
        downloaded_file = await bot.download_file(file_info.file_path)

        file_path = f"ai/database/{message.document.file_name}"
        with open(file_path, 'wb') as new_file:
            new_file.write(downloaded_file)

        # Process PDF
        res = await rag.process_pdf(file_path)

        # Cleanup
        if os.path.exists(file_path):
            os.remove(file_path)

        await bot.edit_message_text(res, m.chat.id, m.message_id)

@bot.message_handler(commands=['ask', 'ai', 'tanya'])
async def handle_ai(message):
    query = message.text.split(maxsplit=1)
    if len(query) < 2:
        # Check if it's a reply to a PDF question
        if not (message.reply_to_message and message.reply_to_message.text):
            return await safe_reply(message, "Ketik pertanyaanmu. Contoh: /ai [pertanyaan]")
        prompt = message.text # Use current text if reply
    else:
        prompt = query[1]

    chat_id = str(message.chat.id)
    m = await safe_reply(message, "...")

    # 1. Search RAG Context
    context_chunks = await rag.search(prompt)
    context_text = "\n".join(context_chunks)

    # 2. Get User Stats from DB
    user_data = db.get_user(message.from_user.id)
    coins = user_data.get("coins", 0)
    xp = user_data.get("xp", 0)
    level = (xp // 100) + 1
    display_name = message.from_user.first_name
    system_prompt = user_data.get("system_prompt")

    # 3. Add Profile to Prompt for Personal AI
    user_context = f"[INFO USER: Nama={display_name}, Koin={coins}, XP={xp}, Level={level}]\n\n"
    full_prompt = user_context + prompt
    
    if context_text:
        full_prompt += f"\n\nKonteks Dokumen:\n{context_text}"
    elif message.chat.type in ['group', 'supergroup']:
        full_prompt = user_context + f"{display_name}: {prompt}"

    # 4. Ask AI with History
    history = db.history.get(chat_id, [])
    try:
        response = await ask_ai(full_prompt, history=history, system_prompt=system_prompt)
    except Exception as e:
        logging.error(f"Error calling AI: {e}")
        response = "Kesalahan dalam memproses permintaan."

    # 5. Update History
    new_history = list(history)
    # Truncate prompt in history to keep context clean
    history_prompt = full_prompt if len(full_prompt) < 2000 else full_prompt[:2000] + "..."
    new_history.append({"role": "user", "content": history_prompt})
    new_history.append({"role": "assistant", "content": response})
    
    # Prune history if too long
    if len(new_history) > MAX_HISTORY:
        new_history = new_history[-MAX_HISTORY:]
    
    # Save to DB
    db.history[chat_id] = new_history
    
    # Handle long responses or markdown errors
    try:
        # Try to edit the "..." message with the response
        if len(response) <= 4000:
            await bot.edit_message_text(response, m.chat.id, m.message_id, parse_mode=None)
        else:
             await bot.edit_message_text("Jawaban terlalu panjang. Mengirim dalam beberapa bagian...", m.chat.id, m.message_id)
             for i in range(0, len(response), 4000):
                 await bot.send_message(message.chat.id, response[i:i+4000], parse_mode=None)
    except Exception as e:
        logging.error(f"Error editing message: {e}")
        # If edit fails (e.g. response too long or other reason), send as new message
        if len(response) > 4000:
             for i in range(0, len(response), 4000):
                 await bot.send_message(message.chat.id, response[i:i+4000], parse_mode=None)
        else:
             await bot.send_message(message.chat.id, response, parse_mode=None)

@bot.message_handler(commands=['resetai', 'clearchat'])
async def reset_ai_handler(message):
    chat_id = str(message.chat.id)
    if chat_id in db.history:
        del db.history[chat_id]
    await safe_reply(message, "Memori dihapus. Siap.")

@bot.message_handler(commands=['resetpdf', 'clearpdf'])
async def reset_pdf_handler(message):
    res = rag.clear_index()
    await safe_reply(message, res)

@bot.message_handler(commands=['setprompt', 'personality'])
async def set_prompt_handler(message):
    """Set custom AI personality for the user"""
    query = message.text.split(maxsplit=1)
    if len(query) < 2:
        return await safe_reply(message, "Gunakan: `/setprompt [deskripsi kepribadian]`\n\nContoh: `/setprompt Jadilah asisten yang dingin dan cuek.`")
    
    new_prompt = query[1]
    user_data = db.get_user(message.from_user.id)
    user_data["system_prompt"] = new_prompt
    db.update_user(message.from_user.id, user_data)
    
    await safe_reply(message, f"✅ Kepribadian AI Anda berhasil diatur menjadi:\n\n`{new_prompt}`")

@bot.message_handler(commands=['resetprompt'])
async def reset_prompt_handler(message):
    """Reset AI personality to default"""
    user_id = message.from_user.id
    user_data = db.get_user(user_id)
    if "system_prompt" in user_data:
        del user_data["system_prompt"]
        db.update_user(user_id, user_data)
    await safe_reply(message, "✅ Kepribadian AI telah dikembalikan ke default (Aphrodite).")

# Optional: Handle direct messages in private
@bot.message_handler(func=lambda m: m.chat.type == 'private' and not m.text.startswith('/'))
async def private_chat_ai(message):
    chat_id = str(message.chat.id)
    prompt = message.text
    
    # Send typing action
    await bot.send_chat_action(message.chat.id, 'typing')
    
    user_data = db.get_user(message.from_user.id)
    system_prompt = user_data.get("system_prompt")
    
    history = db.history.get(chat_id, [])
    try:
        response = await ask_ai(prompt, history=history, system_prompt=system_prompt)
    except Exception as e:
        logging.error(f"Error calling AI: {e}")
        response = "Kesalahan dalam memproses permintaan."
    
    # Update History
    new_history = list(history)
    history_prompt = prompt if len(prompt) < 2000 else prompt[:2000] + "..."
    new_history.append({"role": "user", "content": history_prompt})
    new_history.append({"role": "assistant", "content": response})
    if len(new_history) > MAX_HISTORY:
        new_history = new_history[-MAX_HISTORY:]
    db.history[chat_id] = new_history
    
    if len(response) <= 4000:
        await safe_reply(message, response, parse_mode=None)
    else:
        for i in range(0, len(response), 4000):
            await bot.send_message(message.chat.id, response[i:i+4000], parse_mode=None)

# Handle Tags and Replies in Groups
@bot.message_handler(func=lambda m: m.chat.type in ['group', 'supergroup'] and (m.text or m.caption) and not (m.text or m.caption).startswith('/'))
async def group_auto_ai(message):
    # Fetch bot info asynchronously
    bot_info = await bot.get_me()
    bot_username = bot_info.username.lower()
    
    # Text or Caption
    msg_text = message.text or message.caption or ""
    
    # 1. Check if mentioned (Tag)
    is_mentioned = False
    
    # Primary check using entities
    entities = message.entities or message.caption_entities
    if entities:
        for entity in entities:
            if entity.type == 'mention':
                mention = msg_text[entity.offset:entity.offset+entity.length]
                if mention.lower() == f"@{bot_username}":
                    is_mentioned = True
                    break
            elif entity.type == 'text_mention':
                if entity.user and entity.user.id == bot_info.id:
                    is_mentioned = True
                    break
    
    # Fallback check (simple string search) if entities failed or were missing
    if not is_mentioned:
        if f"@{bot_username}" in msg_text.lower():
            is_mentioned = True
    
    # 2. Check if it's a reply to the bot's message
    is_reply_to_bot = False
    if message.reply_to_message and message.reply_to_message.from_user.id == bot_info.id:
        is_reply_to_bot = True

    if is_mentioned or is_reply_to_bot:
        chat_id = str(message.chat.id)
        # Clean the prompt (remove the tag if it exists)
        import re
        prompt = re.sub(f"@{bot_username}", "", msg_text, flags=re.IGNORECASE).strip()
        
        # If still empty but it was a mention, use the full text but stripped of username
        if not prompt and is_mentioned:
             prompt = msg_text.strip() # Fallback

        if not prompt and is_reply_to_bot:
             prompt = "Lanjutkan atau tanggapi pesan ini." # Fallback if only sticker/empty reply

        if not prompt: return # Ignore if empty

        await bot.send_chat_action(message.chat.id, 'typing')
        
        user_data = db.get_user(message.from_user.id)
        system_prompt = user_data.get("system_prompt")
        
        display_name = message.from_user.first_name
        full_prompt = f"{display_name}: {prompt}"
        
        history = db.history.get(chat_id, [])
        try:
            response = await ask_ai(full_prompt, history=history, system_prompt=system_prompt)
        except Exception as e:
            logging.error(f"Error calling AI: {e}")
            response = "Kesalahan dalam memproses permintaan."
        
        # Update History
        new_history = list(history)
        history_prompt = full_prompt if len(full_prompt) < 2000 else full_prompt[:2000] + "..."
        new_history.append({"role": "user", "content": history_prompt})
        new_history.append({"role": "assistant", "content": response})
        if len(new_history) > MAX_HISTORY:
            new_history = new_history[-MAX_HISTORY:]
        db.history[chat_id] = new_history
        
        if len(response) <= 4000:
            await safe_reply(message, response, parse_mode=None)
        else:
            for i in range(0, len(response), 4000):
                await bot.send_message(message.chat.id, response[i:i+4000], parse_mode=None)
