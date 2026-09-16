import asyncio
import os
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.media_group import MediaGroupBuilder

# Токен автоматически подтягивается из Environment Variables на Render
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 7962428470

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

class TaskState(StatesGroup):
    waiting_for_photos = State()

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📢 Начать задание")]],
        resize_keyboard=True
    )
    await message.answer("Привет! Нажми кнопку ниже, чтобы начать.", reply_markup=kb)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
