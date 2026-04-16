from sqlitedict import SqliteDict
from config import DATABASE_PATH
import os

def get_db(table="main"):
    """Get a database table instance"""
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
    return SqliteDict(DATABASE_PATH, tablename=table, autocommit=True)

class DBManager:
    def __init__(self):
        self.users = get_db("users")
        self.groups = get_db("groups")
        self.settings = get_db("settings")
        self.history = get_db("history")
        self.group_users = get_db("group_users")

    def get_user(self, user_id):
        defaults = {
            "xp": 0,
            "coins": 0,
            "level": 1,
            "messages": 0,
            "last_seen": None,
            "warns": 0,
            "sholat_remind": False,
            "city": "jakarta",
            "first_name": None,
            "inventory": []
        }
        data = self.users.get(str(user_id), {})
        # Merge defaults with existing data to ensure all keys exist
        for k, v in defaults.items():
            if k not in data:
                data[k] = v
        return data

    def update_user(self, user_id, data):
        self.users[str(user_id)] = data

    def get_group(self, chat_id):
        defaults = {
            "welcome_enabled": True,
            "anti_link": False,
            "anti_spam": False,
            "rules": "Belum ada peraturan di grup ini.",
            "welcome_msg": None,
            "sholat_remind": False,
            "city": "jakarta",
            "title": None
        }
        data = self.groups.get(str(chat_id), {})
        for k, v in defaults.items():
            if k not in data:
                data[k] = v
        return data

    def update_group(self, chat_id, data):
        self.groups[str(chat_id)] = data

db = DBManager()
