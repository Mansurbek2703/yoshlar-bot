from aiogram import Router
from bot.handlers.common import router as common_router
from bot.handlers.appeal import router as appeal_router
from bot.handlers.admin import router as admin_router
from bot.handlers.broadcast import router as broadcast_router


def get_main_router() -> Router:
    main_router = Router()
    # Order matters: specific handlers before fallback common handlers
    main_router.include_router(admin_router)
    main_router.include_router(broadcast_router)
    main_router.include_router(appeal_router)
    main_router.include_router(common_router)
    return main_router
