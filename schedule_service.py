from datetime import datetime, timedelta
from config import TIMEZONE
from schedule_data import BELLS, WEEKLY_SCHEDULE, DAYS_NAMES

def get_now():
    """Поточний час у часовому поясі навчального закладу."""
    return datetime.now(TIMEZONE)

def get_current_week_type(dt=None) -> int:
    """
    Визначає чисельник (1) або знаменник (2).
    За стандартним календарем непарний тиждень - 1 (чисельник), парний - 2 (знаменник).
    """
    if dt is None:
        dt = get_now()
    week_num = dt.isocalendar()[1]
    return 1 if (week_num % 2 != 0) else 2

def time_to_minutes(t_str: str) -> int:
    h, m = map(int, t_str.split(":"))
    return h * 60 + m

def get_pair_bells(pair_num: int):
    for b in BELLS:
        if b["pair"] == pair_num:
            return b
    return None

def get_day_schedule(day_offset: int = 0, force_week: int = None):
    """
    Повертає розклад на день з урахуванням зсуву та тижня.
    day_offset: 0 - сьогодні, 1 - завтра тощо.
    """
    now = get_now() + timedelta(days=day_offset)
    day_idx = now.weekday()
    target_week = force_week if force_week is not None else get_current_week_type(now)

    all_pairs = WEEKLY_SCHEDULE.get(day_idx, [])
    filtered_pairs = []

    for item in all_pairs:
        if item["week"] is None or item["week"] == target_week:
            bells = get_pair_bells(item["pair"])
            filtered_pairs.append({
                **item,
                "start": bells["start"] if bells else "??:??",
                "end": bells["end"] if bells else "??:??"
            })

    filtered_pairs.sort(key=lambda x: x["pair"])
    week_label = "Чисельник (1 тиждень)" if target_week == 1 else "Знаменник (2 тиждень)"

    return {
        "day_idx": day_idx,
        "day_name": DAYS_NAMES[day_idx],
        "date": now.strftime("%d.%m.%Y"),
        "week_type": target_week,
        "week_label": week_label,
        "pairs": filtered_pairs
    }

def get_current_and_next_pair():
    """
    Визначає поточну пару (з прогресом у % та хвилинами до кінця)
    та наступну пару (з кількістю хвилин до початку).
    """
    now = get_now()
    day_idx = now.weekday()
    current_week = get_current_week_type(now)
    current_minutes = now.hour * 60 + now.minute

    pairs = WEEKLY_SCHEDULE.get(day_idx, [])
    current_pair = None
    next_pair = None

    for item in pairs:
        if item["week"] is not None and item["week"] != current_week:
            continue

        bells = get_pair_bells(item["pair"])
        if not bells:
            continue

        start_min = time_to_minutes(bells["start"])
        end_min = time_to_minutes(bells["end"])

        pair_data = {
            **item,
            "start": bells["start"],
            "end": bells["end"]
        }

        # Якщо пара зараз іде
        if start_min <= current_minutes <= end_min:
            duration = max(1, end_min - start_min)
            progress = int(((current_minutes - start_min) / duration) * 100)
            pair_data["progress"] = min(100, max(0, progress))
            pair_data["minutes_left"] = max(0, end_min - current_minutes)
            current_pair = pair_data
        # Якщо пара ще попереду сьогодні
        elif start_min > current_minutes:
            if next_pair is None or start_min < time_to_minutes(next_pair["start"]):
                pair_data["minutes_until"] = start_min - current_minutes
                next_pair = pair_data

    return current_pair, next_pair
