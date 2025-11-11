"""About handler - Demo admin panel"""
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

router = Router()
logger = logging.getLogger(__name__)


@router.message(F.text == "🧩 Админ-панель (демо)")
async def show_demo_admin(message: Message):
    """Show demo admin panel"""
    
    text = (
        "⚙️ <b>Это демо-версия админ-панели</b>\n\n"
        "🧪 В этом шоуруме функции доступны всем пользователям для демонстрации возможностей.\n\n"
        "🔐 <b>В реальном боте</b> доступ к админ-панели ограничен и доступен только администраторам.\n\n"
        "📊 <b>Доступные функции</b>:\n"
        "• Просмотр статистики\n"
        "• Список зарегистрированных\n"
        "• Регистрации на встречи\n"
        "• Экспорт данных в CSV\n\n"
        "💡 Используйте команду <code>/admin</code> для доступа к полной панели управления."
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Открыть админ-панель", callback_data="open_admin")],
        [InlineKeyboardButton(text="🔙 Назад в меню", callback_data="back_to_menu")]
    ])
    
    await message.answer(text, reply_markup=keyboard, parse_mode="HTML")
    logger.info(f"Demo admin info shown to user {message.from_user.id}")


@router.callback_query(F.data == "open_admin")
async def open_admin_panel(callback: CallbackQuery):
    """Open admin panel via callback"""
    # Import here to avoid circular dependency
    from bot.handlers.admin import cmd_admin
    
    # Delete the inline keyboard message
    await callback.message.delete()
    
    # Show admin panel
    await cmd_admin(callback.message)
    await callback.answer()


@router.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: CallbackQuery):
    """Go back to main menu"""
    
    await callback.message.delete()
    await callback.message.answer(
        "📋 Главное меню. Выберите действие:"
    )
    await callback.answer()

