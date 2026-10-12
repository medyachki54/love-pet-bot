import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.filters import Command
from fastapi import FastAPI
import uvicorn
import threading

# Вставьте сюда ваш токен от BotFather
API_TOKEN = '8777182579:AAHWevczdBTlDOBwEYJQWAsDU1v4hM1GxVg'

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Данные о питомце
pet_data = {
    "name": "Пушок",
    "exp": 0
}

def get_pet_stage(exp: int) -> str:
    if exp < 15:
        return "🥚 Маленькое яйцо"
    elif exp < 50:
        return "🐣 Вылупившийся птенец"
    elif exp < 150:
        return "🦊 Милый лисёнок"
    else:
        return "🦁 Взрослый дракон любви!"

# Отслеживание сообщений из лички с девушкой (Telegram Business)
@dp.business_message()
async def track_business_messages(message: types.Message):
    old_stage = get_pet_stage(pet_data["exp"])
    pet_data["exp"] += 1
    new_stage = get_pet_stage(pet_data["exp"])

    if old_stage != new_stage:
        await message.reply(
            f"🎉 <b>Наш питомец {pet_data['name']} подрос!</b>\n\n"
            f"Новый статус: {new_stage}\n"
            f"Всего сообщений: {pet_data['exp']} 💌",
            parse_mode=ParseMode.HTML
        )

# Команда /pet для проверки статуса в личке у бота
@dp.message(Command("pet"))
async def check_pet_status(message: types.Message):
    stage = get_pet_stage(pet_data["exp"])
    await message.answer(
        f"🐾 <b>Информация о питомце {pet_data['name']}:</b>\n"
        f"✨ Опыт: {pet_data['exp']} XP\n"
        f"🌱 Стадия: {stage}",
        parse_mode=ParseMode.HTML
    )

# Фоновый запуск Telegram-бота
async def run_bot():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

def start_telegram_bot():
    asyncio.run(run_bot())

# Веб-сервер для хостинга
app = FastAPI()

@app.get("/")
def home():
    return {"status": "Bot is running 24/7!"}

if __name__ == "__main__":
    bot_thread = threading.Thread(target=start_telegram_bot)
    bot_thread.start()
    uvicorn.run(app, host="0.0.0.0", port=7860)
