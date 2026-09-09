from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo


WEBAPP_URL = "https://pat1fai.github.io/colabtod/"  # Твоя ссылка


def main_menu_kb(notif_active: bool, is_admin: bool = False) -> InlineKeyboardMarkup:
    notif_text = "🔔 Сповіщення: [УВІМК]" if notif_active else "🔕 Сповіщення: [ВИМК]"

    keyboard = [
        # Кнопка открытия Apple WebApp
        [
            InlineKeyboardButton(
                text="📱 Відкрити графік (iOS View)",
                web_app=WebAppInfo(url=WEBAPP_URL)
            )
        ],
        [
            InlineKeyboardButton(text="📅 Сьогодні", callback_data="day_today"),
            InlineKeyboardButton(text="📆 Обрати день", callback_data="menu_select_day")
        ],
        [
            InlineKeyboardButton(text="⏳ Графік перерв", callback_data="menu_breaks"),
            InlineKeyboardButton(text=notif_text, callback_data="toggle_notif")
        ]
    ]

    if is_admin:
        keyboard.append([InlineKeyboardButton(text="⚙️ Адмін-панель", callback_data="admin_panel")])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def main_menu_kb(notif_active: bool, is_admin: bool = False) -> InlineKeyboardMarkup:
    notif_text = "🔔 Сповіщення: [УВІМК]" if notif_active else "🔕 Сповіщення: [ВИМК]"

    keyboard = [
        [
            InlineKeyboardButton(text="📅 Сьогодні", callback_data="day_today"),
            InlineKeyboardButton(text="📆 Обрати день", callback_data="menu_select_day")
        ],
        [
            InlineKeyboardButton(text="⏳ Графік перерв", callback_data="menu_breaks"),
            InlineKeyboardButton(text=notif_text, callback_data="toggle_notif")
        ]
    ]
    if is_admin:
        keyboard.append([InlineKeyboardButton(text="⚙️ Адмін-панель", callback_data="admin_panel")])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def admin_menu_kb() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton(text="✏️ Редагувати розклад (JSON)", callback_data="admin_panel")],
        [InlineKeyboardButton(text="⬅️ Головне меню", callback_data="back_main")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def days_kb() -> InlineKeyboardMarkup:
    days = [
        ("Пн", "day_0"), ("Вт", "day_1"), ("Ср", "day_2"),
        ("Чт", "day_3"), ("Пт", "day_4"), ("Сб", "day_5")
    ]
    buttons = [InlineKeyboardButton(text=name, callback_data=code) for name, code in days]
    # Разбиваем кнопки по 3 в ряд
    rows = [buttons[:3], buttons[3:6]]
    rows.append([InlineKeyboardButton(text="⬅️ Назад до меню", callback_data="back_main")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def back_to_main_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="⬅️ Головне меню", callback_data="back_main")]]
    )