import logging
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession
from bot.keyboards.default import get_admin_main_menu, get_cancel_keyboard
from bot.keyboards.inline import get_broadcast_confirm_keyboard
from bot.services.broadcast_service import BroadcastService
from bot.states.states import BroadcastStates

logger = logging.getLogger(__name__)
router = Router()


@router.message(F.text == "📢 Broadcast")
async def start_broadcast(message: Message, state: FSMContext, is_admin: bool):
    if not is_admin:
        return

    await state.set_state(BroadcastStates.WAITING_FOR_MESSAGE)
    await message.answer(
        "📢 <b>Barcha foydalanuvchilarga yuboriladigan xabarni yuboring:</b>\n\n"
        "Matn, rasm, video yoki hujjat yuborishingiz mumkin.",
        reply_markup=get_cancel_keyboard(),
        parse_mode="HTML",
    )


@router.message(BroadcastStates.WAITING_FOR_MESSAGE)
async def preview_broadcast(message: Message, state: FSMContext, is_admin: bool):
    if not is_admin:
        return

    content_preview = message.text or message.caption or "(Media xabar)"
    msg_type = "text"
    if message.photo:
        msg_type = "photo"
    elif message.video:
        msg_type = "video"
    elif message.document:
        msg_type = "document"

    await state.update_data(
        source_chat_id=message.chat.id,
        source_message_id=message.message_id,
        message_type=msg_type,
        content=content_preview,
    )
    await state.set_state(BroadcastStates.CONFIRMING)

    await message.answer(
        "📢 <b>Broadcast xabarni tasdiqlash:</b>\n\n"
        "Xabar yuqorida ko‘rsatilganidek barcha faol foydalanuvchilarga yuboriladi.\n\n"
        "<b>Broadcastni boshlashni tasdiqlaysizmi?</b>",
        reply_markup=get_broadcast_confirm_keyboard(),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "bc_cancel")
async def cancel_broadcast(callback: CallbackQuery, state: FSMContext, is_admin: bool):
    if not is_admin:
        return

    await state.clear()
    await callback.message.edit_text("❌ Broadcast bekor qilindi.")
    await callback.message.answer("Admin paneli:", reply_markup=get_admin_main_menu())
    await callback.answer()


@router.callback_query(F.data == "bc_confirm")
async def execute_broadcast_handler(
    callback: CallbackQuery, state: FSMContext, session: AsyncSession, is_admin: bool, bot
):
    if not is_admin:
        return

    data = await state.get_data()
    source_chat_id = data.get("source_chat_id")
    source_message_id = data.get("source_message_id")
    message_type = data.get("message_type", "text")
    content = data.get("content")

    if not source_chat_id or not source_message_id:
        await callback.answer("Xabar topilmadi, qaytadan urinib ko‘ring.", show_alert=True)
        await state.clear()
        return

    await callback.message.edit_text(
        "⏳ <b>Broadcast xabarlari yuborilmoqda...</b>\nIltimos, kuting.",
        parse_mode="HTML",
    )
    await callback.answer()

    broadcast_service = BroadcastService(session=session, bot=bot)
    record = await broadcast_service.execute_broadcast(
        admin_id=callback.from_user.id,
        source_chat_id=source_chat_id,
        source_message_id=source_message_id,
        message_type=message_type,
        content=content,
    )

    await state.clear()
    summary_text = (
        "📢 <b>Broadcast yakunlandi!</b>\n\n"
        f"👥 <b>Jami foydalanuvchilar:</b> {record.total_users}\n"
        f"✅ <b>Muvaffaqiyatli yetkazildi:</b> {record.success_count}\n"
        f"❌ <b>Yetkazilmadi (bloklangan/xato):</b> {record.failed_count}"
    )
    await callback.message.edit_text(summary_text, parse_mode="HTML")
    await callback.message.answer("Admin paneli:", reply_markup=get_admin_main_menu())
