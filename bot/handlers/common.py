import logging
from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession
from bot.constants import CONTACT_TEXT, START_TEXT
from bot.keyboards.default import get_main_menu
from bot.services.user_service import UserService

logger = logging.getLogger(__name__)
router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, session: AsyncSession, is_admin: bool):
    await state.clear()
    user_service = UserService(session)
    await user_service.get_or_create_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name,
    )
    keyboard = get_main_menu(is_admin=is_admin)
    await message.answer(START_TEXT, reply_markup=keyboard, parse_mode="HTML")


@router.message(Command("help"))
async def cmd_help(message: Message, state: FSMContext, is_admin: bool):
    await state.clear()
    help_text = (
        "ℹ️ <b>Yordam bo‘limi</b>\n\n"
        "• <b>📩 Murojaat yuborish</b> — Ariza, taklif yoki muammolaringizni yuborish.\n"
        "• <b>📋 Murojaatlarim</b> — Yuborilgan murojaatlaringiz holati va javoblarini ko‘rish.\n"
        "• <b>📞 Bog‘lanish</b> — Yoshlar bo‘limi mas’ullari bilan bog‘lanish kontaktlari.\n\n"
        "Murojaat yuborishda matn, rasm, video, audio va hujjatlarni biriktirishingiz mumkin."
    )
    await message.answer(help_text, reply_markup=get_main_menu(is_admin=is_admin), parse_mode="HTML")


@router.message(F.text == "📞 Bog‘lanish")
async def btn_contact(message: Message, is_admin: bool):
    await message.answer(CONTACT_TEXT, reply_markup=get_main_menu(is_admin=is_admin), parse_mode="HTML")


@router.message(F.text == "🏠 Asosiy menyu")
@router.message(F.text == "❌ Bekor qilish")
async def btn_cancel_or_main_menu(message: Message, state: FSMContext, is_admin: bool):
    current_state = await state.get_state()
    if current_state:
        await state.clear()
        await message.answer(
            "❌ Jarayon bekor qilindi.",
            reply_markup=get_main_menu(is_admin=is_admin),
        )
    else:
        await message.answer(
            "Asosiy menyu:",
            reply_markup=get_main_menu(is_admin=is_admin),
        )
