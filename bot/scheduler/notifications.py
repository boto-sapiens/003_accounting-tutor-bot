"""Notification scheduler for meeting invitations and reminders"""
import logging
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import pytz

from bot.data.database import user_repo
from config import config, BOT_TOKEN

logger = logging.getLogger(__name__)

# Get timezone from config
TIMEZONE = pytz.timezone(config['timezone'])

# Global scheduler
scheduler = AsyncIOScheduler(timezone=TIMEZONE)


async def send_invitation(bot: Bot):
    """Send meeting invitation on Monday at 10:00 MSK"""
    logger.info("Starting invitation broadcast...")
    
    users = user_repo.get_all_registered_users()
    meeting_topic = config['meeting']['topic']
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Да, буду", callback_data="meeting_yes"),
            InlineKeyboardButton(text="Нет, не смогу", callback_data="meeting_no")
        ]
    ])
    
    message_text = (
        f"В среду будет встреча на тему: «{meeting_topic}».\n"
        f"Придёшь? 🙂"
    )
    
    success_count = 0
    error_count = 0
    
    for user in users:
        try:
            await bot.send_message(
                chat_id=user.tg_id,
                text=message_text,
                reply_markup=keyboard
            )
            success_count += 1
            logger.info(f"Invitation sent to user {user.tg_id}")
        except Exception as e:
            error_count += 1
            logger.error(f"Failed to send invitation to user {user.tg_id}: {e}")
    
    logger.info(f"Invitation broadcast completed. Success: {success_count}, Errors: {error_count}")


async def send_first_reminder(bot: Bot):
    """Send first reminder on Wednesday at 09:00 MSK to those who confirmed"""
    logger.info("Starting first reminder broadcast...")
    
    users = user_repo.get_users_by_response("yes")
    meeting_topic = config['meeting']['topic']
    meeting_time = config['meeting']['time']
    meeting_link = config['meeting']['link']
    
    message_text = (
        f"Доброе утро! Сегодня встреча: «{meeting_topic}».\n"
        f"Начало в {meeting_time}. Ссылка: {meeting_link}"
    )
    
    success_count = 0
    error_count = 0
    
    for user in users:
        try:
            await bot.send_message(
                chat_id=user.tg_id,
                text=message_text
            )
            success_count += 1
            logger.info(f"First reminder sent to user {user.tg_id}")
        except Exception as e:
            error_count += 1
            logger.error(f"Failed to send first reminder to user {user.tg_id}: {e}")
    
    logger.info(f"First reminder broadcast completed. Success: {success_count}, Errors: {error_count}")


async def send_second_reminder(bot: Bot):
    """Send second reminder on Wednesday at 10:40 MSK to those who confirmed"""
    logger.info("Starting second reminder broadcast...")
    
    users = user_repo.get_users_by_response("yes")
    meeting_link = config['meeting']['link']
    
    message_text = (
        f"Через 20 минут встречаемся! Вот ссылка: {meeting_link}"
    )
    
    success_count = 0
    error_count = 0
    
    for user in users:
        try:
            await bot.send_message(
                chat_id=user.tg_id,
                text=message_text
            )
            success_count += 1
            logger.info(f"Second reminder sent to user {user.tg_id}")
        except Exception as e:
            error_count += 1
            logger.error(f"Failed to send second reminder to user {user.tg_id}: {e}")
    
    logger.info(f"Second reminder broadcast completed. Success: {success_count}, Errors: {error_count}")


def setup_scheduler(bot: Bot):
    """Setup scheduler with all jobs"""
    
    # Parse schedule from config
    schedule_config = config['schedule']
    
    # Monday 10:00 MSK - Send invitation
    invitation_day = schedule_config['invitation_day']
    invitation_time = schedule_config['invitation_time']
    hour, minute = map(int, invitation_time.split(':'))
    
    scheduler.add_job(
        send_invitation,
        CronTrigger(day_of_week=_day_to_cron(invitation_day), hour=hour, minute=minute, timezone=TIMEZONE),
        args=[bot],
        id='send_invitation',
        name='Send meeting invitation',
        replace_existing=True
    )
    logger.info(f"Scheduled invitation: {invitation_day} at {invitation_time} {TIMEZONE}")
    
    # Wednesday 09:00 MSK - First reminder
    reminder1_day = schedule_config['reminder_1_day']
    reminder1_time = schedule_config['reminder_1_time']
    hour, minute = map(int, reminder1_time.split(':'))
    
    scheduler.add_job(
        send_first_reminder,
        CronTrigger(day_of_week=_day_to_cron(reminder1_day), hour=hour, minute=minute, timezone=TIMEZONE),
        args=[bot],
        id='send_first_reminder',
        name='Send first reminder',
        replace_existing=True
    )
    logger.info(f"Scheduled first reminder: {reminder1_day} at {reminder1_time} {TIMEZONE}")
    
    # Wednesday 10:40 MSK - Second reminder
    reminder2_day = schedule_config['reminder_2_day']
    reminder2_time = schedule_config['reminder_2_time']
    hour, minute = map(int, reminder2_time.split(':'))
    
    scheduler.add_job(
        send_second_reminder,
        CronTrigger(day_of_week=_day_to_cron(reminder2_day), hour=hour, minute=minute, timezone=TIMEZONE),
        args=[bot],
        id='send_second_reminder',
        name='Send second reminder',
        replace_existing=True
    )
    logger.info(f"Scheduled second reminder: {reminder2_day} at {reminder2_time} {TIMEZONE}")
    
    # Start scheduler
    scheduler.start()
    logger.info("Scheduler started successfully")


def _day_to_cron(day: str) -> str:
    """Convert day name to cron format"""
    days = {
        'monday': 'mon',
        'tuesday': 'tue',
        'wednesday': 'wed',
        'thursday': 'thu',
        'friday': 'fri',
        'saturday': 'sat',
        'sunday': 'sun'
    }
    return days.get(day.lower(), day)


def stop_scheduler():
    """Stop scheduler"""
    if scheduler.running:
        scheduler.shutdown()
        logger.info("Scheduler stopped")

