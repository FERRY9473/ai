import random
import asyncio
import logging
from services.ai_engine import ask_ai

logger = logging.getLogger("RPG_Engine")

class RPGEngine:
    def __init__(self):
        self.monsters = [
            {"name": "Slime Hijau", "min_level": 1, "hp": 30, "atk": 5, "xp": 25, "coins": 15, "loot": "Lendir Slime"},
            {"name": "Goblin Pencuri", "min_level": 1, "hp": 50, "atk": 10, "xp": 50, "coins": 40, "loot": "Belati Berkarat"},
            {"name": "Serigala Hutan", "min_level": 2, "hp": 70, "atk": 15, "xp": 70, "coins": 30, "loot": "Taring Serigala"},
            {"name": "Orc Prajurit", "min_level": 5, "hp": 150, "atk": 25, "xp": 150, "coins": 100, "loot": "Gada Kayu Besar"},
            {"name": "Shadow Assassin", "min_level": 8, "hp": 200, "atk": 45, "xp": 300, "coins": 250, "loot": "Permata Hitam"},
            {"name": "Naga Api", "min_level": 15, "hp": 800, "atk": 80, "xp": 2000, "coins": 1500, "loot": "Sisik Naga"},
        ]
        
        self.events = [
            "menemukan mata air suci",
            "terjebak dalam lubang lumpur",
            "melihat pedagang misterius yang lewat",
            "menemukan peti harta karun tua",
            "mendengar suara auman dari kejauhan"
        ]

    async def generate_story(self, user_name, target_name, action="bertemu"):
        """Generate a dramatic story using AI"""
        prompt = (
            f"Buatlah narasi RPG fantasi sangat singkat (1-2 kalimat). "
            f"Karakter: {user_name}. Kejadian: Sedang menjelajah dan {action} {target_name}. "
            f"Gunakan bahasa Indonesia yang seru dan menegangkan."
        )
        try:
            story = await ask_ai(prompt, system_prompt="Kamu adalah Dungeon Master RPG yang kejam tapi adil.")
            return story
        except:
            return f"{user_name} sedang berjalan di hutan gelap dan tiba-tiba {target_name} muncul dari balik semak!"

    def get_random_monster(self, user_level):
        possible = [m for m in self.monsters if m["min_level"] <= user_level + 2]
        return random.choice(possible) if possible else self.monsters[0]

    def get_random_event(self):
        return random.choice(self.events)

rpg_engine = RPGEngine()
