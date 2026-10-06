import logging
from typing import Any, Dict, List
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from sqlalchemy.ext.asyncio import AsyncSession
from bot.config import settings
from bot.constants import STATUS_BADGES, STATUS_LABELS, AppealStatus
from bot.database.models import User
from bot.keyboards.default import (
    get_cancel_keyboard,
    get_main_menu,
)
from bot.keyboards.inline import (
    get_appeals_list_keyboard,
    get_user_appeal_keyboard,
)
from bot.services.appeal_service import AppealService
from bot.states.states import AppealStates
from bot.utils.formatters import format_appeal_detail
from bot.utils.notifier import notify_admins_followup, notify_admins_new_appeal

logger = logging.getLogger(__name__)
router = Router()


def extract_message_data(message: Message) -> Dict[str, Any]:
    text = message.caption or message.text or ""
    msg_type = "text"
    attachments: List[Dict[str, Any]] = []

    if message.photo:
        msg_type = "photo"
        photo = message.photo[-1]
        attachments.append({
            "telegram_file_id": photo.file_id,
            "file_type": "photo",
            "file_name": "photo.jpg",
            "mime_type": "image/jpeg",
            "file_size": photo.file_size,
        })
    elif message.document:
        msg_type = "document"
        doc = message.document
        attachments.append({
            "telegram_file_id": doc.file_id,
            "file_type": "document",
            "file_name": doc.file_name,
            "mime_type": doc.mime_type,
            "file_size": doc.file_size,
        })
    elif message.video:
        msg_type = "video"
        vid = message.video
        attachments.append({
            "telegram_file_id": vid.file_id,
            "file_type": "video",
            "file_name": vid.file_name or "video.mp4",
            "mime_type": vid.mime_type or "video/mp4",
            "file_size": vid.file_size,
        })
    elif message.voice:
        msg_type = "voice"
        voice = message.voice
        attachments.append({
            "telegram_file_id": voice.file_id,
            "file_type": "voice",
            "file_name": "voice.ogg",
            "mime_type": voice.mime_type or "audio/ogg",
            "file_size": voice.file_size,
        })
    elif message.audio:
        msg_type = "audio"
        aud = message.audio
        attachments.append({
            "telegram_file_id": aud.file_id,
            "file_type": "audio",
            "file_name": aud.file_name or "audio.mp3",
            "mime_type": aud.mime_type or "audio/mpeg",
            "file_size": aud.file_size,
        })

    return {
        "text": text,
        "message_type": msg_type,
        "telegram_message_id": message.message_id,
        "sender_id": message.from_user.id,
        "attachments": attachments,
    }


@router.message(F.text == "📩 Murojaat yuborish")
async def start_appeal(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(AppealStates.WAITING_FOR_CONTENT)

    text = (
        "✍️ <b>Murojaatingizni yuboring:</b>\n\n"
        "Matn, rasm, video, audio yoki hujjat yuborishingiz mumkin.\n\n"
        "<i>Xabaringizni yuborishingiz bilan u qabul qilinadi va mas’ullarga yetkaziladi.</i>"
    )
    await message.answer(text, reply_markup=get_cancel_keyboard(), parse_mode="HTML")


@router.message(AppealStates.WAITING_FOR_CONTENT)
async def process_appeal_submission(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    user: User,
    is_admin: bool,
    bot,
):
    # Check file size limit
    file_size = 0
    if message.document:
        file_size = message.document.file_size or 0
    elif message.video:
        file_size = message.video.file_size or 0
    elif message.audio:
        file_size = message.audio.file_size or 0

    if file_size > settings.MAX_FILE_SIZE:
        await message.answer(
            "⚠️ Fayl hajmi 50 MB dan oshmasligi kerak. Iltimos, kichikroq hajmda yuboring.",
            reply_markup=get_cancel_keyboard(),
        )
        return

    item = extract_message_data(message)
    if not item["text"] and not item["attachments"]:
        await message.answer("⚠️ Iltimos, matn yoki fayl yuboring.", reply_markup=get_cancel_keyboard())
        return

    # Create appeal immediately
    appeal_service = AppealService(session)
    appeal = await appeal_service.create_appeal(
        user_id=user.id,
        messages_draft=[item],
    )
    await state.clear()

    preview_text = item["text"] or "(Biriktirilgan fayl)"
    if len(preview_text) > 200:
        preview_text = preview_text[:197] + "..."

    att_count = len(item["attachments"])

    # Confirmation with inline actions to attach more files or view appeals
    confirm_text = (
        "✅ <b>Murojaatingiz muvaffaqiyatli qabul qilindi!</b>\n\n"
        f"Murojaat raqami: <b>{appeal.public_id}</b>\n\n"
        "Yoshlar bo‘limi mas’ullari murojaatingizni ko‘rib chiqadi. Javob ushbu bot orqali yuboriladi."
    )
    
    inline_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="➕ Yana fayl/xabar biriktirish",
                    callback_data=f"usr_followup:{appeal.id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text="📋 Murojaatlarim",
                    callback_data="usr_my_appeals",
                )
            ]
        ]
    )

    await message.answer(
        confirm_text,
        reply_markup=get_main_menu(is_admin=is_admin),
        parse_mode="HTML",
    )
    await message.answer(
        "<i>Qo‘shimcha ma’lumot qo‘shish yoki holatni kuzatish:</i>",
        reply_markup=inline_kb,
        parse_mode="HTML",
    )

    # Notify administrators immediately
    await notify_admins_new_appeal(
        bot=bot,
        session=session,
        appeal=appeal,
        preview_text=preview_text,
        attachments_count=att_count,
    )


@router.message(F.text == "📋 Murojaatlarim")
async def show_my_appeals(message: Message, session: AsyncSession, user: User):
    appeal_service = AppealService(session)
    appeals = await appeal_service.get_user_appeals(user_id=user.id)

    if not appeals:
        await message.answer(
            "📋 <b>Sizda hali murojaatlar mavjud emas.</b>\n\n"
            "Murojaat yuborish uchun <b>'📩 Murojaat yuborish'</b> tugmasini bosing.",
            parse_mode="HTML",
        )
        return

    keyboard = get_appeals_list_keyboard(
        appeals=appeals,
        callback_prefix="usr_appeal",
        page=1,
        total_pages=1,
    )
    await message.answer(
        "📋 <b>Sizning murojaatlaringiz:</b>\nBatafsil ko‘rish uchun murojaatni tanlang:",
        reply_markup=keyboard,
        parse_mode="HTML",
    )


@router.callback_query(F.data == "usr_my_appeals")
async def cb_user_my_appeals(callback: CallbackQuery, session: AsyncSession, user: User):
    appeal_service = AppealService(session)
    appeals = await appeal_service.get_user_appeals(user_id=user.id)

    if not appeals:
        await callback.message.edit_text(
            "📋 Sizda hali murojaatlar mavjud emas.",
        )
        await callback.answer()
        return

    keyboard = get_appeals_list_keyboard(
        appeals=appeals,
        callback_prefix="usr_appeal",
        page=1,
        total_pages=1,
    )
    await callback.message.edit_text(
        "📋 <b>Sizning murojaatlaringiz:</b>\nBatafsil ko‘rish uchun murojaatni tanlang:",
        reply_markup=keyboard,
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("usr_appeal:"))
async def cb_user_appeal_detail(callback: CallbackQuery, session: AsyncSession, user: User):
    appeal_id = int(callback.data.split(":")[1])
    appeal_service = AppealService(session)
    appeal = await appeal_service.get_appeal_by_id(appeal_id)

    if not appeal or appeal.user_id != user.id:
        await callback.answer("Murojaat topilmadi!", show_alert=True)
        return

    detail_text = format_appeal_detail(appeal, for_admin=False)
    is_closed = appeal.status in [AppealStatus.CLOSED.value, AppealStatus.RESOLVED.value]
    keyboard = get_user_appeal_keyboard(appeal.id, is_closed=is_closed)

    await callback.message.edit_text(detail_text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("usr_files:"))
async def cb_user_appeal_files(callback: CallbackQuery, session: AsyncSession, user: User, bot):
    appeal_id = int(callback.data.split(":")[1])
    appeal_service = AppealService(session)
    appeal = await appeal_service.get_appeal_by_id(appeal_id)

    if not appeal or appeal.user_id != user.id:
        await callback.answer("Murojaat topilmadi!", show_alert=True)
        return

    attachments = []
    for msg in appeal.messages:
        attachments.extend(msg.attachments)

    if not attachments:
        await callback.answer("Ushbu murojaatga fayllar biriktirilmagan.", show_alert=True)
        return

    await callback.answer("Fayllar yuborilmoqda...")
    for att in attachments:
        try:
            if att.file_type == "photo":
                await bot.send_photo(
                    chat_id=callback.from_user.id,
                    photo=att.telegram_file_id,
                    caption=f"📎 Murojaat: {appeal.public_id}",
                )
            elif att.file_type == "video":
                await bot.send_video(
                    chat_id=callback.from_user.id,
                    video=att.telegram_file_id,
                    caption=f"📎 Murojaat: {appeal.public_id}",
                )
            elif att.file_type == "voice":
                await bot.send_voice(
                    chat_id=callback.from_user.id,
                    voice=att.telegram_file_id,
                    caption=f"📎 Murojaat: {appeal.public_id}",
                )
            elif att.file_type == "audio":
                await bot.send_audio(
                    chat_id=callback.from_user.id,
                    audio=att.telegram_file_id,
                    caption=f"📎 Murojaat: {appeal.public_id}",
                )
            else:
                await bot.send_document(
                    chat_id=callback.from_user.id,
                    document=att.telegram_file_id,
                    caption=f"📎 Murojaat: {appeal.public_id}",
                )
        except Exception as e:
            logger.warning(f"Failed to send attachment to user: {e}")


@router.callback_query(F.data.startswith("usr_followup:"))
async def cb_user_appeal_followup(callback: CallbackQuery, state: FSMContext, session: AsyncSession, user: User):
    appeal_id = int(callback.data.split(":")[1])
    appeal_service = AppealService(session)
    appeal = await appeal_service.get_appeal_by_id(appeal_id)

    if not appeal or appeal.user_id != user.id:
        await callback.answer("Murojaat topilmadi!", show_alert=True)
        return

    if appeal.status in [AppealStatus.CLOSED.value, AppealStatus.RESOLVED.value]:
        await callback.answer("Ushbu murojaat yopilgan, qo‘shimcha xabar yuborib bo‘lmaydi.", show_alert=True)
        return

    await state.set_state(AppealStates.WAITING_FOLLOWUP)
    await state.update_data(appeal_id=appeal.id)
    await callback.message.answer(
        f"✍️ <b>{appeal.public_id} murojaatiga qo‘shimcha ma’lumotingiz yoki faylni yuboring:</b>",
        reply_markup=get_cancel_keyboard(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(AppealStates.WAITING_FOLLOWUP)
async def handle_user_followup_message(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    user: User,
    is_admin: bool,
    bot,
):
    data = await state.get_data()
    appeal_id = data.get("appeal_id")
    appeal_service = AppealService(session)
    appeal = await appeal_service.get_appeal_by_id(appeal_id)

    if not appeal or appeal.user_id != user.id:
        await state.clear()
        await message.answer("Murojaat topilmadi.", reply_markup=get_main_menu(is_admin=is_admin))
        return

    msg_data = extract_message_data(message)
    await appeal_service.add_message(
        appeal_id=appeal.id,
        sender_type="USER",
        sender_id=message.from_user.id,
        text=msg_data["text"],
        message_type=msg_data["message_type"],
        telegram_message_id=msg_data["telegram_message_id"],
        attachments=msg_data["attachments"],
    )

    await state.clear()
    await message.answer(
        f"✅ <b>{appeal.public_id}</b> murojaatiga qo‘shimcha ma’lumot biriktirildi va mas’ullarga yuborildi.",
        reply_markup=get_main_menu(is_admin=is_admin),
        parse_mode="HTML",
    )

    # Notify admins
    await notify_admins_followup(
        bot=bot,
        session=session,
        appeal=appeal,
        message_text=msg_data["text"] or "(Fayl yuborildi)",
        attachments_count=len(msg_data["attachments"]),
    )
