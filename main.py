import logging
import asyncio
import os
import sqlite3
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils import executor
from aiogram.utils.deep_linking import get_start_link
from aiogram.dispatcher.filters import CommandStart

API_TOKEN = '7535405556:AAGMqFynf25DF8RV-Zy6G4RssZOzrISLB50'
ADMIN_ID = 7702280273

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# База
conn = sqlite3.connect('bot_db.db')
cursor = conn.cursor()

cursor.execute('''CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    bonus INTEGER DEFAULT 10,
    inviter_id INTEGER
)''')

cursor.execute('''CREATE TABLE IF NOT EXISTS videos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_id TEXT
)''')

conn.commit()

# 🔘 Кнопкалар
main_kb = ReplyKeyboardMarkup(resize_keyboard=True)
main_kb.add(KeyboardButton("Детский"), KeyboardButton("Бонус"), KeyboardButton("VIP"))

admin_kb = ReplyKeyboardMarkup(resize_keyboard=True)
admin_kb.add(KeyboardButton("Видео салу"), KeyboardButton("Қолданушы саны"), KeyboardButton("Рассылка"))

# 👤 Старт
@dp.message_handler(CommandStart(deep_link=True))
async def start_ref(message: types.Message):
    inviter_id = int(message.get_args())
    user_id = message.from_user.id

    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    if not cursor.fetchone():
        cursor.execute("INSERT INTO users (user_id, bonus, inviter_id) VALUES (?, ?, ?)", (user_id, 10, inviter_id))
        cursor.execute("UPDATE users SET bonus = bonus + 2 WHERE user_id = ?", (inviter_id,))
        conn.commit()

    kb = admin_kb if user_id == ADMIN_ID else main_kb
    await message.answer("Ботқа қош келдіңіз!", reply_markup=kb)

@dp.message_handler(CommandStart())
async def start(message: types.Message):
    user_id = message.from_user.id
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    if not cursor.fetchone():
        cursor.execute("INSERT INTO users (user_id, bonus) VALUES (?, ?)", (user_id, 10))
        conn.commit()

    kb = admin_kb if user_id == ADMIN_ID else main_kb
    await message.answer("Ботқа қош келдіңіз!", reply_markup=kb)

# 🎥 Видео салу (Админ)
@dp.message_handler(lambda msg: msg.text == "Видео салу" and msg.from_user.id == ADMIN_ID)
async def prompt_video(message: types.Message):
    await message.answer("Видеоларды жібере беріңіз (бірнешеуін қатар).")

@dp.message_handler(content_types=types.ContentType.VIDEO)
async def save_video(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        video_id = message.video.file_id
        cursor.execute("INSERT INTO videos (file_id) VALUES (?)", (video_id,))
        conn.commit()
        await message.reply("✅ Видео сақталды.")
    else:
        await message.reply("Тек админ ғана видео сала алады.")

# 👶 Детский батырмасы
@dp.message_handler(lambda msg: msg.text == "Детский")
async def show_video(message: types.Message):
    user_id = message.from_user.id
    cursor.execute("SELECT bonus FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()

    if row and row[0] >= 3:
        cursor.execute("SELECT file_id FROM videos ORDER BY RANDOM() LIMIT 1")
        video = cursor.fetchone()
        if video:
            await bot.send_video(chat_id=message.chat.id, video=video[0])
            cursor.execute("UPDATE users SET bonus = bonus - 3 WHERE user_id = ?", (user_id,))
            conn.commit()
        else:
            await message.answer("Қазір видео жоқ.")
    else:
        await message.answer("❌ 3 бонус керек!")

# 🎁 Бонус батырмасы
@dp.message_handler(lambda msg: msg.text == "Бонус")
async def bonus(message: types.Message):
    user_id = message.from_user.id
    link = await get_start_link(payload=str(user_id), encode=True)
    cursor.execute("SELECT bonus FROM users WHERE user_id = ?", (user_id,))
    bonus = cursor.fetchone()[0]
    await message.answer(f"🎁 Сіздің бонусыңыз: {bonus}\n📢 Достарыңызды шақырыңыз: {link}")

# 👑 VIP батырмасы
@dp.message_handler(lambda msg: msg.text == "VIP")
async def vip(message: types.Message):
    await message.answer("👑 VIP Бонустар сатып алу:\n\n50 бонус = 2000тг\n100 бонус = 4000тг\n\nСатып алу үшін: @KazHubALU")

# 👥 Қолданушы саны
@dp.message_handler(lambda msg: msg.text == "Қолданушы саны" and msg.from_user.id == ADMIN_ID)
async def count_users(message: types.Message):
    cursor.execute("SELECT COUNT(*) FROM users")
    count = cursor.fetchone()[0]
    await message.answer(f"👥 Қолданушылар саны: {count}")

# 📣 Рассылка
@dp.message_handler(lambda msg: msg.text == "Рассылка" and msg.from_user.id == ADMIN_ID)
async def start_broadcast(message: types.Message):
    await message.answer("✉️ Хабарламаңызды жіберіңіз (барлық қолданушыларға таратылады).")

@dp.message_handler(lambda msg: msg.from_user.id == ADMIN_ID, content_types=types.ContentType.TEXT)
async def broadcast_text(message: types.Message):
    cursor.execute("SELECT user_id FROM users")
    users = cursor.fetchall()
    for user in users:
        try:
            await bot.send_message(user[0], message.text)
        except:
            pass
    await message.answer("✅ Барлығына жіберілді.")

# 📂 Папка жасау
if not os.path.exists("saved_videos"):
    os.makedirs("saved_videos")

# 🔄 Старт
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    executor.start_polling(dp, skip_updates=True)
