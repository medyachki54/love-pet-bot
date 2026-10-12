import asyncio
import json
import os
import logging
from aiogram import Bot, Dispatcher
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command

# Токен берётся из переменных окружения (безопасно)
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не установлен! Добавь его в Environment Variables на хостинге.")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

DATA_FILE = "pet_data.json"

# Начальные данные по умолчанию
default_data = {
    "is_active": False,
    "users": [],  # Список участников
    "total_messages": 0,
    "current_exp": 0,
    "max_exp": 250,
    "level": 1,
    "pet_name": None
}

# Создаем постоянные кнопки под чатом
main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="/pet"), KeyboardButton(text="/profile")],
        [KeyboardButton(text="/start_pet")]
    ],
    resize_keyboard=True
)

def load_data():
    """Загрузка прогресса из файла"""
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                for key, val in default_data.items():
                    if key not in data:
                        data[key] = val
                return data
        except Exception:
            pass
    return default_data.copy()

def save_data(data):
    """Сохранение прогресса в файл"""
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        logging.error(f"Ошибка сохранения данных: {e}")

pet_game = load_data()

def add_exp(amount=1):
    """Добавление опыта и проверка уровней"""
    pet_game["total_messages"] += amount
    pet_game["current_exp"] += amount
    
    leveled_up = False
    while pet_game["current_exp"] >= pet_game["max_exp"]:
        pet_game["current_exp"] -= pet_game["max_exp"]
        pet_game["level"] += 1
        pet_game["max_exp"] *= 2
        leveled_up = True
        
    save_data(pet_game)
    return leveled_up

# 1. Приветствие по команде /start
@dp.message(Command("start"))
@dp.business_message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "Приветствую тебя — я твой виртуальный питомец. 🐾\n"
        "Введи команду /start_pet один раз, чтобы начать растить питомца "
        "вместе со своим любимым человеком 🥰",
        reply_markup=main_keyboard
    )

# 2. Совместный запуск по команде /start_pet
@dp.message(Command("start_pet"))
@dp.business_message(Command("start_pet"))
async def accept_pet(message: Message):
    user = message.from_user
    user_id = user.id
    username = f"@{user.username}" if user.username else user.first_name

    if pet_game["is_active"]:
        await message.answer("🐾 Питомец уже запущен и активно растет!", reply_markup=main_keyboard)
        return

    existing_user_ids = [u["id"] for u in pet_game["users"]]
    
    if user_id not in existing_user_ids:
        pet_game["users"].append({"id": user_id, "name": username})
        save_data(pet_game)

    count = len(pet_game["users"])

    if count == 1:
        await message.answer(
            f"⏳ Первый участник ({username}) подтвердил готовность! ✨\n"
            "Теперь второй человек должен отправить команду `/start_pet`.",
            reply_markup=main_keyboard
        )
    elif count >= 2:
        pet_game["is_active"] = True
        save_data(pet_game)
        await message.answer(
            f"🎉 Второй участник ({username}) ввел команду!\n\n"
            "Поздравляю вас, у вас появилось яйцо питомца 🥚☺️☺️☺️, "
            "общайтесь, прокачивайтесь и растите вместе ❤️",
            reply_markup=main_keyboard
        )

# 3. Команда для выбора имени питомца (доступна с 5 уровня)
@dp.message(Command("name"))
@dp.business_message(Command("name"))
async def set_pet_name(message: Message):
    if not pet_game["is_active"]:
        await message.answer("💤 Питомец ещё не родился!", reply_markup=main_keyboard)
        return
        
    if pet_game["level"] < 5:
        await message.answer(f"🐣 Питомец еще маленький! Он вылупится на 5 уровне (сейчас уровень {pet_game['level']}).", reply_markup=main_keyboard)
        return

    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("⚠️ Пожалуйста, укажите имя после команды. Например: `/name Персик`", reply_markup=main_keyboard)
        return

    pet_name = args[1].strip()
    pet_game["pet_name"] = pet_name
    save_data(pet_game)

    await message.answer(f"🎉 Ура! Вы назвали своего питомца: **{pet_name}** 🍼💖 Теперь он растет под этим именем!", reply_markup=main_keyboard)

# 4. Автоматический подсчет сообщений из Telegram Business
@dp.business_message()
async def track_business_messages(message: Message):
    if not pet_game["is_active"]:
        return

    leveled_up = add_exp(1)
    
    if leveled_up:
        if pet_game["level"] == 5 and not pet_game["pet_name"]:
            await message.answer(
                f"🎉 **Поздравляем! Питомец достиг Уровня 5 и вылупился из яйца!** 🐣✨\n\n"
                f"Теперь вы можете дать ему имя! Введите команду в формате: `/name Имя_питомца`",
                reply_markup=main_keyboard
            )
        else:
            await message.answer(
                f"🎉 **Поздравляем! Питомец перешел на Уровень {pet_game['level']}!** 🌟\n\n"
                f"🐾 **Статус вашего питомца:**\n"
                f"💬 Общее количество сообщений: {pet_game['total_messages']}\n"
                f"✨ Exp: {pet_game['current_exp']}/{pet_game['max_exp']}\n"
                f"🌟 Уровень: {pet_game['level']}",
                reply_markup=main_keyboard
            )

# 5. Проверка статуса питомца (/pet)
@dp.message(Command("pet"))
@dp.business_message(Command("pet"))
async def show_pet_status(message: Message):
    if not pet_game["is_active"]:
        users_ready = len(pet_game["users"])
        await message.answer(
            f"💤 **Питомец ещё не родился!**\n\n"
            f"👥 Готово участников: {users_ready}/2\n"
            f"Отправьте `/start_pet`, чтобы подтвердить готовность.",
            reply_markup=main_keyboard
        )
        return

    if pet_game["pet_name"]:
        pet_display = f"🏷 Имя: {pet_game['pet_name']}"
    elif pet_game["level"] >= 5:
        pet_display = "🐣 Вылупился! (Введите /name <имя>)"
    else:
        pet_display = "🥚 Стадия: Яйцо (вылупится на 5 уровне)"

    await message.answer(
        f"🐾 **Статус вашего питомца:**\n"
        f"💬 Общее количество сообщений: {pet_game['total_messages']}\n"
        f"✨ Exp: {pet_game['current_exp']}/{pet_game['max_exp']}\n"
        f"🌟 Уровень: {pet_game['level']}\n"
        f"{pet_display}",
        reply_markup=main_keyboard
    )

# 6. Команда профиля (/profile)
@dp.message(Command("profile"))
@dp.business_message(Command("profile"))
async def show_profile(message: Message):
    user = message.from_user
    user_id = user.id
    username = f"@{user.username}" if user.username else user.first_name

    partner = "Ещё не подключился ⏳"
    if len(pet_game["users"]) >= 2:
        for u in pet_game["users"]:
            if u["id"] != user_id:
                partner = f"{u['name']} (ID: `{u['id']}`)"
                break
    elif len(pet_game["users"]) == 1 and pet_game["users"][0]["id"] == user_id:
        partner = "Ожидание второго участника... ⏳"

    pet_info = pet_game["pet_name"] if pet_game["pet_name"] else ("🥚 Яйцо" if pet_game["level"] < 5 else "🐣 Готов к имени (/name)")

    await message.answer(
        f"👤 **Ваш профиль:**\n"
        f"🆔 ID: `{user_id}`\n"
        f"🏷 Имя / Юз: {username}\n\n"
        f"❤️ **Партнер по питомцу:**\n"
        f"{partner}\n\n"
        f"🐾 **Питомец:** {pet_info} (Уровень {pet_game['level']})",
        reply_markup=main_keyboard
    )

async def main():
    logging.basicConfig(level=logging.INFO)
    await bot.delete_webhook(drop_pending_updates=False)
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())

if __name__ == "__main__":
    asyncio.run(main())
