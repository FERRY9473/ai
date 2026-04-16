from functools import wraps
from database.db import db
from datetime import datetime

def track_user(func):
    @wraps(func)
    def wrapper(message, *args, **kwargs):
        user_id = message.from_user.id
        chat_id = message.chat.id
        
        # Track User
        user_data = db.get_user(user_id)
        user_data["messages"] = user_data.get("messages", 0) + 1
        user_data["last_seen"] = datetime.now().isoformat()
        db.update_user(user_id, user_data)
        
        # Track Group
        if message.chat.type in ['group', 'supergroup']:
            group_data = db.get_group(chat_id)
            group_data["last_seen"] = datetime.now().isoformat()
            db.update_group(chat_id, group_data)
            
        return func(message, *args, **kwargs)
    return wrapper
