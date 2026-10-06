from typing import Any, Dict, List, Optional
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from bot.constants import STATUS_BADGES, STATUS_LABELS, AppealStatus
from bot.database.models import Appeal


def get_admin_appeal_keyboard(appeal_id: int, status: str, is_detail: bool = False) -> InlineKeyboardMarkup:
    badge = STATUS_BADGES.get(status, "📌")
    detail_btn_text = "🔄 Yangilash" if is_detail else "📋 Batafsil"
    buttons = [
        [
            InlineKeyboardButton(text="💬 Javob berish", callback_data=f"adm_reply:{appeal_id}"),
            InlineKeyboardButton(text=f"🔄 Status ({badge})", callback_data=f"adm_status_menu:{appeal_id}"),
        ],
        [
            InlineKeyboardButton(text="📁 Fayllarni ko‘rish", callback_data=f"adm_files:{appeal_id}"),
            InlineKeyboardButton(text=detail_btn_text, callback_data=f"adm_detail:{appeal_id}"),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_status_change_keyboard(appeal_id: int, current_status: str) -> InlineKeyboardMarkup:
    buttons = []
    for st in AppealStatus:
        label = STATUS_LABELS.get(st.value, st.value)
        if st.value == current_status:
            label = f"🔘 {label}"
        buttons.append([InlineKeyboardButton(text=label, callback_data=f"set_st:{appeal_id}:{st.value}")])

    buttons.append([InlineKeyboardButton(text="🔙 Orqaga", callback_data=f"adm_detail:{appeal_id}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_user_appeal_keyboard(appeal_id: int, is_closed: bool = False) -> InlineKeyboardMarkup:
    buttons = []
    if not is_closed:
        buttons.append([
            InlineKeyboardButton(text="💬 Qo‘shimcha xabar yuborish", callback_data=f"usr_followup:{appeal_id}")
        ])
    buttons.append([
        InlineKeyboardButton(text="📁 Biriktirilgan fayllar", callback_data=f"usr_files:{appeal_id}")
    ])
    buttons.append([
        InlineKeyboardButton(text="🔙 Murojaatlarim ro‘yxati", callback_data="usr_my_appeals")
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_appeals_list_keyboard(
    appeals: List[Appeal],
    callback_prefix: str,
    page: int = 1,
    total_pages: int = 1,
    filter_type: str = "all",
) -> InlineKeyboardMarkup:
    keyboard = []
    for app in appeals:
        badge = STATUS_BADGES.get(app.status, "📌")
        btn_text = f"{app.public_id} — {badge} {app.status}"
        keyboard.append([
            InlineKeyboardButton(text=btn_text, callback_data=f"{callback_prefix}:{app.id}")
        ])

    nav_buttons = []
    if page > 1:
        nav_buttons.append(
            InlineKeyboardButton(text="◀️ Oldingi", callback_data=f"page:{filter_type}:{page - 1}")
        )
    if total_pages > 1:
        nav_buttons.append(
            InlineKeyboardButton(text=f"📄 {page}/{total_pages}", callback_data="noop")
        )
    if page < total_pages:
        nav_buttons.append(
            InlineKeyboardButton(text="Keyingi ▶️", callback_data=f"page:{filter_type}:{page + 1}")
        )

    if nav_buttons:
        keyboard.append(nav_buttons)

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_broadcast_confirm_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Ha, hammaga yuborilsin", callback_data="bc_confirm"),
                InlineKeyboardButton(text="❌ Bekor qilish", callback_data="bc_cancel"),
            ]
        ]
    )


def get_admin_management_keyboard(is_superadmin: bool = False) -> InlineKeyboardMarkup:
    buttons = []
    if is_superadmin:
        buttons.append([
            InlineKeyboardButton(text="➕ Yangi admin qo‘shish", callback_data="adm_add_admin"),
            InlineKeyboardButton(text="🗑 Adminni o‘chirish", callback_data="adm_del_admin_menu"),
        ])
    buttons.append([
        InlineKeyboardButton(text="🔄 Yangilash", callback_data="adm_refresh_admins"),
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_remove_admin_keyboard(admins: List[Dict[str, Any]]) -> InlineKeyboardMarkup:
    buttons = []
    for adm in admins:
        if adm.get("can_remove"):
            btn_text = f"❌ {adm['name']} ({adm['telegram_id']})"
            buttons.append([
                InlineKeyboardButton(text=btn_text, callback_data=f"adm_do_remove:{adm['telegram_id']}")
            ])

    buttons.append([
        InlineKeyboardButton(text="🔙 Orqaga", callback_data="adm_refresh_admins")
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)
