import asyncio
from aiogram import Bot
from aiogram.exceptions import TelegramForbiddenError
from schedule_service import get_now, time_to_minutes, get_current_week_type
from schedule_data import WEEKLY_SCHEDULE
from database import get_subscribers

sent_today = set()

async def notification_worker(bot: Bot):
    """
    Фоновий процес: кожні 25 секунд перевіряє розклад і
    надсилає сповіщення рівно за 5 хвилин до початку кожної пари.
    """
    last_day = None
    while True:
        try:
            now = get_now()
            today_str = now.strftime("%Y-%m-%d")

            # Очищення відправлених сповіщень опівночі
            if last_day != today_str:
                sent_today.clear()
                last_day = today_str

            day_idx = now.weekday()
            current_week = get_current_week_type(now)
            current_minutes = now.hour * 60 + now.minute

            pairs = WEEKLY_SCHEDULE.get(day_idx, [])
            for p in pairs:
                if p.get("week") is not None and p.get("week") != current_week:
                    continue

                start_min = time_to_minutes(p["start"])
                diff = start_min - current_minutes
                notify_key = f"{today_str}_{p['pair']}_{p['start']}"

                # Якщо до пари залишилось 5 хвилин і ми ще не сповіщали
                if diff == 5 and notify_key not in sent_today:
                    sent_today.add(notify_key)
                    subscribers = await get_subscribers()

                    text = (
                        f"🔔 <b>Увага! Через 5 хвилин починається пара:</b>\n\n"
                        f"📚 <b>{p['name']}</b> ({p.get('type', 'Заняття')})\n"
                        f"⏰ {p['start']} – {p['end']}\n"
                        f"🚪 {p.get('room', 'Аудиторія не вказана')}\n"
                        f"👨‍🏫 {p.get('teacher', 'Викладач не вказаний')}\n\n"
                        f"<i>Приготуйтеся до заняття! 📖</i>"
                    )

                    for uid in subscribers:
                        try:
                            await bot.send_message(uid, text, parse_mode="HTML")
                            await asyncio.sleep(0.04)
                        except TelegramForbiddenError:
                            pass
                        except Exception as e:
                            print(f"Помилка надсилання сповіщення {uid}: {e}")

        except Exception as e:
            print(f"Помилка у циклі сповіщень: {e}")

        await asyncio.sleep(25)
