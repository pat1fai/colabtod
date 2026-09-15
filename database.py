import aiosqlite

DB_PATH = "bot_users.db"

async def init_db():
    """Ініціалізація таблиці користувачів та їх налаштувань."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                notifications_enabled INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.commit()

async def add_user(user_id: int, username: str, first_name: str):
    """Додавання нового або оновлення існуючого користувача."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO users (user_id, username, first_name)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                username = excluded.username,
                first_name = excluded.first_name
        """, (user_id, username or "", first_name or ""))
        await db.commit()

async def toggle_notifications(user_id: int) -> bool:
    """Перемикання статусу сповіщень (увімкнено / вимкнено)."""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT notifications_enabled FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            current_state = row[0] if row else 1
            new_state = 0 if current_state == 1 else 1

        await db.execute("UPDATE users SET notifications_enabled = ? WHERE user_id = ?", (new_state, user_id))
        await db.commit()
        return bool(new_state)

async def get_subscribers():
    """Отримання всіх ID користувачів, у яких увімкнені сповіщення."""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT user_id FROM users WHERE notifications_enabled = 1") as cursor:
            rows = await cursor.fetchall()
            return [row[0] for row in rows]
