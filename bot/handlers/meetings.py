"""Meetings handler for viewing and registering for meetings"""
import logging
from datetime import datetime
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from bot.data.database import user_repo, registration_repo
from config import config

router = Router()
logger = logging.getLogger(__name__)


def get_upcoming_meetings():
    """Get list of upcoming meetings"""
    meetings = config.get('upcoming_meetings', [])
    today = datetime.now().date()
    
    # Filter only future meetings
    upcoming = []
    for meeting in meetings:
        meeting_date = datetime.strptime(meeting['date'], '%Y-%m-%d').date()
        if meeting_date >= today:
            upcoming.append(meeting)
    
    return upcoming


@router.message(F.text == "📅 Ближайшие встречи")
async def show_upcoming_meetings(message: Message):
    """Show list of upcoming meetings"""
    meetings = get_upcoming_meetings()
    
    if not meetings:
        await message.answer("На данный момент нет запланированных встреч.")
        return
    
    text = "📅 <b>Ближайшие встречи</b>\n\n"
    
    for meeting in meetings:
        meeting_date = datetime.strptime(meeting['date'], '%Y-%m-%d')
        formatted_date = meeting_date.strftime('%d.%m.%Y (%A)')
        
        # Translate day name to Russian
        day_names = {
            'Monday': 'Понедельник',
            'Tuesday': 'Вторник',
            'Wednesday': 'Среда',
            'Thursday': 'Четверг',
            'Friday': 'Пятница',
            'Saturday': 'Суббота',
            'Sunday': 'Воскресенье'
        }
        for en, ru in day_names.items():
            formatted_date = formatted_date.replace(en, ru)
        
        text += f"📌 <b>{formatted_date} в {meeting['time']}</b>\n"
        text += f"   {meeting['topic']}\n\n"
    
    await message.answer(text, parse_mode="HTML")


@router.message(F.text == "🔔 Мои встречи")
async def show_my_meetings(message: Message):
    """Show user's registered meetings"""
    tg_id = message.from_user.id
    user = user_repo.get_user_by_tg_id(tg_id)
    
    if not user:
        await message.answer("Вы не зарегистрированы. Отправьте /start")
        return
    
    registrations = registration_repo.get_user_registrations(user.id)
    
    if not registrations:
        await message.answer(
            "У вас пока нет записей на встречи.\n\n"
            "Используйте кнопку «📝 Записаться на встречу» чтобы выбрать встречу."
        )
        return
    
    # Get meeting details from config
    meetings_dict = {}
    for meeting in config.get('upcoming_meetings', []):
        meetings_dict[meeting['date']] = meeting
    
    text = "🔔 <b>Ваши встречи</b>\n\n"
    
    today = datetime.now().date()
    active_count = 0
    
    for reg in registrations:
        meeting_date = datetime.strptime(reg.meeting_date, '%Y-%m-%d').date()
        
        # Skip past meetings
        if meeting_date < today:
            continue
        
        active_count += 1
        formatted_date = datetime.strptime(reg.meeting_date, '%Y-%m-%d').strftime('%d.%m.%Y')
        
        meeting_info = meetings_dict.get(reg.meeting_date, {})
        topic = meeting_info.get('topic', 'Встреча')
        time = meeting_info.get('time', '11:00')
        
        status_emoji = "✅" if reg.status == "registered" else "❌"
        
        text += f"{status_emoji} <b>{formatted_date} в {time}</b>\n"
        text += f"   {topic}\n\n"
    
    if active_count == 0:
        await message.answer("У вас нет предстоящих встреч.")
    else:
        await message.answer(text, parse_mode="HTML")


@router.message(F.text == "📝 Записаться на встречу")
async def register_for_meeting_menu(message: Message):
    """Show menu to register for a meeting"""
    tg_id = message.from_user.id
    user = user_repo.get_user_by_tg_id(tg_id)
    
    if not user:
        await message.answer("Вы не зарегистрированы. Отправьте /start")
        return
    
    meetings = get_upcoming_meetings()
    
    if not meetings:
        await message.answer("На данный момент нет доступных встреч для записи.")
        return
    
    # Create inline keyboard with meetings
    keyboard_buttons = []
    
    for meeting in meetings:
        meeting_date = datetime.strptime(meeting['date'], '%Y-%m-%d')
        formatted_date = meeting_date.strftime('%d.%m')
        
        # Check if already registered
        is_registered = registration_repo.is_registered(user.id, meeting['date'])
        
        if is_registered:
            button_text = f"✅ {formatted_date} - {meeting['topic'][:30]}..."
            callback_data = f"already_registered:{meeting['date']}"
        else:
            button_text = f"📝 {formatted_date} - {meeting['topic'][:30]}..."
            callback_data = f"register:{meeting['date']}"
        
        keyboard_buttons.append([InlineKeyboardButton(
            text=button_text,
            callback_data=callback_data
        )])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    
    await message.answer(
        "📝 <b>Выберите встречу для записи:</b>\n\n"
        "✅ - вы уже записаны\n"
        "📝 - нажмите для записи",
        reply_markup=keyboard,
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("register:"))
async def register_for_meeting(callback: CallbackQuery):
    """Register user for a meeting"""
    tg_id = callback.from_user.id
    user = user_repo.get_user_by_tg_id(tg_id)
    
    if not user:
        await callback.answer("Ошибка: пользователь не найден")
        return
    
    meeting_date = callback.data.split(":")[1]
    
    # Create registration
    result = registration_repo.create_registration(user.id, meeting_date)
    
    if result:
        # Get meeting info
        meetings = config.get('upcoming_meetings', [])
        meeting_info = next((m for m in meetings if m['date'] == meeting_date), None)
        
        if meeting_info:
            formatted_date = datetime.strptime(meeting_date, '%Y-%m-%d').strftime('%d.%m.%Y')
            
            await callback.message.edit_text(
                f"✅ <b>Вы записаны!</b>\n\n"
                f"📅 Дата: {formatted_date}\n"
                f"🕐 Время: {meeting_info['time']}\n"
                f"📌 Тема: {meeting_info['topic']}\n\n"
                f"Мы напомним вам о встрече перед началом.",
                parse_mode="HTML"
            )
        
        logger.info(f"User {tg_id} registered for meeting {meeting_date}")
        await callback.answer("Вы успешно записаны!")
    else:
        await callback.answer("Вы уже записаны на эту встречу")


@router.callback_query(F.data.startswith("already_registered:"))
async def already_registered(callback: CallbackQuery):
    """Handle click on already registered meeting"""
    await callback.answer("Вы уже записаны на эту встречу ✅")


@router.message(F.text == "🚫 Отписаться")
async def unsubscribe(message: Message):
    """Unsubscribe from newsletters"""
    tg_id = message.from_user.id
    user = user_repo.get_user_by_tg_id(tg_id)
    
    if user:
        user_repo.update_user(tg_id, is_active=False, is_registered=False)
        logger.info(f"User {tg_id} unsubscribed")
        await message.answer(
            "🚫 Вы отписались от рассылок.\n\n"
            "Возвращайтесь, когда будете готовы! Отправьте /start чтобы снова подписаться. 🙂"
        )
    else:
        await message.answer("Вы не были зарегистрированы.")

