import logging
from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from sqlalchemy.ext.asyncio import AsyncSession
from bot.constants import STATUS_BADGES, STATUS_LABELS
from bot.database.models import Appeal
from bot.keyboards.inline import get_admin_appeal_keyboard
from bot.services.user_service import UserService
from bot.utils.formatters import format_admin_notification

logger = logging.getLogger(__name__)


async def notify_admins_new_appeal(
    bot: Bot,
    session: AsyncSession,
    appeal: Appeal,
    preview_text: str,
    attachments_count: int,
) -> None:
    user_service = UserService(session)
    admin_ids = await user_service.get_all_admin_ids()
    text = format_admin_notification(appeal, preview_text, attachments_count)
    keyboard = get_admin_appeal_keyboard(appeal.id, appeal.status)

    for aid in admin_ids:
        try:
            await bot.send_message(
                chat_id=aid,
                text=text,
                reply_markup=keyboard,
                parse_mode="HTML",
            )
        except Exception as e:
            logger.warning(f"Could not notify admin {aid} of new appeal: {e}")


async def notify_admins_followup(
    bot: Bot,
    session: AsyncSession,
    appeal: Appeal,
    message_text: str,
    attachments_count: int,
) -> None:
    user_service = UserService(session)
    admin_ids = await user_service.get_all_admin_ids()

    u = appeal.user
    full_name = f"{u.first_name or ''} {u.last_name or ''}".strip() or "Noma'lum"
    att_note = f"\n📎 <i>Biriktirilgan fayllar: {attachments_count} ta</i>" if attachments_count else ""

    text = (
        f"💬 <b>MUROJAATGA QO‘SHIMCHA XABAR</b>\n\n"
        f"🆔 <b>Murojaat:</b> <b>{appeal.public_id}</b>\n"
        f"👤 <b>Talaba:</b> {full_name}\n"
        f"🆔 <b>Telegram ID:</b> <code>{u.telegram_id}</code>\n\n"
        f"📝 <b>Xabar:</b>\n{message_text}{att_note}"
    )
    keyboard = get_admin_appeal_keyboard(appeal.id, appeal.status)

    for aid in admin_ids:
        try:
            await bot.send_message(
                chat_id=aid,
                text=text,
                reply_markup=keyboard,
                parse_mode="HTML",
            )
        except Exception as e:
            logger.warning(f"Could not notify admin {aid} of followup: {e}")


async def notify_user_status_changed(
    bot: Bot, appeal: Appeal, new_status: str
) -> None:
    badge = STATUS_BADGES.get(new_status, "📌")
    label = STATUS_LABELS.get(new_status, new_status)
    text = (
        f"🔄 <b>Murojaat holati yangilandi!</b>\n\n"
        f"Murojaat raqami: <b>{appeal.public_id}</b>\n"
        f"Yangi holat: {badge} <b>{label}</b>\n\n"
        f"Murojaatlarim bo‘limi orqali batafsil ma’lumot olishingiz mumkin."
    )
    try:
        await bot.send_message(
            chat_id=appeal.user.telegram_id,
            text=text,
            parse_mode="HTML",
        )
    except Exception as e:
        logger.warning(f"Could not notify user {appeal.user.telegram_id} of status change: {e}")
