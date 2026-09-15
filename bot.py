import asyncio
import os
import sys

# Підтримка коректного виведення в консоль
if sys.platform == "win32":
    import io
    if hasattr(sys.stdout, 'buffer'):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    if hasattr(sys.stderr, 'buffer'):
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    WebAppInfo, MenuButtonWebApp
)
from aiogram.client.session.aiohttp import AiohttpSession

from config import BOT_TOKEN, WEBAPP_URL
from database import init_db, add_user, toggle_notifications
from schedule_service import get_day_schedule, get_current_and_next_pair
from notifier import notification_worker

# Автоматичне налаштування проксі для безкоштовного тарифу PythonAnywhere
proxy = os.getenv("http_proxy") or os.getenv("HTTP_PROXY")
if not proxy:
    # Перевірка, чи запущено на серверах PythonAnywhere
    if "PYTHONANYWHERE_DOMAIN" in os.environ or "PYTHONANYWHERE_SITE" in os.environ or os.path.exists("/var/log/pythonanywhere") or "pat1fai" in os.path.abspath(__file__):
        if not sys.platform.startswith("win"):
            proxy = "http://proxy.server:3128"

session = AiohttpSession(proxy=proxy) if proxy else None
if proxy:
    print(f"🌐 Використовується проксі PythonAnywhere: {proxy}")

bot = Bot(token=BOT_TOKEN, session=session)
dp = Dispatcher()

def get_main_keyboard():
    # Якщо вказано посилання HTTPS (наприклад, GitHub Pages), додаємо нативну кнопку Web App
    if WEBAPP_URL.startswith("https://"):
        app_button = KeyboardButton(text="📱 Відкрити розклад", web_app=WebAppInfo(url=WEBAPP_URL))
    else:
        app_button = KeyboardButton(text="📱 Відкрити розклад (Web App)")

    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="🕒 Поточна пара"),
                KeyboardButton(text="⏭ Наступна пара")
            ],
            [
                KeyboardButton(text="📅 Сьогодні"),
                KeyboardButton(text="📆 Завтра")
            ],
            [
                app_button
            ],
            [
                KeyboardButton(text="🔔 Налаштування сповіщень")
            ]
        ],
        resize_keyboard=True
    )

@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    await add_user(message.from_user.id, message.from_user.username, message.from_user.first_name)

    if WEBAPP_URL.startswith("https://"):
        try:
            await bot.set_chat_menu_button(
                chat_id=message.chat.id,
                menu_button=MenuButtonWebApp(text="Розклад", web_app=WebAppInfo(url=WEBAPP_URL))
            )
        except Exception as e:
            print(f"Помилка встановлення MenuButton: {e}")

    await message.answer(
        f"Привіт, <b>{message.from_user.first_name}</b>! 👋\n\n"
        "Я помічник з розкладу пар для групи <b>КМ 24-9-1</b> (ВСП ФК КрНУ).\n\n"
        "✨ <b>Можливості бота:</b>\n"
        "• 🔔 <b>Оповіщення за 5 хвилин</b> до кожної пари автоматично для всіх користувачів\n"
        "• 🕒 Перегляд поточної та наступної пари\n"
        "• 📅 Розклад на сьогодні та завтра\n"
        "• 📱 Преміальний додаток у стилі Apple (Mini App) за кнопкою нижче!\n\n"
        "Оберіть дію на клавіатурі нижче:",
        reply_markup=get_main_keyboard(),
        parse_mode="HTML"
    )

@dp.message(F.text == "🕒 Поточна пара")
async def show_current(message: types.Message):
    curr, _ = get_current_and_next_pair()
    if not curr:
        await message.answer("🌴 <b>Зараз пари немає!</b> Можна спокійно відпочивати.", parse_mode="HTML")
        return

    await message.answer(
        f"🟢 <b>Зараз триває {curr['pair']}-а пара:</b>\n\n"
        f"📚 <b>{curr['name']}</b> ({curr.get('type', 'Заняття')})\n"
        f"⏰ {curr['start']} – {curr['end']}\n"
        f"🚪 {curr.get('room', 'Аудиторія не вказана')}\n"
        f"👨‍🏫 {curr.get('teacher', 'Викладач не вказаний')}\n\n"
        f"📊 Пройшло: <b>{curr['progress']}%</b> | Залишилось: <b>{curr['minutes_left']} хв</b>",
        parse_mode="HTML"
    )

@dp.message(F.text == "⏭ Наступна пара")
async def show_next(message: types.Message):
    _, nxt = get_current_and_next_pair()
    if not nxt:
        await message.answer("✨ <b>На сьогодні всі пари закінчилися!</b> Гарного відпочинку.", parse_mode="HTML")
        return

    await message.answer(
        f"⏳ <b>Наступна {nxt['pair']}-а пара:</b>\n\n"
        f"📚 <b>{nxt['name']}</b> ({nxt.get('type', 'Заняття')})\n"
        f"⏰ Початок о <b>{nxt['start']}</b> (до {nxt['end']})\n"
        f"🚪 {nxt.get('room', 'Аудиторія не вказана')}\n"
        f"👨‍🏫 {nxt.get('teacher', 'Викладач не вказаний')}\n\n"
        f"⏳ До початку залишилося: <b>{nxt['minutes_until']} хв</b>",
        parse_mode="HTML"
    )

@dp.message(F.text == "📅 Сьогодні")
async def show_today(message: types.Message):
    data = get_day_schedule(0)
    if not data["pairs"]:
        await message.answer(f"🎉 <b>{data['day_name']} ({data['date']})</b>: пар немає!", parse_mode="HTML")
        return

    lines = [
        f"📅 <b>Розклад на сьогодні ({data['day_name']}, {data['date']}):</b>",
        f"🏷 <i>{data['week_label']}</i>\n"
    ]
    for p in data["pairs"]:
        lines.append(
            f"<b>{p['pair']}. {p['start']}–{p['end']}</b> — {p['name']}\n"
            f"   🚪 {p['room']} | 👨‍🏫 {p['teacher']}"
        )

    await message.answer("\n\n".join(lines), parse_mode="HTML")

@dp.message(F.text == "📆 Завтра")
async def show_tomorrow(message: types.Message):
    data = get_day_schedule(1)
    if not data["pairs"]:
        await message.answer(f"🎉 <b>Завтра ({data['day_name']}, {data['date']})</b>: пар немає!", parse_mode="HTML")
        return

    lines = [
        f"📆 <b>Розклад на завтра ({data['day_name']}, {data['date']}):</b>",
        f"🏷 <i>{data['week_label']}</i>\n"
    ]
    for p in data["pairs"]:
        lines.append(
            f"<b>{p['pair']}. {p['start']}–{p['end']}</b> — {p['name']}\n"
            f"   🚪 {p['room']} | 👨‍🏫 {p['teacher']}"
        )

    await message.answer("\n\n".join(lines), parse_mode="HTML")

@dp.message(F.text == "📱 Відкрити розклад (Web App)")
async def show_webapp_info(message: types.Message):
    await message.answer(
        f"📱 <b>Розклад у стилі Apple доступний за посиланням:</b>\n\n"
        f"👉 <a href=\"{WEBAPP_URL}\">{WEBAPP_URL}</a>",
        parse_mode="HTML"
    )

@dp.message(F.text == "🔔 Налаштування сповіщень")
async def toggle_notify(message: types.Message):
    status = await toggle_notifications(message.from_user.id)
    if status:
        await message.answer("🔔 <b>Сповіщення увімкнено!</b>\nВи будете отримувати нагадування за 5 хвилин до початку кожної пари.", parse_mode="HTML")
    else:
        await message.answer("🔕 <b>Сповіщення вимкнено.</b>\nВи більше не будете отримувати нагадування перед парами.", parse_mode="HTML")

async def main():
    print("⏳ Ініціалізація бази даних...")
    await init_db()

    print("🔔 Активація фонового планувальника сповіщень (за 5 хв)...")
    asyncio.create_task(notification_worker(bot))

    print("🚀 Telegram бот запущений та готовий до роботи 24/7!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("Бот зупинений.")
