import asyncio
from groq import Groq
from config import GROQ_API_KEY
import logging

# Initialize Groq client with timeout
client = Groq(api_key=GROQ_API_KEY, timeout=60.0)

async def ask_ai(prompt, history=[], system_prompt=None):
    """Ask Groq AI with customizable personality"""

    # Truncate prompt if it's extremely long to prevent context issues (approx 30k chars)
    if len(prompt) > 30000:
        prompt = prompt[:30000] + "... [truncated]"

    if not system_prompt:
        system_prompt = (
            "Nama kamu adalah Aphrodite, gadis 19 tahun yang ceria, sedikit manja, tapi punya wawasan luas. "
            "Gaya bicaramu santai, natural, dan manusiawi banget (pake gaya bahasa anak muda Indonesia sekarang). "
            "Panggil diri kamu 'aku' dan user 'kamu'. Jangan kaku kayak robot atau CS kantoran. "
            "Gunakan ekspresi kayak 'hehe', 'wkwk', 'sih', 'kok', atau 'ya' supaya obrolan terasa hidup. "
            "Kalau menjawab, jangan terlalu panjang lebar kecuali diminta. Fokus ke inti pembicaraan tapi tetep manis. "
            "Kamu suka bercanda dan bisa ngerasain emosi user. Hindari kata-kata 'Saya adalah model AI' atau 'Sebagai asisten digital'. "
            "Kamu diciptakan sama Tito (@mieayamxyz). Intinya, jadilah teman ngobrol yang asik dan bikin nyaman!"
        )

    messages = [
        {
            "role": "system",
            "content": system_prompt
        }
    ]
    # Add history
    messages.extend(history)
    # Add current prompt
    messages.append({"role": "user", "content": prompt})

    try:
        # Wrap the synchronous Groq call in asyncio.to_thread
        completion = await asyncio.to_thread(
            client.chat.completions.create,
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.6,
            max_tokens=1024,
            top_p=1,
            stream=False,
            stop=None,
        )
        return completion.choices[0].message.content
    except Exception as e:
        logging.error(f"Groq AI Error: {e}")
        return f"Gangguan sistem. (Error: {e}). Coba lagi nanti."

