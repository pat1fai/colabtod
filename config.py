import os
import pytz

# Токен вашого Telegram бота від @BotFather
BOT_TOKEN = os.getenv("BOT_TOKEN", "8687663427:AAFEcyQ6R_UeDb224PU8E5egaLbx2CGMyK8")

# Часовий пояс навчального закладу (Київ)
TIMEZONE = pytz.timezone("Europe/Kyiv")

# Порт для внутрішнього веб-сервера Telegram Mini App
PORT = int(os.getenv("PORT", 8080))

# Посилання на Telegram Web App (GitHub Pages)
WEBAPP_URL = os.getenv("WEBAPP_URL", "https://pat1fai.github.io/colabtod/")
