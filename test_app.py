import asyncio
import os
import sys

# Test environment with SQLite in memory
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["BOT_TOKEN"] = "8830551287:AAFVlYoFLTLlbyUcuOrFWU3Nq8D5SCTfnak"
os.environ["ADMIN_IDS"] = "1202082857,1156019398"
os.environ["SUPERADMIN_IDS"] = "1202082857"
os.environ["USE_WEBHOOK"] = "False"

from bot.config import settings
from bot.database.session import init_db, async_session_maker, engine
from bot.services.user_service import UserService
from bot.services.appeal_service import AppealService
from bot.constants import AppealStatus
from bot.handlers import get_main_router


async def test_full_flow():
    print("1. Initializing in-memory DB...")
    await init_db()
    print("   Database initialized successfully!")

    print("2. Testing UserService & Superadmin Management...")
    async with async_session_maker() as session:
        user_service = UserService(session)
        user = await user_service.get_or_create_user(
            telegram_id=999888,
            username="talaba_test",
            first_name="Mansurbek",
            last_name="Testov",
        )
        assert user.id is not None
        assert user.telegram_id == 999888
        print(f"   Created user: {user.first_name} (ID: {user.id})")

        # Check superadmin and admin detection
        is_sa = user_service.is_superadmin(1202082857)
        is_adm1 = await user_service.is_admin(1202082857)
        is_adm2 = await user_service.is_admin(1156019398)
        is_adm_normal = await user_service.is_admin(999888)
        assert is_sa is True
        assert is_adm1 is True
        assert is_adm2 is True
        assert is_adm_normal is False
        print(f"   Superadmin (1202082857): {is_sa}")
        print(f"   Youth Specialist Admin (1156019398): {is_adm2}")

        # Dynamic add admin test
        new_adm = await user_service.add_admin(telegram_id=555666, name="Yordamchi Admin")
        assert new_adm.is_active is True
        assert (await user_service.is_admin(555666)) is True
        print(f"   Dynamic Admin Added: {new_adm.name} ({new_adm.telegram_id})")

        # Dynamic remove admin test
        removed = await user_service.remove_admin(555666)
        assert removed is True
        assert (await user_service.is_admin(555666)) is False
        print(f"   Dynamic Admin Removed: {removed}")

    print("3. Testing AppealService...")
    async with async_session_maker() as session:
        appeal_service = AppealService(session)
        draft = [
            {
                "text": "Talabalar turar joyi bo‘yicha ariza",
                "message_type": "text",
                "telegram_message_id": 101,
                "sender_id": 999888,
                "attachments": [
                    {
                        "telegram_file_id": "file_id_photo_123",
                        "file_type": "photo",
                        "file_name": "photo.jpg",
                        "mime_type": "image/jpeg",
                        "file_size": 102400,
                    }
                ],
            }
        ]

        appeal = await appeal_service.create_appeal(
            user_id=user.id,
            messages_draft=draft,
            subject="TTJ arizasi",
        )
        assert appeal.public_id == "#000001" or appeal.public_id.startswith("#")
        assert appeal.status == AppealStatus.NEW.value
        assert len(appeal.messages) == 1
        assert len(appeal.messages[0].attachments) == 1
        print(f"   Created appeal: {appeal.public_id} with status: {appeal.status}")

        # Test status update
        updated = await appeal_service.update_status(appeal.id, AppealStatus.IN_PROGRESS.value)
        assert updated.status == AppealStatus.IN_PROGRESS.value
        print(f"   Updated appeal status to: {updated.status}")

        # Test adding direct admin reply
        reply_msg = await appeal_service.add_message(
            appeal_id=appeal.id,
            sender_type="ADMIN",
            sender_id=1156019398,
            text="Arizangiz qabul qilindi va ko‘rib chiqilmoqda.",
            message_type="text",
        )
        assert reply_msg.sender_type == "ADMIN"
        print(f"   Added admin reply to appeal: {reply_msg.text}")

        # Test statistics
        stats = await appeal_service.get_statistics()
        print(f"   Statistics: {stats}")
        assert stats["total"] == 1
        assert stats["in_progress"] == 1

        # Test search
        search_res = await appeal_service.search_appeals(appeal.public_id)
        assert len(search_res) >= 1
        print(f"   Search by {appeal.public_id} returned {len(search_res)} results.")

    print("4. Testing Router & Dispatcher loading...")
    router = get_main_router()
    assert router is not None
    print(f"   Router loaded with {len(router.sub_routers)} sub-routers.")

    await engine.dispose()
    print("\nALL VERIFICATION TESTS PASSED SUCCESSFULLY! [SUCCESS]")


if __name__ == "__main__":
    asyncio.run(test_full_flow())
