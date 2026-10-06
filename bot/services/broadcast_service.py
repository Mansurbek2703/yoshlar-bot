import asyncio
import logging
from typing import Optional
from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError, TelegramRetryAfter
from sqlalchemy.ext.asyncio import AsyncSession
from bot.database.models import Broadcast, User
from bot.services.user_service import UserService

logger = logging.getLogger(__name__)


class BroadcastService:
    def __init__(self, session: AsyncSession, bot: Bot):
        self.session = session
        self.bot = bot

    async def execute_broadcast(
        self,
        admin_id: int,
        source_chat_id: int,
        source_message_id: int,
        message_type: str = "text",
        content: Optional[str] = None,
    ) -> Broadcast:
        user_service = UserService(self.session)
        users = await user_service.get_all_active_users()
        total_users = len(users)

        broadcast = Broadcast(
            admin_id=admin_id,
            message_type=message_type,
            content=content,
            total_users=total_users,
            success_count=0,
            failed_count=0,
        )
        self.session.add(broadcast)
        await self.session.commit()
        await self.session.refresh(broadcast)

        success = 0
        failed = 0

        for user in users:
            try:
                await self.bot.copy_message(
                    chat_id=user.telegram_id,
                    from_chat_id=source_chat_id,
                    message_id=source_message_id,
                )
                success += 1
            except TelegramForbiddenError:
                # User blocked bot
                failed += 1
                user.is_active = False
            except TelegramRetryAfter as e:
                # Rate limit hit, wait and retry once
                await asyncio.sleep(e.retry_after)
                try:
                    await self.bot.copy_message(
                        chat_id=user.telegram_id,
                        from_chat_id=source_chat_id,
                        message_id=source_message_id,
                    )
                    success += 1
                except Exception:
                    failed += 1
            except Exception as e:
                logger.warning(f"Failed to send broadcast to {user.telegram_id}: {e}")
                failed += 1

            # Rate limit protection (approx 25 messages per second)
            await asyncio.sleep(0.04)

        broadcast.success_count = success
        broadcast.failed_count = failed
        await self.session.commit()
        await self.session.refresh(broadcast)
        return broadcast
