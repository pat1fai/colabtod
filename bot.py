import asyncio
import json
from datetime import datetime, timedelta

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, BotCommandScopeDefault, BotCommandScopeChat
from aiogram.filters import CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram.types import Message, CallbackQuery, BotCommand
from aiogram.filters import Command
from aiohttp import web
import aiohttp_cors

from config import TOKEN, ADMIN_ID
from schedule_data import SCHEDULE as DEFAULT_SCHEDULE, DAYS_NAMES
import database as db
import keyboards as kb

bot = Bot(token=TOKEN)
# MemoryStorage нужен для FSM (машины состояний админа)
dp = Dispatcher(storage=MemoryStorage())


# Состояния для редактирования расписания
class AdminStates(StatesGroup):
    waiting_for_schedule_json = State()


# --- Хелперы форматирования ---

def format_day_schedule(day_index: int, schedule: dict) -> str:
    day_name = DAYS_NAMES.get(day_index, "Невідомий день")
    pairs = schedule.get(day_index, [])
    if not pairs:
        return f"📅 <b>{day_name}</b>\n\n🎉 Пар немає! Відпочиваємо."

    text = f"📅 <b>Розклад: {day_name}</b>\n"
    text += "────────────────────\n"
    for i, pair in enumerate(pairs, start=1):
        teacher = f"\n   👨‍🏫 <i>{pair['teacher']}</i>" if pair.get("teacher") else ""
        text += f"<b>{i}. [{pair['start']} - {pair['end']}]</b>\n   📖 {pair['name']}{teacher}\n"
    return text


async def get_schedule_api(request):
    schedule = db.get_schedule_db()
    # Возвращаем JSON с заголовком против кэширования
    return web.json_response(schedule, headers={
        "Cache-Control": "no-store, no-cache, must-revalidate",
        "Pragma": "no-cache"
    })


async def start_api():
    app = web.Application()

    # Настраиваем CORS, чтобы GitHub Pages мог делать запросы к твоему серверу
    cors = aiohttp_cors.setup(app, defaults={
        "*": aiohttp_cors.ResourceOptions(
            allow_credentials=True,
            expose_headers="*",
            allow_headers="*",
        )
    })

    resource = app.router.add_resource("/api/schedule")
    cors.add(resource.add_route("GET", get_schedule_api))

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 8080)
    await site.start()
    print("API розкладу запущено на порту 8080!")

async def setup_bot_commands(bot: Bot):
    commands = [
        BotCommand(command="start", description="🏠 Головне меню"),
        BotCommand(command="today", description="📅 Пари на сьогодні"),
        BotCommand(command="breaks", description="⏳ Розклад перерв"),
        BotCommand(command="notifications", description="🔔 Увімкнути/Вимкнути сповіщення"),
    ]
    # Отправляем список команд на сервера Telegram
    await bot.set_my_commands(commands)


def format_breaks(schedule: dict) -> str:
    text = "⏳ <b>Графік перерв за днями:</b>\n\n"
    has_breaks = False

    for day_idx in range(6):
        pairs = schedule.get(day_idx, [])
        if len(pairs) > 1:
            has_breaks = True
            text += f"📌 <b>{DAYS_NAMES[day_idx]}:</b>\n"
            for i in range(len(pairs) - 1):
                p1_end = pairs[i]["end"]
                p2_start = pairs[i + 1]["start"]
                t1 = datetime.strptime(p1_end, "%H:%M")
                t2 = datetime.strptime(p2_start, "%H:%M")
                diff = int((t2 - t1).total_seconds() / 60)
                text += f"   • Між {i+1} та {i+2} парою: <b>{diff} хв</b> ({p1_end} ➔ {p2_start})\n"
            text += "\n"

    return text if has_breaks else "Перерв не знайдено."


# --- Фоновый планировщик ---

async def check_schedule():
    now = datetime.now()
    schedule = db.get_schedule_db()
    pairs = schedule.get(now.weekday())
    if not pairs:
        return

    target_time = (now + timedelta(minutes=5)).strftime("%H:%M")

    for i, pair in enumerate(pairs):
        if pair["start"] == target_time:
            pair_num = i + 1
            teacher = f"\n👨‍🏫 <i>{pair['teacher']}</i>" if pair.get("teacher") else ""

            break_info = ""
            if i > 0:
                t1 = datetime.strptime(pairs[i - 1]["end"], "%H:%M")
                t2 = datetime.strptime(pair["start"], "%H:%M")
                diff = int((t2 - t1).total_seconds() / 60)
                break_info = f"\n⏳ Перерва тривала: <b>{diff} хв</b>"

            msg = (
                f"🔔 <b>Увага! Пара через 5 хвилин!</b>\n"
                f"────────────────────\n"
                f"📚 <b>{pair_num}. {pair['name']}</b>{teacher}\n"
                f"🕒 Час: <b>{pair['start']} - {pair['end']}</b>"
                f"{break_info}\n"
                f"────────────────────\n"
                f"<i>Готуйся до заняття!</i>"
            )

            recipients = db.get_subscribed_users()
            for uid in recipients:
                try:
                    await bot.send_message(uid, msg, parse_mode="HTML")
                except Exception:
                    pass


# --- Хэндлеры команд и меню ---

@dp.message(CommandStart())
async def cmd_start(message: Message):
    db.register_user(message.chat.id)
    status = db.get_user_status(message.chat.id)
    is_adm = message.chat.id == ADMIN_ID
    await message.answer(
        f"👋 <b>Привіт, {message.from_user.first_name}!</b>\n\n"
        f"Я твій помічник з розкладу.\n"
        f"Обирай потрібну дію на панелі нижче 👇",
        reply_markup=kb.main_menu_kb(status, is_adm),
        parse_mode="HTML"
    )

@dp.message(Command("today"))
async def cmd_today(message: Message):
    today = datetime.now().weekday()
    schedule = db.get_schedule_db()
    text = format_day_schedule(today, schedule)
    await message.answer(text, reply_markup=kb.back_to_main_kb(), parse_mode="HTML")


@dp.message(Command("breaks"))
async def cmd_breaks(message: Message):
    schedule = db.get_schedule_db()
    text = format_breaks(schedule)
    await message.answer(text, reply_markup=kb.back_to_main_kb(), parse_mode="HTML")


@dp.message(Command("notifications"))
async def cmd_toggle_notif(message: Message):
    new_status = db.toggle_notifications(message.chat.id)
    status_text = "увімкнено 🔔" if new_status else "вимкнено 🔕"
    await message.answer(f"Сповіщення {status_text}!")


@dp.callback_query(F.data == "back_main")
async def cb_back_main(call: CallbackQuery):
    status = db.get_user_status(call.message.chat.id)
    is_adm = call.message.chat.id == ADMIN_ID
    await call.message.edit_text(
        "Головне меню розкладу:",
        reply_markup=kb.main_menu_kb(status, is_adm)
    )
    await call.answer()


@dp.callback_query(F.data == "toggle_notif")
async def cb_toggle_notif(call: CallbackQuery):
    new_status = db.toggle_notifications(call.message.chat.id)
    is_adm = call.message.chat.id == ADMIN_ID
    await call.message.edit_reply_markup(
        reply_markup=kb.main_menu_kb(new_status, is_adm)
    )
    status_text = "увімкнено 🔔" if new_status else "вимкнено 🔕"
    await call.answer(f"Сповіщення {status_text}")


@dp.callback_query(F.data == "day_today")
async def cb_day_today(call: CallbackQuery):
    today = datetime.now().weekday()
    schedule = db.get_schedule_db()
    text = format_day_schedule(today, schedule)
    await call.message.edit_text(text, reply_markup=kb.back_to_main_kb(), parse_mode="HTML")
    await call.answer()


@dp.callback_query(F.data == "menu_select_day")
async def cb_select_day_menu(call: CallbackQuery):
    await call.message.edit_text("Оберіть день тижня:", reply_markup=kb.days_kb())
    await call.answer()


@dp.callback_query(F.data.startswith("day_"))
async def cb_show_day(call: CallbackQuery):
    day_idx = int(call.data.split("_")[1])
    schedule = db.get_schedule_db()
    text = format_day_schedule(day_idx, schedule)
    await call.message.edit_text(text, reply_markup=kb.days_kb(), parse_mode="HTML")
    await call.answer()


@dp.callback_query(F.data == "menu_breaks")
async def cb_menu_breaks(call: CallbackQuery):
    schedule = db.get_schedule_db()
    text = format_breaks(schedule)
    await call.message.edit_text(text, reply_markup=kb.back_to_main_kb(), parse_mode="HTML")
    await call.answer()

@dp.message(Command("admin"))
@dp.message(F.text.lower().in_(["админ", "admin"]))
async def cmd_admin(message: Message):
    # Проверяем права: если пишет не админ — вежливо отказываем
    if message.chat.id != ADMIN_ID:
        await message.answer("⛔ <b>Доступ заборонено!</b> Ви не є адміністратором.", parse_mode="HTML")
        return

    # Если админ — открываем меню
    await message.answer(
        "⚙️ <b>Панель адміністратора</b>\n\nОберіть потрібну дію:",
        reply_markup=kb.admin_menu_kb(),
        parse_mode="HTML"
    )

# --- Админ-панель: обновление расписания без остановки бота ---

@dp.callback_query(F.data == "admin_panel")
async def cb_admin_panel(call: CallbackQuery, state: FSMContext):
    if call.message.chat.id != ADMIN_ID:
        await call.answer("Доступ заборонено!", show_alert=True)
        return

    await state.set_state(AdminStates.waiting_for_schedule_json)
    current_json = json.dumps(db.get_schedule_db(), ensure_ascii=False, indent=2)

    await call.message.answer(
        "🛠 <b>Режим редагування розкладу</b>\n\n"
        "Надішли у відповідь новий розклад у форматі JSON. "
        "Ось поточна версія для зразка:",
        parse_mode="HTML"
    )
    # Отправляем текущий конфиг, чтобы админ мог его скопировать и отредактировать
    await call.message.answer(f"<code>{current_json}</code>", parse_mode="HTML")
    await call.answer()


@dp.message(StateFilter(AdminStates.waiting_for_schedule_json))
async def process_new_schedule(message: Message, state: FSMContext):
    if message.chat.id != ADMIN_ID:
        return

    try:
        new_data = json.loads(message.text)
        # Валидация: ключи должны превращаться в целые числа
        parsed_data = {int(k): v for k, v in new_data.items()}
        db.update_schedule_db(parsed_data)

        await state.clear()
        await message.answer("✅ <b>Розклад успішно оновлено!</b> Зміни вже застосовані на льоту.", parse_mode="HTML")
    except Exception as e:
        await message.answer(
            f"❌ <b>Помилка у форматі JSON:</b>\n<code>{e}</code>\n\n"
            "Перевір синтаксис (коми, лапки) та надішли ще раз або зупини команду командою /start.",
            parse_mode="HTML"
        )


# --- Старт программы ---

# --- Старт программы ---

async def setup_bot_commands(bot: Bot):
    user_commands = [
        BotCommand(command="start", description="🏠 Головне меню"),
        BotCommand(command="today", description="📅 Пари на сьогодні"),
        BotCommand(command="breaks", description="⏳ Розклад перерв"),
        BotCommand(command="notifications", description="🔔 Увімкнути/Вимкнути сповіщення"),
    ]
    await bot.set_my_commands(user_commands, scope=BotCommandScopeDefault())

    # Безопасная установка для админа
    if ADMIN_ID and ADMIN_ID != 0:
        try:
            admin_commands = user_commands + [
                BotCommand(command="admin", description="⚙️ Адмін-панель керування")
            ]
            await bot.set_my_commands(admin_commands, scope=BotCommandScopeChat(chat_id=ADMIN_ID))
        except Exception as e:
            print(f"Попередження: не вдалося зареєструвати команди адміна: {e}")


async def main():
    # 1. Инициализация базы данных
    db.init_db(DEFAULT_SCHEDULE)
    await setup_bot_commands(bot)
    # 2. Установка команд меню в Telegram
    await setup_bot_commands(bot)

    # 3. Запуск фонового планировщика
    scheduler = AsyncIOScheduler()
    scheduler.add_job(check_schedule, trigger="interval", minutes=1)
    scheduler.start()
    print("Планувальник сповіщень запущено!")

    # 4. Очистка старых сообщений и вечный цикл работы
    await bot.delete_webhook(drop_pending_updates=True)
    print("Бот успішно працює і слухає повідомлення...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())