from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy import desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from bot.constants import AppealStatus
from bot.database.models import Appeal, Attachment, Message, User


class AppealService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def _generate_public_id(self) -> str:
        stmt = select(func.max(Appeal.id))
        result = await self.session.execute(stmt)
        max_id = result.scalar() or 0
        next_id = max_id + 1
        return f"#{next_id:06d}"

    async def create_appeal(
        self,
        user_id: int,
        messages_draft: List[Dict[str, Any]],
        subject: Optional[str] = None,
    ) -> Appeal:
        public_id = await self._generate_public_id()
        appeal = Appeal(
            public_id=public_id,
            user_id=user_id,
            status=AppealStatus.NEW.value,
            subject=subject,
        )
        self.session.add(appeal)
        await self.session.flush()

        for msg_item in messages_draft:
            db_msg = Message(
                appeal_id=appeal.id,
                sender_type="USER",
                sender_id=msg_item.get("sender_id", 0),
                message_type=msg_item.get("message_type", "text"),
                text=msg_item.get("text"),
                telegram_message_id=msg_item.get("telegram_message_id"),
            )
            self.session.add(db_msg)
            await self.session.flush()

            attachments = msg_item.get("attachments", [])
            for att in attachments:
                db_att = Attachment(
                    message_id=db_msg.id,
                    telegram_file_id=att["telegram_file_id"],
                    file_type=att["file_type"],
                    file_name=att.get("file_name"),
                    mime_type=att.get("mime_type"),
                    file_size=att.get("file_size"),
                )
                self.session.add(db_att)

        await self.session.commit()
        return await self.get_appeal_by_id(appeal.id)  # type: ignore

    async def get_appeal_by_id(self, appeal_id: int) -> Optional[Appeal]:
        stmt = (
            select(Appeal)
            .where(Appeal.id == appeal_id)
            .options(
                selectinload(Appeal.user),
                selectinload(Appeal.messages).selectinload(Message.attachments),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_appeal_by_public_id(self, public_id: str) -> Optional[Appeal]:
        clean_id = public_id.strip()
        if not clean_id.startswith("#"):
            clean_id = f"#{clean_id}"
        stmt = (
            select(Appeal)
            .where(Appeal.public_id == clean_id)
            .options(
                selectinload(Appeal.user),
                selectinload(Appeal.messages).selectinload(Message.attachments),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_user_appeals(self, user_id: int, limit: int = 50, offset: int = 0) -> List[Appeal]:
        stmt = (
            select(Appeal)
            .where(Appeal.user_id == user_id)
            .order_by(desc(Appeal.created_at))
            .limit(limit)
            .offset(offset)
            .options(
                selectinload(Appeal.messages).selectinload(Message.attachments),
            )
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_new_appeals(self, limit: int = 20, offset: int = 0) -> List[Appeal]:
        stmt = (
            select(Appeal)
            .where(Appeal.status == AppealStatus.NEW.value)
            .order_by(desc(Appeal.created_at))
            .limit(limit)
            .offset(offset)
            .options(
                selectinload(Appeal.user),
                selectinload(Appeal.messages).selectinload(Message.attachments),
            )
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_all_appeals(
        self, limit: int = 20, offset: int = 0, status: Optional[str] = None
    ) -> List[Appeal]:
        stmt = select(Appeal).order_by(desc(Appeal.created_at)).limit(limit).offset(offset)
        if status:
            stmt = stmt.where(Appeal.status == status)
        stmt = stmt.options(
            selectinload(Appeal.user),
            selectinload(Appeal.messages).selectinload(Message.attachments),
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count_all_appeals(self, status: Optional[str] = None) -> int:
        stmt = select(func.count(Appeal.id))
        if status:
            stmt = stmt.where(Appeal.status == status)
        result = await self.session.execute(stmt)
        return result.scalar() or 0

    async def search_appeals(self, query: str, limit: int = 20) -> List[Appeal]:
        query = query.strip()
        search_terms = []

        if query.startswith("#") or query.isdigit():
            norm_id = query if query.startswith("#") else f"#{int(query):06d}"
            search_terms.append(Appeal.public_id == norm_id)

        # Telegram ID check
        if query.isdigit():
            search_terms.append(User.telegram_id == int(query))

        # Username / Name match
        search_terms.append(User.username.ilike(f"%{query}%"))
        search_terms.append(User.first_name.ilike(f"%{query}%"))
        search_terms.append(User.last_name.ilike(f"%{query}%"))

        stmt = (
            select(Appeal)
            .join(User, Appeal.user_id == User.id)
            .where(or_(*search_terms))
            .order_by(desc(Appeal.created_at))
            .limit(limit)
            .options(
                selectinload(Appeal.user),
                selectinload(Appeal.messages).selectinload(Message.attachments),
            )
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def update_status(self, appeal_id: int, new_status: str) -> Optional[Appeal]:
        appeal = await self.get_appeal_by_id(appeal_id)
        if not appeal:
            return None

        appeal.status = new_status
        if new_status in (AppealStatus.RESOLVED.value, AppealStatus.CLOSED.value):
            appeal.closed_at = datetime.now(timezone.utc)
        else:
            appeal.closed_at = None

        await self.session.commit()
        await self.session.refresh(appeal)
        return appeal

    async def add_message(
        self,
        appeal_id: int,
        sender_type: str,
        sender_id: int,
        text: Optional[str] = None,
        message_type: str = "text",
        telegram_message_id: Optional[int] = None,
        attachments: Optional[List[Dict[str, Any]]] = None,
    ) -> Message:
        msg = Message(
            appeal_id=appeal_id,
            sender_type=sender_type,
            sender_id=sender_id,
            message_type=message_type,
            text=text,
            telegram_message_id=telegram_message_id,
        )
        self.session.add(msg)
        await self.session.flush()

        if attachments:
            for att in attachments:
                db_att = Attachment(
                    message_id=msg.id,
                    telegram_file_id=att["telegram_file_id"],
                    file_type=att["file_type"],
                    file_name=att.get("file_name"),
                    mime_type=att.get("mime_type"),
                    file_size=att.get("file_size"),
                )
                self.session.add(db_att)

        await self.session.commit()
        return msg

    async def get_statistics(self) -> Dict[str, int]:
        total_stmt = select(func.count(Appeal.id))
        total = (await self.session.execute(total_stmt)).scalar() or 0

        status_counts = {}
        for st in AppealStatus:
            count_stmt = select(func.count(Appeal.id)).where(Appeal.status == st.value)
            count = (await self.session.execute(count_stmt)).scalar() or 0
            status_counts[st.value] = count

        return {
            "total": total,
            "new": status_counts.get(AppealStatus.NEW.value, 0),
            "in_progress": status_counts.get(AppealStatus.IN_PROGRESS.value, 0),
            "waiting": status_counts.get(AppealStatus.WAITING.value, 0),
            "resolved": status_counts.get(AppealStatus.RESOLVED.value, 0),
            "closed": status_counts.get(AppealStatus.CLOSED.value, 0),
        }
