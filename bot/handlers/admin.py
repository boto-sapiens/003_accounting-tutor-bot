"""Admin handler for administrative functions"""
import logging
import csv
from datetime import datetime
from io import StringIO
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile, BufferedInputFile
from bot.data.database import user_repo, registration_repo
from config import config, DEMO_MODE

router = Router()
logger = logging.getLogger(__name__)


def is_admin(user_id: int) -> bool:
    """Check if user is admin (in DEMO_MODE, everyone is admin)"""
    if DEMO_MODE:
        return True
    admin_ids = config.get('admins', [])
    return user_id in admin_ids


@router.message(Command("admin"))
async def cmd_admin(message: Message):
    """Show admin menu"""
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет доступа к админ-панели.")
        logger.warning(f"Unauthorized admin access attempt by {message.from_user.id} (@{message.from_user.username})")
        return
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👥 Список зарегистрированных", callback_data="admin_registered")],
        [InlineKeyboardButton(text="📊 Общая статистика", callback_data="admin_stats")],
        [InlineKeyboardButton(text="📂 Экспорт базы", callback_data="admin_export")],
        [InlineKeyboardButton(text="📋 Регистрации на встречи", callback_data="admin_meeting_regs")]
    ])
    
    demo_notice = "🧪 <b>DEMO MODE</b> - Админ-панель доступна всем\n\n" if DEMO_MODE else ""
    
    await message.answer(
        f"{demo_notice}👨‍💼 <b>Админ-панель</b>\n\n"
        "Выберите действие:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    
    logger.info(f"Admin panel accessed by {message.from_user.id} (@{message.from_user.username})")


@router.message(Command("myid"))
async def cmd_myid(message: Message):
    """Show user's Telegram ID"""
    await message.answer(
        f"ℹ️ <b>Ваша информация:</b>\n\n"
        f"👤 ID: <code>{message.from_user.id}</code>\n"
        f"📛 Username: @{message.from_user.username}\n"
        f"📝 Имя: {message.from_user.first_name} {message.from_user.last_name or ''}",
        parse_mode="HTML"
    )


@router.callback_query(F.data == "admin_registered")
async def admin_show_registered(callback: CallbackQuery):
    """Show list of registered users"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа")
        return
    
    users = user_repo.get_all_registered_users()
    
    if not users:
        await callback.message.edit_text("📋 Нет зарегистрированных пользователей.")
        await callback.answer()
        return
    
    text = "👥 <b>Зарегистрированные пользователи</b>\n\n"
    
    for i, user in enumerate(users, 1):
        username_str = f"@{user.username}" if user.username else "без username"
        text += f"{i}. {user.first_name} ({username_str})\n"
        text += f"   ID: <code>{user.tg_id}</code>\n\n"
    
    text += f"\n<b>Всего:</b> {len(users)} чел."
    
    await callback.message.edit_text(text, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "admin_stats")
async def admin_show_stats(callback: CallbackQuery):
    """Show general statistics"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа")
        return
    
    # Get user statistics
    conn = user_repo._get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM users WHERE is_registered = 1")
    registered_users = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM users WHERE is_active = 0")
    unsubscribed_users = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM registrations")
    total_registrations = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(DISTINCT user_id) FROM registrations WHERE status = 'registered'")
    users_with_registrations = cursor.fetchone()[0]
    
    conn.close()
    
    text = "📊 <b>Общая статистика</b>\n\n"
    text += f"👥 <b>Пользователи:</b>\n"
    text += f"   • Всего: {total_users}\n"
    text += f"   • Подписаны на рассылку: {registered_users}\n"
    text += f"   • Отписались: {unsubscribed_users}\n\n"
    text += f"📝 <b>Регистрации:</b>\n"
    text += f"   • Всего записей: {total_registrations}\n"
    text += f"   • Пользователей с записями: {users_with_registrations}\n"
    
    await callback.message.edit_text(text, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "admin_meeting_regs")
async def admin_show_meeting_registrations(callback: CallbackQuery):
    """Show registrations for upcoming meetings"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа")
        return
    
    meetings = config.get('upcoming_meetings', [])
    today = datetime.now().date()
    
    text = "📋 <b>Регистрации на встречи</b>\n\n"
    
    for meeting in meetings:
        meeting_date_obj = datetime.strptime(meeting['date'], '%Y-%m-%d').date()
        
        # Skip past meetings
        if meeting_date_obj < today:
            continue
        
        formatted_date = meeting_date_obj.strftime('%d.%m.%Y')
        registrations = registration_repo.get_meeting_registrations(meeting['date'])
        
        text += f"📅 <b>{formatted_date}</b> - {meeting['topic']}\n"
        
        if registrations:
            text += f"   Записано: {len(registrations)} чел.\n"
            for tg_id, first_name, last_name, username, created_at in registrations:
                username_str = f"@{username}" if username else "без username"
                text += f"   • {first_name} ({username_str})\n"
        else:
            text += "   Пока нет записей\n"
        
        text += "\n"
    
    await callback.message.edit_text(text, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "admin_export")
async def admin_export_data(callback: CallbackQuery):
    """Export data to CSV"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа")
        return
    
    await callback.message.edit_text("⏳ Экспортирую данные...")
    
    # Export users
    users = user_repo.get_all_registered_users()
    
    # Create users CSV
    users_csv = StringIO()
    users_writer = csv.writer(users_csv)
    users_writer.writerow(['TG_ID', 'First Name', 'Last Name', 'Username', 'Is Active', 'Is Registered'])
    
    for user in users:
        users_writer.writerow([
            user.tg_id,
            user.first_name,
            user.last_name,
            user.username,
            'Да' if user.is_active else 'Нет',
            'Да' if user.is_registered else 'Нет'
        ])
    
    # Export registrations
    registrations = registration_repo.get_all_registrations_with_users()
    
    regs_csv = StringIO()
    regs_writer = csv.writer(regs_csv)
    regs_writer.writerow(['TG_ID', 'First Name', 'Username', 'Meeting Date', 'Status', 'Registered At'])
    
    for tg_id, first_name, last_name, username, meeting_date, status, created_at in registrations:
        regs_writer.writerow([
            tg_id,
            f"{first_name} {last_name or ''}".strip(),
            username,
            meeting_date,
            status,
            created_at
        ])
    
    # Send files
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    users_file = BufferedInputFile(
        users_csv.getvalue().encode('utf-8-sig'),
        filename=f'users_{timestamp}.csv'
    )
    
    regs_file = BufferedInputFile(
        regs_csv.getvalue().encode('utf-8-sig'),
        filename=f'registrations_{timestamp}.csv'
    )
    
    await callback.message.answer_document(
        users_file,
        caption="📄 Экспорт пользователей"
    )
    
    await callback.message.answer_document(
        regs_file,
        caption="📄 Экспорт регистраций"
    )
    
    await callback.message.answer("✅ Экспорт завершён!")
    await callback.answer()
    
    logger.info(f"Data exported by admin {callback.from_user.id}")

