import asyncio
import logging
import os

from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from aiogram.utils.media_group import MediaGroupBuilder

# Твой ID администратора
ADMIN_ID = 7962428470

# Получаем токен из переменных окружения Render
TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise ValueError("Переменная BOT_TOKEN не найдена! Добавь её в Render → Environment.")

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())


# --- Состояния ---
class TaskState(StatesGroup):
    waiting_for_photos = State()


# --- Клавиатуры ---
main_kb = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="📢 Начать задание")]],
    resize_keyboard=True
)

submit_kb = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="📸 Отправить выполнение")]],
    resize_keyboard=True
)


# --- 1. /start ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Привет! 👋\n\n"
        "Это бот для выполнения заданий.\n"
        "Нажми кнопку ниже, чтобы получить задание.",
        reply_markup=main_kb
    )


# --- 2. Кнопка «Начать задание» ---
@dp.message(F.text == "📢 Начать задание")
async def start_task(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "📋 *Ваше задание:*\n\n"
        "Необходимо сделать *10 комментариев* в TikTok.\n\n"
        "После выполнения нажми кнопку «📸 Отправить выполнение» "
        "и загрузи 10 скриншотов.",
        parse_mode="Markdown",
        reply_markup=submit_kb
    )


# --- 5. Кнопка «Отправить выполнение» ---
@dp.message(F.text == "📸 Отправить выполнение")
async def ask_for_photos(message: types.Message, state: FSMContext):
    await state.set_state(TaskState.waiting_for_photos)
    await state.update_data(photos=[])
    await message.answer(
        "📸 Отправь 10 скриншотов (можно альбомом или по одному).\n\n"
        "Когда закончишь — нажми /done",
        reply_markup=ReplyKeyboardRemove()
    )


# --- 6. Приём фото ---
@dp.message(TaskState.waiting_for_photos, F.photo)
async def handle_photo(message: types.Message, state: FSMContext):
    data = await state.get_data()
    photos = data.get("photos", [])
    photos.append(message.photo[-1].file_id)
    await state.update_data(photos=photos)

    count = len(photos)
    await message.answer(f"✅ Принято фото: {count}/10")

    if count >= 10:
        await message.answer("У тебя уже 10 фото! Нажми /done, чтобы отправить заявку.")


# --- Завершение сбора фото ---
@dp.message(TaskState.waiting_for_photos, Command("done"))
async def finish_task(message: types.Message, state: FSMContext):
    data = await state.get_data()
    photos = data.get("photos", [])

    if not photos:
        await message.answer("Ты не отправил ни одного фото. Нажми «📸 Отправить выполнение» заново.")
        await state.clear()
        return

    # 7. Подтверждение пользователю
    await message.answer(
        "✅ Заявка отправлена на проверку. Ожидай.",
        reply_markup=main_kb
    )

    # 8. Отправка заявки админу
    try:
        await bot.send_message(
            ADMIN_ID,
            f"🔔 *Новая заявка!*\n"
            f"От: @{message.from_user.username or 'без username'}\n"
            f"ID: `{message.from_user.id}`\n"
            f"Фото: {len(photos)} шт.",
            parse_mode="Markdown"
        )

        # Отправляем альбомами по 10 фото (лимит Telegram)
        for i in range(0, len(photos), 10):
            chunk = photos[i:i + 10]
            media_group = MediaGroupBuilder()
            for photo_id in chunk:
                media_group.add_photo(media=photo_id)
            await bot.send_media_group(chat_id=ADMIN_ID, media=media_group.build())

    except Exception as e:
        logging.error(f"Ошибка отправки админу: {e}")
        await message.answer("⚠️ Ошибка при отправке заявки. Попробуй позже.")

    await state.clear()


# --- Игнорирование лишнего текста ---
@dp.message(TaskState.waiting_for_photos)
async def ignore_other(message: types.Message):
    await message.answer("Пожалуйста, отправь фото или нажми /done, чтобы завершить.")


async def main():
    logging.basicConfig(level=logging.INFO)
    print("🚀 Бот запущен...")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
