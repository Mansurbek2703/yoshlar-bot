from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, User as TgUser
from sqlalchemy.ext.asyncio import AsyncSession
from bot.services.user_service import UserService


class AuthMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        tg_user: TgUser = data.get("event_from_user")
        session: AsyncSession = data.get("session")

        if tg_user and session:
            user_service = UserService(session)
            db_user = await user_service.get_or_create_user(
                telegram_id=tg_user.id,
                username=tg_user.username,
                first_name=tg_user.first_name,
                last_name=tg_user.last_name,
            )
            is_superadmin = user_service.is_superadmin(tg_user.id)
            is_admin = await user_service.is_admin(tg_user.id)

            data["user"] = db_user
            data["is_superadmin"] = is_superadmin
            data["is_admin"] = is_admin
        else:
            data["user"] = None
            data["is_superadmin"] = False
            data["is_admin"] = False

        return await handler(event, data)
