from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


def get_main_menu(is_admin: bool = False) -> ReplyKeyboardMarkup:
    keyboard = [
        [
            KeyboardButton(text="📩 Murojaat yuborish"),
            KeyboardButton(text="📋 Murojaatlarim"),
        ],
        [
            KeyboardButton(text="📞 Bog‘lanish"),
        ],
    ]
    if is_admin:
        keyboard.append([KeyboardButton(text="⚙️ Admin panel")])

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        input_field_placeholder="Murojaat yuborish yoki bo‘limni tanlang...",
    )


def get_draft_control_keyboard() -> ReplyKeyboardMarkup:
    keyboard = [
        [
            KeyboardButton(text="➕ Yana fayl/xabar qo‘shish"),
            KeyboardButton(text="✅ Murojaatni yuborish"),
        ],
        [
            KeyboardButton(text="❌ Bekor qilish"),
        ],
    ]
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        input_field_placeholder="Qo‘shimcha fayl yuboring yoki yakunlang...",
    )


def get_cancel_keyboard() -> ReplyKeyboardMarkup:
    keyboard = [
        [
            KeyboardButton(text="❌ Bekor qilish"),
        ]
    ]
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        input_field_placeholder="Xabarni yuboring yoki bekor qiling...",
    )


def get_admin_main_menu() -> ReplyKeyboardMarkup:
    keyboard = [
        [
            KeyboardButton(text="📥 Yangi murojaatlar"),
            KeyboardButton(text="📋 Barcha murojaatlar"),
        ],
        [
            KeyboardButton(text="🔎 Murojaatni qidirish"),
            KeyboardButton(text="📢 Broadcast"),
        ],
        [
            KeyboardButton(text="📊 Statistika"),
            KeyboardButton(text="👥 Adminlar"),
        ],
        [
            KeyboardButton(text="🏠 Asosiy menyu"),
        ],
    ]
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        input_field_placeholder="Admin boshqaruv bo‘limini tanlang...",
    )
