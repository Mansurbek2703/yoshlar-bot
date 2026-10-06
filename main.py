import asyncio
import logging
import os
import sys
from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import ErrorEvent
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

from bot.config import settings
from bot.database import engine, init_db
from bot.handlers import get_main_router
from bot.middlewares import AuthMiddleware, DatabaseMiddleware

# Ensure logs directory
os.makedirs("logs", exist_ok=True)

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("logs/bot.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger("youth_bot")


async def on_startup(bot: Bot) -> None:
    logger.info("Starting up Youth Affairs Bot...")
    # Initialize database tables
    await init_db()

    # Inform admin on startup
    me = await bot.get_me()
    logger.info(f"Bot authorized as @{me.username} (ID: {me.id})")
    logger.info(f"Loaded {len(settings.admin_ids)} admin IDs from configuration.")

    if settings.USE_WEBHOOK:
        logger.info(f"Setting webhook to: {settings.webhook_url}")
        await bot.set_webhook(
            url=settings.webhook_url,
            secret_token=settings.WEBHOOK_SECRET,
            drop_pending_updates=True,
        )
        logger.info("Webhook successfully registered with Telegram.")
    else:
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("Webhook deleted, running in long-polling mode.")


async def on_shutdown(bot: Bot) -> None:
    logger.info("Shutting down Youth Affairs Bot...")
    if settings.USE_WEBHOOK:
        try:
            await bot.delete_webhook()
        except Exception as e:
            logger.warning(f"Error deleting webhook on shutdown: {e}")
    await bot.session.close()
    await engine.dispose()
    logger.info("Bot shutdown complete.")


async def global_error_handler(event: ErrorEvent) -> bool:
    logger.exception(f"Unhandled exception caught: {event.exception}", exc_info=event.exception)
    try:
        if event.update.message:
            await event.update.message.answer(
                "⚠️ Texnik xatolik yuz berdi. Iltimos, birozdan so‘ng qayta urinib ko‘ring."
            )
        elif event.update.callback_query:
            await event.update.callback_query.answer(
                "⚠️ Texnik xatolik yuz berdi. Iltimos, birozdan so‘ng qayta urinib ko‘ring.",
                show_alert=True,
            )
    except Exception as e:
        logger.warning(f"Failed to send friendly error message to user: {e}")
    return True


async def health_check(request: web.Request) -> web.Response:
    return web.json_response({
        "status": "healthy",
        "service": "Youth Affairs Appeals Telegram Bot",
        "mode": "webhook" if settings.USE_WEBHOOK else "polling",
    })


def create_bot_and_dispatcher() -> tuple[Bot, Dispatcher]:
    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=MemoryStorage())

    # Register Middlewares
    dp.message.middleware(DatabaseMiddleware())
    dp.callback_query.middleware(DatabaseMiddleware())
    dp.message.middleware(AuthMiddleware())
    dp.callback_query.middleware(AuthMiddleware())

    # Register Main Router
    dp.include_router(get_main_router())

    # Register Global Error Handler
    dp.errors.register(global_error_handler)

    return bot, dp


def run_webhook():
    bot, dp = create_bot_and_dispatcher()

    app = web.Application()
    app.router.add_get("/", health_check)
    app.router.add_get("/health", health_check)

    # Register webhook handler
    webhook_requests_handler = SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
        secret_token=settings.WEBHOOK_SECRET,
    )
    webhook_requests_handler.register(app, path=settings.WEBHOOK_PATH)

    setup_application(app, dp, bot=bot)

    async def on_app_startup(app: web.Application):
        await on_startup(bot)

    async def on_app_cleanup(app: web.Application):
        await on_shutdown(bot)

    app.on_startup.append(on_app_startup)
    app.on_cleanup.append(on_app_cleanup)

    logger.info(
        f"Starting webhook server on {settings.WEB_SERVER_HOST}:{settings.WEB_SERVER_PORT}..."
    )
    web.run_app(
        app,
        host=settings.WEB_SERVER_HOST,
        port=settings.WEB_SERVER_PORT,
    )


async def run_polling():
    bot, dp = create_bot_and_dispatcher()
    await on_startup(bot)
    try:
        logger.info("Starting polling loop...")
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await on_shutdown(bot)


def main():
    if settings.USE_WEBHOOK:
        run_webhook()
    else:
        asyncio.run(run_polling())


if __name__ == "__main__":
    main()
