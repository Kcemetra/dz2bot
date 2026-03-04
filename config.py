import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
NINJAS_API_KEY = os.getenv("NINJAS_API_KEY")

if not all([BOT_TOKEN, WEATHER_API_KEY, GEMINI_API_KEY, NINJAS_API_KEY]):
    raise ValueError("Не все API ключи заданы в .env")