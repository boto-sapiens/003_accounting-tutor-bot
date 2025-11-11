"""Start and stop command handlers"""
import logging
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from bot.data.database import user_repo

router = Router()
logger = logging.getLogger(__name__)


@router.message(Command("start"))
async def cmd_start(message: Message):
    """Handle /start command"""
    tg_id = message.from_user.id
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name
    username = message.from_user.username
    
    # Check if user exists
    user = user_repo.get_user_by_tg_id(tg_id)
    
    if not user:
        # Create new user
        user_repo.create_user(
            tg_id=tg_id,
            first_name=first_name,
            last_name=last_name,
            username=username
        )
        logger.info(f"New user created: {tg_id} (@{username})")
    else:
        # Reactivate user if they were inactive
        if not user.is_active:
            user_repo.update_user(tg_id, is_active=True)
            logger.info(f"User reactivated: {tg_id} (@{username})")
    
    # Send welcome message with buttons
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Да", callback_data="register_yes"),
            InlineKeyboardButton(text="Нет", callback_data="register_no")
        ]
    ])
    
    await message.answer(
        "👋 Привет! Я <b>Тамара — бухгалтер</b>.\n\n"
        "Помогаю бизнесу навести порядок в финансах, рассчитать налоги и сэкономить время.\n\n"
        "📊 Хочу показать, как работает бот для автоматизации бухгалтерии.\n\n"
        "💡 <b>Хотите получать приглашения на встречи по средам?</b>",
        reply_markup=keyboard,
        parse_mode="HTML"
    )


@router.message(Command("stop"))
async def cmd_stop(message: Message):
    """Handle /stop command"""
    tg_id = message.from_user.id
    
    user = user_repo.get_user_by_tg_id(tg_id)
    
    if user:
        user_repo.update_user(tg_id, is_active=False)
        logger.info(f"User unsubscribed: {tg_id}")
        await message.answer("Вы отписались. Возвращайтесь, когда будете готовы 🙂")
    else:
        await message.answer("Вы не были зарегистрированы. Используйте /start для начала.")


@router.callback_query(F.data == "register_yes")
async def register_yes(callback: CallbackQuery):
    """Handle 'Yes' button for registration"""
    tg_id = callback.from_user.id
    
    user_repo.update_user(tg_id, is_registered=True)
    logger.info(f"User registered: {tg_id}")
    
    # Import here to avoid circular dependency
    from bot.handlers.menu import get_main_menu_keyboard
    
    await callback.message.edit_text(
        "✅ Отлично! Я буду присылать тебе приглашения на встречи.\n\n"
        "Используйте меню ниже для навигации:"
    )
    
    # Send menu
    await callback.message.answer(
        "📋 Главное меню доступно. Выберите действие:",
        reply_markup=get_main_menu_keyboard()
    )
    
    await callback.answer()


@router.callback_query(F.data == "register_no")
async def register_no(callback: CallbackQuery):
    """Handle 'No' button for registration"""
    tg_id = callback.from_user.id
    
    user_repo.update_user(tg_id, is_registered=False)
    logger.info(f"User declined registration: {tg_id}")
    
    await callback.message.edit_text(
        "Хорошо! Если потребуется — дай знать командой /start."
    )
    await callback.answer()


@router.callback_query(F.data == "meeting_yes")
async def meeting_yes(callback: CallbackQuery):
    """Handle 'Yes, I will come' button"""
    tg_id = callback.from_user.id
    
    user_repo.update_user(tg_id, last_response="yes")
    logger.info(f"User confirmed attendance: {tg_id}")
    
    await callback.message.edit_text(
        "Отлично! Буду ждать тебя в среду 😊\n"
        "Напомню о встрече перед началом."
    )
    await callback.answer()


@router.callback_query(F.data == "meeting_no")
async def meeting_no(callback: CallbackQuery):
    """Handle 'No, I cannot come' button"""
    tg_id = callback.from_user.id
    
    user_repo.update_user(tg_id, last_response="no")
    logger.info(f"User declined attendance: {tg_id}")
    
    await callback.message.edit_text(
        "Понятно. Жаль, что не получится! 🙂\n"
        "В следующий раз обязательно увидимся."
    )
    await callback.answer()

