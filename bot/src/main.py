import asyncio
import logging
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN

# Import handlers
from bot.handlers import start, menu, meetings, admin, about

# Import scheduler
from bot.scheduler.notifications import setup_scheduler, stop_scheduler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """Main bot entry point"""
    # Initialize bot and dispatcher
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    
    # Register routers (order matters - more specific first)
    dp.include_router(admin.router)
    dp.include_router(about.router)
    dp.include_router(menu.router)
    dp.include_router(meetings.router)
    dp.include_router(start.router)
    
    # Setup scheduler
    setup_scheduler(bot)
    
    logger.info("Bot starting...")
    logger.info("Scheduler initialized with meeting notifications")
    logger.info("All handlers registered: start, menu, meetings, admin, about")
    
    # Start polling
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        stop_scheduler()
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
        stop_scheduler()

