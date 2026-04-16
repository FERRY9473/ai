import datetime
import pytz
from config import TZ

def get_now():
    """Get current time in Jakarta timezone"""
    jakarta_tz = pytz.timezone(TZ)
    return datetime.datetime.now(jakarta_tz)

def format_time(dt=None, fmt="%H:%M:%S"):
    """Format time to HH:MM:SS"""
    if dt is None:
        dt = get_now()
    return dt.strftime(fmt)

def format_date(dt=None, fmt="%d/%m/%Y"):
    """Format date to DD/MM/YYYY"""
    if dt is None:
        dt = get_now()
    return dt.strftime(fmt)

def clean_markdown(text):
    """Clean markdown characters to prevent parsing errors"""
    chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in chars:
        text = text.replace(char, f'\\{char}')
    return text

def get_greeting():
    """Get greeting based on current hour in Jakarta"""
    h = get_now().hour
    if 4 <= h < 11:
        return "Pagi"
    elif 11 <= h < 15:
        return "Siang"
    elif 15 <= h < 18:
        return "Sore"
    else:
        return "Malam"
