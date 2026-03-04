import aiosqlite

DB_NAME = 'tracker.db'

# создаем таблицу пользователей, если её еще нет
async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                weight REAL,
                height REAL,
                age INTEGER,
                gender TEXT,
                activity INTEGER,
                city TEXT,
                water_goal REAL,
                calorie_goal REAL,
                logged_water REAL DEFAULT 0,
                logged_calories REAL DEFAULT 0,
                burned_calories REAL DEFAULT 0
            )
        ''')
        await db.commit()

# получаем данные пользователя по id
async def get_user(user_id):
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)) as cursor:
            return await cursor.fetchone()

# обновляем данные пользователя
async def update_user(user_id, **kwargs):
    async with aiosqlite.connect(DB_NAME) as db:
        columns = ', '.join([f"{k} = ?" for k in kwargs.keys()])
        values = list(kwargs.values())
        values.append(user_id)

        await db.execute(f"INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
        await db.execute(f"UPDATE users SET {columns} WHERE user_id = ?", values)
        await db.commit()

# добавляем выпитую воду
async def log_water(user_id, amount):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("UPDATE users SET logged_water = logged_water + ? WHERE user_id = ?", (amount, user_id))
        await db.commit()

# добавляем калории
async def log_calories(user_id, amount):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("UPDATE users SET logged_calories = logged_calories + ? WHERE user_id = ?", (amount, user_id))
        await db.commit()

# записываем результаты тренировки
async def log_workout_db(user_id, burned_kcal, added_water):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('''
            UPDATE users 
            SET burned_calories = burned_calories + ?,
                water_goal = water_goal + ?
            WHERE user_id = ?
        ''', (burned_kcal, added_water, user_id))
        await db.commit()