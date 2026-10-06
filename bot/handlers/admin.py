import logging
import math
from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession
from bot.constants import STATUS_BADGES, STATUS_LABELS, AppealStatus
from bot.keyboards.default import (
    get_admin_main_menu,
    get_cancel_keyboard,
    get_main_menu,
)
from bot.keyboards.inline import (
    get_admin_appeal_keyboard,
    get_admin_management_keyboard,
    get_appeals_list_keyboard,
    get_remove_admin_keyboard,
    get_status_change_keyboard,
)
from bot.services.appeal_service import AppealService
from bot.services.user_service import UserService
from bot.states.states import AdminManagementStates, AdminReplyStates, AdminSearchStates
from bot.utils.formatters import format_appeal_detail, format_statistics
from bot.utils.notifier import notify_user_status_changed

logger = logging.getLogger(__name__)
router = Router()

PAGE_SIZE = 10


@router.message(Command("admin"))
@router.message(F.text == "⚙️ Admin panel")
async def show_admin_panel(message: Message, is_admin: bool):
    if not is_admin:
        await message.answer("⛔ Sizda administrator huquqlari mavjud emas.")
        return

    await message.answer(
        "⚙️ <b>Yoshlar bo‘limi boshqaruv paneli</b>\n\nKerakli bo‘limni tanlang:",
        reply_markup=get_admin_main_menu(),
        parse_mode="HTML",
    )


@router.message(F.text == "📥 Yangi murojaatlar")
async def show_new_appeals(message: Message, session: AsyncSession, is_admin: bool):
    if not is_admin:
        return

    appeal_service = AppealService(session)
    appeals = await appeal_service.get_new_appeals(limit=20)

    if not appeals:
        await message.answer(
            "📥 <b>Hozircha yangi murojaatlar mavjud emas.</b>",
            reply_markup=get_admin_main_menu(),
            parse_mode="HTML",
        )
        return

    keyboard = get_appeals_list_keyboard(
        appeals=appeals,
        callback_prefix="adm_detail",
        page=1,
        total_pages=1,
        filter_type="new",
    )
    await message.answer(
        f"📥 <b>Yangi murojaatlar ({len(appeals)} ta):</b>\nBatafsil ko‘rish uchun tanlang:",
        reply_markup=keyboard,
        parse_mode="HTML",
    )


@router.message(F.text == "📋 Barcha murojaatlar")
async def show_all_appeals(message: Message, session: AsyncSession, is_admin: bool):
    if not is_admin:
        return

    appeal_service = AppealService(session)
    total = await appeal_service.count_all_appeals()
    total_pages = max(1, math.ceil(total / PAGE_SIZE))
    appeals = await appeal_service.get_all_appeals(limit=PAGE_SIZE, offset=0)

    if not appeals:
        await message.answer(
            "📋 <b>Bazada murojaatlar mavjud emas.</b>",
            reply_markup=get_admin_main_menu(),
            parse_mode="HTML",
        )
        return

    keyboard = get_appeals_list_keyboard(
        appeals=appeals,
        callback_prefix="adm_detail",
        page=1,
        total_pages=total_pages,
        filter_type="all",
    )
    await message.answer(
        f"📋 <b>Barcha murojaatlar (Jami: {total}):</b>\nSahifa 1/{total_pages}:",
        reply_markup=keyboard,
        parse_mode="HTML",
    )


@router.callback_query(F.data.startswith("page:"))
async def handle_pagination(callback: CallbackQuery, session: AsyncSession, is_admin: bool):
    if not is_admin:
        await callback.answer("Ruxsat berilmagan!", show_alert=True)
        return

    parts = callback.data.split(":")
    filter_type = parts[1]
    page = int(parts[2])

    appeal_service = AppealService(session)
    status_filter = AppealStatus.NEW.value if filter_type == "new" else None
    total = await appeal_service.count_all_appeals(status=status_filter)
    total_pages = max(1, math.ceil(total / PAGE_SIZE))
    offset = (page - 1) * PAGE_SIZE

    appeals = await appeal_service.get_all_appeals(
        limit=PAGE_SIZE, offset=offset, status=status_filter
    )

    keyboard = get_appeals_list_keyboard(
        appeals=appeals,
        callback_prefix="adm_detail",
        page=page,
        total_pages=total_pages,
        filter_type=filter_type,
    )
    await callback.message.edit_text(
        f"📋 <b>Murojaatlar ro‘yxati (Sahifa {page}/{total_pages}):</b>",
        reply_markup=keyboard,
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("adm_detail:"))
async def show_appeal_detail(callback: CallbackQuery, session: AsyncSession, is_admin: bool):
    if not is_admin:
        await callback.answer("Ruxsat berilmagan!", show_alert=True)
        return

    appeal_id = int(callback.data.split(":")[1])
    appeal_service = AppealService(session)
    appeal = await appeal_service.get_appeal_by_id(appeal_id)

    if not appeal:
        await callback.answer("Murojaat topilmadi!", show_alert=True)
        return

    text = format_appeal_detail(appeal, for_admin=True)
    keyboard = get_admin_appeal_keyboard(appeal.id, appeal.status)

    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("adm_status_menu:"))
async def show_status_menu(callback: CallbackQuery, session: AsyncSession, is_admin: bool):
    if not is_admin:
        await callback.answer("Ruxsat berilmagan!", show_alert=True)
        return

    appeal_id = int(callback.data.split(":")[1])
    appeal_service = AppealService(session)
    appeal = await appeal_service.get_appeal_by_id(appeal_id)

    if not appeal:
        await callback.answer("Murojaat topilmadi!", show_alert=True)
        return

    keyboard = get_status_change_keyboard(appeal.id, appeal.status)
    await callback.message.edit_text(
        f"🔄 <b>Murojaat {appeal.public_id} holatini tanlang:</b>",
        reply_markup=keyboard,
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("set_st:"))
async def update_appeal_status_handler(
    callback: CallbackQuery, session: AsyncSession, is_admin: bool, bot
):
    if not is_admin:
        await callback.answer("Ruxsat berilmagan!", show_alert=True)
        return

    parts = callback.data.split(":")
    appeal_id = int(parts[1])
    new_status = parts[2]

    appeal_service = AppealService(session)
    appeal = await appeal_service.update_status(appeal_id, new_status)

    if not appeal:
        await callback.answer("Murojaat topilmadi!", show_alert=True)
        return

    # Notify student
    await notify_user_status_changed(bot, appeal, new_status)

    badge = STATUS_BADGES.get(new_status, "📌")
    label = STATUS_LABELS.get(new_status, new_status)
    await callback.answer(f"Status o‘zgartirildi: {label}")

    text = format_appeal_detail(appeal, for_admin=True)
    keyboard = get_admin_appeal_keyboard(appeal.id, appeal.status)
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")


@router.callback_query(F.data.startswith("adm_files:"))
async def view_appeal_files(callback: CallbackQuery, session: AsyncSession, is_admin: bool, bot):
    if not is_admin:
        await callback.answer("Ruxsat berilmagan!", show_alert=True)
        return

    appeal_id = int(callback.data.split(":")[1])
    appeal_service = AppealService(session)
    appeal = await appeal_service.get_appeal_by_id(appeal_id)

    if not appeal:
        await callback.answer("Murojaat topilmadi!", show_alert=True)
        return

    attachments = []
    for msg in appeal.messages:
        attachments.extend(msg.attachments)

    if not attachments:
        await callback.answer("Ushbu murojaatga biriktirilgan fayllar yo‘q.", show_alert=True)
        return

    await callback.answer(f"{len(attachments)} ta fayl yuborilmoqda...")
    for att in attachments:
        try:
            caption = f"📎 Murojaat: {appeal.public_id} ({att.file_type})"
            if att.file_type == "photo":
                await bot.send_photo(chat_id=callback.from_user.id, photo=att.telegram_file_id, caption=caption)
            elif att.file_type == "video":
                await bot.send_video(chat_id=callback.from_user.id, video=att.telegram_file_id, caption=caption)
            elif att.file_type == "voice":
                await bot.send_voice(chat_id=callback.from_user.id, voice=att.telegram_file_id, caption=caption)
            elif att.file_type == "audio":
                await bot.send_audio(chat_id=callback.from_user.id, audio=att.telegram_file_id, caption=caption)
            else:
                await bot.send_document(chat_id=callback.from_user.id, document=att.telegram_file_id, caption=caption)
        except Exception as e:
            logger.warning(f"Error sending attachment to admin: {e}")


@router.callback_query(F.data.startswith("adm_reply:"))
async def start_admin_reply(callback: CallbackQuery, state: FSMContext, session: AsyncSession, is_admin: bool):
    if not is_admin:
        await callback.answer("Ruxsat berilmagan!", show_alert=True)
        return

    appeal_id = int(callback.data.split(":")[1])
    appeal_service = AppealService(session)
    appeal = await appeal_service.get_appeal_by_id(appeal_id)

    if not appeal:
        await callback.answer("Murojaat topilmadi!", show_alert=True)
        return

    await state.set_state(AdminReplyStates.WAITING_FOR_REPLY)
    await state.update_data(appeal_id=appeal.id)
    await callback.message.answer(
        f"💬 <b>{appeal.public_id} murojaatiga javobingizni yuboring:</b>\n\n"
        "Matn, rasm, video, ovozli xabar yoki hujjat yuborishingiz mumkin.",
        reply_markup=get_cancel_keyboard(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(AdminReplyStates.WAITING_FOR_REPLY)
async def send_admin_reply(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    is_admin: bool,
    bot,
):
    if not is_admin:
        return

    data = await state.get_data()
    appeal_id = data.get("appeal_id")
    appeal_service = AppealService(session)
    appeal = await appeal_service.get_appeal_by_id(appeal_id)

    if not appeal:
        await state.clear()
        await message.answer("Murojaat topilmadi.", reply_markup=get_admin_main_menu())
        return

    from bot.handlers.appeal import extract_message_data
    msg_data = extract_message_data(message)

    # Save admin reply to DB
    await appeal_service.add_message(
        appeal_id=appeal.id,
        sender_type="ADMIN",
        sender_id=message.from_user.id,
        text=msg_data["text"],
        message_type=msg_data["message_type"],
        telegram_message_id=msg_data["telegram_message_id"],
        attachments=msg_data["attachments"],
    )

    # If appeal was NEW, update to IN_PROGRESS automatically
    if appeal.status == AppealStatus.NEW.value:
        await appeal_service.update_status(appeal.id, AppealStatus.IN_PROGRESS.value)

    # Direct reply to student
    student_tg_id = appeal.user.telegram_id
    reply_header = (
        "📩 <b>Yoshlar bo‘limidan javob:</b>\n\n"
        f"{msg_data['text'] or '(Fayl biriktirilgan)'}\n\n"
        f"📌 <i>Murojaat raqami: {appeal.public_id}</i>"
    )

    try:
        if not msg_data["attachments"]:
            await bot.send_message(chat_id=student_tg_id, text=reply_header, parse_mode="HTML")
        else:
            first_sent = False
            for att in msg_data["attachments"]:
                caption = reply_header if not first_sent else None
                first_sent = True
                if att["file_type"] == "photo":
                    await bot.send_photo(chat_id=student_tg_id, photo=att["telegram_file_id"], caption=caption, parse_mode="HTML")
                elif att["file_type"] == "video":
                    await bot.send_video(chat_id=student_tg_id, video=att["telegram_file_id"], caption=caption, parse_mode="HTML")
                elif att["file_type"] == "voice":
                    await bot.send_voice(chat_id=student_tg_id, voice=att["telegram_file_id"], caption=caption, parse_mode="HTML")
                elif att["file_type"] == "audio":
                    await bot.send_audio(chat_id=student_tg_id, audio=att["telegram_file_id"], caption=caption, parse_mode="HTML")
                else:
                    await bot.send_document(chat_id=student_tg_id, document=att["telegram_file_id"], caption=caption, parse_mode="HTML")
    except Exception as e:
        logger.warning(f"Could not deliver admin reply to user {student_tg_id}: {e}")

    await state.clear()
    await message.answer(
        f"✅ <b>{appeal.public_id}</b> murojaatiga javob talabaga muvaffaqiyatli yuborildi.",
        reply_markup=get_admin_main_menu(),
        parse_mode="HTML",
    )


@router.message(F.text == "🔎 Murojaatni qidirish")
async def start_search(message: Message, state: FSMContext, is_admin: bool):
    if not is_admin:
        return

    await state.set_state(AdminSearchStates.WAITING_FOR_QUERY)
    await message.answer(
        "🔎 <b>Qidiruv uchun ma’lumot kiriting:</b>\n\n"
        "• Murojaat ID (masalan: <code>#000125</code> yoki <code>125</code>)\n"
        "• Talaba Telegram ID (masalan: <code>123456789</code>)\n"
        "• Talaba ismi yoki username",
        reply_markup=get_cancel_keyboard(),
        parse_mode="HTML",
    )


@router.message(AdminSearchStates.WAITING_FOR_QUERY)
async def process_search(message: Message, state: FSMContext, session: AsyncSession, is_admin: bool):
    if not is_admin:
        return

    query = message.text.strip()
    appeal_service = AppealService(session)
    results = await appeal_service.search_appeals(query=query)

    await state.clear()
    if not results:
        await message.answer(
            f"🔎 <b>'{query}'</b> bo‘yicha hech qanday murojaat topilmadi.",
            reply_markup=get_admin_main_menu(),
            parse_mode="HTML",
        )
        return

    keyboard = get_appeals_list_keyboard(
        appeals=results,
        callback_prefix="adm_detail",
        page=1,
        total_pages=1,
        filter_type="search",
    )
    await message.answer(
        f"🔎 <b>Qidiruv natijalari ({len(results)} ta topildi):</b>\nBatafsil ko‘rish uchun tanlang:",
        reply_markup=keyboard,
        parse_mode="HTML",
    )


@router.message(F.text == "📊 Statistika")
async def show_statistics(message: Message, session: AsyncSession, is_admin: bool):
    if not is_admin:
        return

    appeal_service = AppealService(session)
    user_service = UserService(session)

    stats = await appeal_service.get_statistics()
    total_users = await user_service.get_total_users_count()

    text = format_statistics(stats, total_users)
    await message.answer(text, reply_markup=get_admin_main_menu(), parse_mode="HTML")


@router.message(F.text == "👥 Adminlar")
async def show_admins_list(
    message: Message, session: AsyncSession, is_admin: bool, is_superadmin: bool
):
    if not is_admin:
        return

    user_service = UserService(session)
    admins = await user_service.get_all_admins()

    lines = ["👥 <b>Tizim administratorlari:</b>\n"]
    for adm in admins:
        badge = "👑 <b>Superadmin</b>" if adm["is_superadmin"] else "👔 <b>Admin</b>"
        lines.append(f"• {badge}: <b>{adm['name']}</b>\n   🆔 ID: <code>{adm['telegram_id']}</code>")

    if is_superadmin:
        lines.append("\n<i>Superadmin sifatida yangi admin qo‘shishingiz yoki o‘chirishingiz mumkin:</i>")

    keyboard = get_admin_management_keyboard(is_superadmin=is_superadmin)
    await message.answer("\n".join(lines), reply_markup=keyboard, parse_mode="HTML")


@router.callback_query(F.data == "adm_refresh_admins")
async def cb_refresh_admins(
    callback: CallbackQuery, session: AsyncSession, is_admin: bool, is_superadmin: bool
):
    if not is_admin:
        return

    user_service = UserService(session)
    admins = await user_service.get_all_admins()

    lines = ["👥 <b>Tizim administratorlari:</b>\n"]
    for adm in admins:
        badge = "👑 <b>Superadmin</b>" if adm["is_superadmin"] else "👔 <b>Admin</b>"
        lines.append(f"• {badge}: <b>{adm['name']}</b>\n   🆔 ID: <code>{adm['telegram_id']}</code>")

    if is_superadmin:
        lines.append("\n<i>Superadmin sifatida yangi admin qo‘shishingiz yoki o‘chirishingiz mumkin:</i>")

    keyboard = get_admin_management_keyboard(is_superadmin=is_superadmin)
    await callback.message.edit_text("\n".join(lines), reply_markup=keyboard, parse_mode="HTML")
    await callback.answer("Yangilandi.")


@router.callback_query(F.data == "adm_add_admin")
async def cb_add_admin_start(
    callback: CallbackQuery, state: FSMContext, is_superadmin: bool
):
    if not is_superadmin:
        await callback.answer("Faqat superadmin admin qo‘sha oladi!", show_alert=True)
        return

    await state.set_state(AdminManagementStates.WAITING_FOR_ADMIN_ID)
    await callback.message.answer(
        "➕ <b>Yangi admin qo‘shish:</b>\n\n"
        "Adminning Telegram ID raqamini kiriting (masalan: <code>1156019398</code>):",
        reply_markup=get_cancel_keyboard(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(AdminManagementStates.WAITING_FOR_ADMIN_ID)
async def process_new_admin_id(
    message: Message, state: FSMContext, is_superadmin: bool
):
    if not is_superadmin:
        return

    text = message.text.strip()
    if not text.isdigit():
        await message.answer("⚠️ Telegram ID faqat raqamlardan iborat bo‘lishi kerak. Qaytadan kiriting:")
        return

    admin_tg_id = int(text)
    await state.update_data(new_admin_id=admin_tg_id)
    await state.set_state(AdminManagementStates.WAITING_FOR_ADMIN_NAME)

    await message.answer(
        f"🆔 ID: <code>{admin_tg_id}</code>\n\n"
        "Endi adminning ismini yoki lavozimini kiriting (masalan: <i>Javohir - Yoshlar yetakchisi</i>):",
        reply_markup=get_cancel_keyboard(),
        parse_mode="HTML",
    )


@router.message(AdminManagementStates.WAITING_FOR_ADMIN_NAME)
async def process_new_admin_name(
    message: Message, state: FSMContext, session: AsyncSession, is_superadmin: bool
):
    if not is_superadmin:
        return

    data = await state.get_data()
    new_admin_id = data.get("new_admin_id")
    name = message.text.strip()

    user_service = UserService(session)
    await user_service.add_admin(telegram_id=new_admin_id, name=name)

    await state.clear()
    await message.answer(
        f"✅ <b>Yangi admin muvaffaqiyatli qo‘shildi!</b>\n\n"
        f"👤 Ism/Lavozim: <b>{name}</b>\n"
        f"🆔 Telegram ID: <code>{new_admin_id}</code>\n\n"
        "Ushbu foydalanuvchi endi botda admin paneldan to‘liq foydalanishi va murojaatlarga javob berishi mumkin.",
        reply_markup=get_admin_main_menu(),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "adm_del_admin_menu")
async def cb_del_admin_menu(
    callback: CallbackQuery, session: AsyncSession, is_superadmin: bool
):
    if not is_superadmin:
        await callback.answer("Faqat superadmin adminlarni o‘chira oladi!", show_alert=True)
        return

    user_service = UserService(session)
    admins = await user_service.get_all_admins()

    deletable = [a for a in admins if a.get("can_remove")]
    if not deletable:
        await callback.answer("O‘chirish mumkin bo‘lgan qo‘shimcha adminlar mavjud emas.", show_alert=True)
        return

    keyboard = get_remove_admin_keyboard(admins)
    await callback.message.edit_text(
        "🗑 <b>O‘chirish uchun adminni tanlang:</b>\n"
        "<i>(Asosiy .env dagi adminlar va superadminni o‘chirib bo‘lmaydi)</i>",
        reply_markup=keyboard,
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("adm_do_remove:"))
async def cb_do_remove_admin(
    callback: CallbackQuery, session: AsyncSession, is_superadmin: bool
):
    if not is_superadmin:
        await callback.answer("Faqat superadmin!", show_alert=True)
        return

    remove_id = int(callback.data.split(":")[1])
    user_service = UserService(session)
    success = await user_service.remove_admin(remove_id)

    if success:
        await callback.answer("Admin muvaffaqiyatli o‘chirildi!", show_alert=True)
    else:
        await callback.answer("Ushbu adminni o‘chirib bo‘lmaydi.", show_alert=True)

    # Refresh list
    admins = await user_service.get_all_admins()
    lines = ["👥 <b>Tizim administratorlari:</b>\n"]
    for adm in admins:
        badge = "👑 <b>Superadmin</b>" if adm["is_superadmin"] else "👔 <b>Admin</b>"
        lines.append(f"• {badge}: <b>{adm['name']}</b>\n   🆔 ID: <code>{adm['telegram_id']}</code>")

    keyboard = get_admin_management_keyboard(is_superadmin=is_superadmin)
    await callback.message.edit_text("\n".join(lines), reply_markup=keyboard, parse_mode="HTML")
