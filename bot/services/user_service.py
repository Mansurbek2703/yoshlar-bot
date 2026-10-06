from typing import Any, Dict, List, Optional
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from bot.config import settings
from bot.database.models import Admin, User


class UserService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_or_create_user(
        self,
        telegram_id: int,
        username: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
    ) -> User:
        stmt = select(User).where(User.telegram_id == telegram_id)
        result = await self.session.execute(stmt)
        user = result.scalar_one_or_none()

        if user:
            changed = False
            if user.username != username:
                user.username = username
                changed = True
            if user.first_name != first_name:
                user.first_name = first_name
                changed = True
            if user.last_name != last_name:
                user.last_name = last_name
                changed = True
            if not user.is_active:
                user.is_active = True
                changed = True
            if changed:
                await self.session.commit()
                await self.session.refresh(user)
            return user

        new_user = User(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
            is_active=True,
        )
        self.session.add(new_user)
        await self.session.commit()
        await self.session.refresh(new_user)
        return new_user

    async def get_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        stmt = select(User).where(User.telegram_id == telegram_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all_active_users(self) -> List[User]:
        stmt = select(User).where(User.is_active.is_(True))
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_total_users_count(self) -> int:
        stmt = select(func.count(User.id)).where(User.is_active.is_(True))
        result = await self.session.execute(stmt)
        return result.scalar() or 0

    def is_superadmin(self, telegram_id: int) -> bool:
        return telegram_id in settings.superadmin_ids

    async def is_admin(self, telegram_id: int) -> bool:
        if self.is_superadmin(telegram_id):
            return True
        if telegram_id in settings.admin_ids:
            return True
        stmt = select(Admin).where(Admin.telegram_id == telegram_id, Admin.is_active.is_(True))
        result = await self.session.execute(stmt)
        admin = result.scalar_one_or_none()
        return admin is not None

    async def get_all_admin_ids(self) -> List[int]:
        ids = set(settings.admin_ids)
        ids.update(settings.superadmin_ids)
        stmt = select(Admin.telegram_id).where(Admin.is_active.is_(True))
        result = await self.session.execute(stmt)
        db_admin_ids = result.scalars().all()
        ids.update(db_admin_ids)
        return list(ids)

    async def add_admin(self, telegram_id: int, name: str) -> Admin:
        stmt = select(Admin).where(Admin.telegram_id == telegram_id)
        result = await self.session.execute(stmt)
        admin = result.scalar_one_or_none()

        if admin:
            admin.is_active = True
            admin.name = name
            await self.session.commit()
            await self.session.refresh(admin)
            return admin

        new_admin = Admin(
            telegram_id=telegram_id,
            name=name,
            is_active=True,
        )
        self.session.add(new_admin)
        await self.session.commit()
        await self.session.refresh(new_admin)
        return new_admin

    async def remove_admin(self, telegram_id: int) -> bool:
        # Cannot remove superadmins
        if self.is_superadmin(telegram_id):
            return False

        stmt = select(Admin).where(Admin.telegram_id == telegram_id)
        result = await self.session.execute(stmt)
        admin = result.scalar_one_or_none()

        if admin:
            admin.is_active = False
            await self.session.commit()
            return True
        return False

    async def get_all_admins(self) -> List[Dict[str, Any]]:
        admin_ids = await self.get_all_admin_ids()
        admins = []

        for aid in admin_ids:
            stmt = select(Admin).where(Admin.telegram_id == aid)
            res = await self.session.execute(stmt)
            obj = res.scalar_one_or_none()

            is_super = self.is_superadmin(aid)
            name = obj.name if obj and obj.name else ("Superadmin" if is_super else "Administrator")
            
            # Check user table for additional name info if not present
            if not obj or not obj.name:
                u_stmt = select(User).where(User.telegram_id == aid)
                u_res = await self.session.execute(u_stmt)
                u = u_res.scalar_one_or_none()
                if u and (u.first_name or u.username):
                    name = f"{u.first_name or ''} {u.last_name or ''}".strip() or f"@{u.username}"

            is_env = (aid in settings.admin_ids) or is_super
            can_remove = not is_super and not (aid in settings.admin_ids)

            admins.append({
                "telegram_id": aid,
                "name": name,
                "is_superadmin": is_super,
                "is_env": is_env,
                "can_remove": can_remove,
                "is_active": True if not obj else obj.is_active,
            })

        # Sort: Superadmins first, then by name
        admins.sort(key=lambda a: (not a["is_superadmin"], a["name"]))
        return admins
