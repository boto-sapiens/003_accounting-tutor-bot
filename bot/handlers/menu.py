"""Menu handler for main bot navigation"""
import logging
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton

router = Router()
logger = logging.getLogger(__name__)


def get_main_menu_keyboard():
    """Get main menu keyboard"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="🔔 Мои встречи"),
                KeyboardButton(text="📅 Ближайшие встречи")
            ],
            [
                KeyboardButton(text="📝 Записаться на встречу"),
                KeyboardButton(text="🧩 Админ-панель (демо)")
            ],
            [
                KeyboardButton(text="🚫 Отписаться")
            ]
        ],
        resize_keyboard=True,
        persistent=True
    )
    return keyboard


@router.message(Command("menu"))
async def cmd_menu(message: Message):
    """Show main menu"""
    await message.answer(
        "📋 Главное меню\n\n"
        "Выберите действие:",
        reply_markup=get_main_menu_keyboard()
    )

