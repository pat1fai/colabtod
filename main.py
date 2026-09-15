import asyncio
import os
import sys

# Забезпечення коректного виведення UTF-8 (емодзі та кирилиця) на Windows
if sys.platform == "win32":
    import io
    if hasattr(sys.stdout, 'buffer'):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    if hasattr(sys.stderr, 'buffer'):
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from aiohttp import web
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    WebAppInfo, MenuButtonWebApp
)

from config import BOT_TOKEN, WEBAPP_URL, PORT
from database import init_db, add_user, toggle_notifications
from schedule_service import get_day_schedule, get_current_and_next_pair
from notifier import notification_worker

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

def get_main_keyboard():
    # Telegram вимагає обов'язково HTTPS для WebAppInfo
    is_https = WEBAPP_URL.startswith("https://")
    
    if is_https:
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

    # Встановлення кнопки меню в лівому нижньому кутку Telegram (тільки якщо налаштовано HTTPS)
    if WEBAPP_URL.startswith("https://"):
        try:
            await bot.set_chat_menu_button(
                chat_id=message.chat.id,
                menu_button=MenuButtonWebApp(text="Розклад", web_app=WebAppInfo(url=WEBAPP_URL))
            )
        except Exception as e:
            print(f"Помилка встановлення кнопки меню: {e}")

    await message.answer(
        f"Привіт, <b>{message.from_user.first_name}</b>! 👋\n\n"
        "Я твій помічник з розкладу пар для групи <b>КМ 24-9-1</b> (ВСП ФК КрНУ).\n\n"
        "✨ <b>Основні можливості:</b>\n"
        "• 🔔 <b>Оповіщення за 5 хвилин</b> до початку кожної пари для всіх підписників\n"
        "• 🕒 Перегляд поточної пари, що йде зараз (з прогресом у %)\n"
        "• ⏭ Перегляд наступної пари та часу перерви\n"
        "• 📅 Розклад на сьогодні та завтра\n"
        "• 📱 Повноцінний <b>додаток у стилі Apple</b> прямо в Telegram (кнопка внизу або в меню)!\n\n"
        "Оберіть дію на клавіатурі нижче:",
        reply_markup=get_main_keyboard(),
        parse_mode="HTML"
    )

@dp.message(F.text == "🕒 Поточна пара")
async def show_current(message: types.Message):
    curr, _ = get_current_and_next_pair()
    if not curr:
        await message.answer("🌴 <b>Зараз пари немає!</b> Можна спокійно відпочивати або готуватися до наступних занять.", parse_mode="HTML")
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
        await message.answer("✨ <b>На сьогодні всі пари закінчилися!</b> Чудового вечора.", parse_mode="HTML")
        return

    await message.answer(
        f"⏳ <b>Наступна {nxt['pair']}-а пара:</b>\n\n"
        f"📚 <b>{nxt['name']}</b> ({nxt.get('type', 'Заняття')})\n"
        f"⏰ Початок о <b>{nxt['start']}</b> (до {nxt['end']})\n"
        f"🚪 {nxt.get('room', 'Аудиторія не вказана')}\n"
        f"👨‍🏫 {nxt.get('teacher', 'Викладач не вказаний')}\n\n"
        f"⏳ До початку пари залишилося: <b>{nxt['minutes_until']} хв</b>",
        parse_mode="HTML"
    )

@dp.message(F.text == "📅 Сьогодні")
async def show_today(message: types.Message):
    data = get_day_schedule(0)
    if not data["pairs"]:
        await message.answer(f"🎉 <b>{data['day_name']} ({data['date']})</b>: пар немає, вихідний!", parse_mode="HTML")
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
        await message.answer(f"🎉 <b>Завтра ({data['day_name']}, {data['date']})</b>: пар немає, відпочивайте!", parse_mode="HTML")
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
        "📱 <b>Telegram Web App</b>\n\n"
        "Для відкриття додатку всередині Telegram потрібне безпечне посилання <code>https://</code>.\n\n"
        "• Зараз на комп'ютері ви можете відкрити розклад у браузері:\n"
        "👉 <a href=\"http://localhost:8080\">http://localhost:8080</a>\n\n"
        "• Щоб відкривати його з мобільного телефону в Telegram, запустіть у терміналі тунель:\n"
        "<code>npx localtunnel --port 8080</code>\n"
        "і вкажіть отримане HTTPS-посилання у файлі <code>config.py</code>!",
        parse_mode="HTML",
        disable_web_page_preview=True
    )

@dp.message(F.text == "🔔 Налаштування сповіщень")
async def toggle_notify(message: types.Message):
    status = await toggle_notifications(message.from_user.id)
    if status:
        await message.answer("🔔 <b>Сповіщення увімкнено!</b>\nВи будете отримувати нагадування за 5 хвилин до початку кожної пари.", parse_mode="HTML")
    else:
        await message.answer("🔕 <b>Сповіщення вимкнено.</b>\nВи більше не будете отримувати нагадування перед парами.", parse_mode="HTML")

# API для Telegram Mini App
async def api_schedule(request):
    sched_type = request.query.get("type", "today")

    if sched_type == "tomorrow":
        data = get_day_schedule(1)
    elif sched_type == "week1":
        data = get_day_schedule(0, force_week=1)
    elif sched_type == "week2":
        data = get_day_schedule(0, force_week=2)
    else:
        data = get_day_schedule(0)

    # Додаємо мітку поточної пари для сьогодні
    curr, _ = get_current_and_next_pair()
    if curr and sched_type == "today":
        for p in data["pairs"]:
            if p["pair"] == curr["pair"]:
                p["is_current"] = True
                p["progress"] = curr["progress"]
                p["minutes_left"] = curr["minutes_left"]

    return web.json_response(data)

async def main():
    print("⏳ Ініціалізація бази даних...")
    await init_db()

    # 1. Запуск Web App сервера
    print("🌐 Запуск Mini App веб-сервера...")
    app = web.Application()
    app.router.add_get('/api/schedule', api_schedule)

    webapp_dir = os.path.join(os.path.dirname(__file__), 'webapp')
    app.router.add_static('/', path=webapp_dir, show_index=True)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', PORT)
    await site.start()
    print(f"✅ Web App працює на http://localhost:{PORT}")

    # 2. Фоновий воркер сповіщень за 5 хвилин
    asyncio.create_task(notification_worker(bot))
    print("✅ Фоновий планувальник сповіщень (за 5 хв) активовано!")

    # 3. Запуск опитування Telegram
    print("🚀 Telegram бот запущений та готовий до роботи!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("Бот зупинений.")
