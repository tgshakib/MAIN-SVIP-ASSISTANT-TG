import asyncio
import logging
import os
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand
from config import BOT_TOKEN, ADMIN_ID
from handlers import user, admin, payment, converter
from handlers import language_handler, mm_setup, mm_session, mm_admin_access, mm_menu, mm_payment, forex_calculator
from handlers import mailing
from scheduler import start_scheduler
from admin_msg_tracker import AdminOutgoingTracker
from user_msg_tracker import UserOutgoingTracker
import mm_database as mmdb

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

async def main():
    bot = Bot(token=BOT_TOKEN)
    bot.session.middleware(AdminOutgoingTracker())
    bot.session.middleware(UserOutgoingTracker())
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    # Register all routers
    dp.include_router(mailing.router)
    dp.include_router(admin.router)
    dp.include_router(payment.router)
    dp.include_router(mm_admin_access.router)
    dp.include_router(mm_payment.router)
    dp.include_router(mm_setup.router)
    dp.include_router(mm_session.router)
    dp.include_router(mm_menu.router)
    dp.include_router(forex_calculator.router)
    dp.include_router(language_handler.router)
    dp.include_router(user.router)
    dp.include_router(converter.router)

    # Set bot command menu
    await bot.set_my_commands([
        BotCommand(command="start",   description="Start bot and open menu"),
        BotCommand(command="admin",   description="Admin panel"),
        BotCommand(command="convert", description="Open timezone converter"),
    ])

    # Grant admin(s) automatic lifetime MM access on every startup
    admin_ids = []
    if ADMIN_ID:
        admin_ids.append(ADMIN_ID)
    raw_admin_ids = os.environ.get("ADMIN_IDS", "")
    for aid in raw_admin_ids.split(","):
        aid = aid.strip()
        if aid.isdigit():
            admin_id_int = int(aid)
            if admin_id_int not in admin_ids:
                admin_ids.append(admin_id_int)
    if admin_ids:
        mmdb.grant_admin_lifetime_access(admin_ids)

    # Start background scheduler
    await start_scheduler(bot)

    logger.info("Bot is starting...")
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())

if __name__ == "__main__":
    asyncio.run(main())
