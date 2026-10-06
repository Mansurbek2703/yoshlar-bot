from enum import Enum


class AppealStatus(str, Enum):
    NEW = "NEW"
    IN_PROGRESS = "IN_PROGRESS"
    WAITING = "WAITING"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"


STATUS_LABELS = {
    AppealStatus.NEW.value: "🆕 Yangi",
    AppealStatus.IN_PROGRESS.value: "🔄 Ko‘rib chiqilmoqda",
    AppealStatus.WAITING.value: "⏳ Ma’lumot kutilmoqda",
    AppealStatus.RESOLVED.value: "✅ Hal qilindi",
    AppealStatus.CLOSED.value: "🔒 Yopildi",
}

STATUS_BADGES = {
    AppealStatus.NEW.value: "🆕",
    AppealStatus.IN_PROGRESS.value: "🔄",
    AppealStatus.WAITING.value: "⏳",
    AppealStatus.RESOLVED.value: "✅",
    AppealStatus.CLOSED.value: "🔒",
}

START_TEXT = (
    "👋 <b>Assalomu alaykum!</b>\n\n"
    "🏛 <b>Al-Xorazmiy universiteti Yoshlar bo‘limining</b> murojaatlar botiga xush kelibsiz.\n\n"
    "Ushbu bot orqali Yoshlar bo‘limiga murojaat, taklif, ariza va muammolaringizni yuborishingiz mumkin.\n\n"
    "Kerakli bo‘limni tanlang:"
)

ABOUT_TEXT = (
    "ℹ️ <b>Yoshlar bo‘limi haqida</b>\n\n"
    "Yoshlar bilan ishlash, ma’naviyat va ma’rifat bo‘limi universitet talabalarining "
    "intellektual, ijodiy va ijtimoiy faolligini oshirish, talabalar turmush sharoitini yaxshilash "
    "hamda ularni har tomonlama qo‘llab-quvvatlash bilan shug‘ullanadi.\n\n"
    "<b>Bo‘limning asosiy vazifalari:</b>\n"
    "• Talabalarning huquq va manfaatlarini himoya qilish;\n"
    "• Talabalar murojaatlari, taklif va muammolarini o‘z vaqtida ko‘rib chiqish;\n"
    "• Talabalar turar joyi va ijtimoiy masalalarni muvofiqlashtirish;\n"
    "• Ma’naviy-ma’rifiy tadbirlar, to‘garaklar va yoshlar loyihalarini tashkil etish;\n"
    "• Iqtidorli talabalarni rag‘batlantirish va qo‘llab-quvvatlash."
)

CONTACT_TEXT = (
    "📞 <b>Yoshlar bo‘limi bilan bog‘lanish</b>\n\n"
    "📍 <b>Manzil:</b> Al-Xorazmiy universiteti asosiy binosi\n"
    "🏢 <b>Xona:</b> Yoshlar bo‘limi (204-xona)\n"
    "📞 <b>Telefon:</b> +998 71 200 00 00\n"
    "✉️ <b>Elektron pochta:</b> yoshlar@akhu.uz\n"
    "🌐 <b>Universitet sayti:</b> <a href=\"https://akhu.uz\">akhu.uz</a>\n"
    "📢 <b>Rasmiy Telegram kanal:</b> @akhu_yoshlar\n\n"
    "⏰ <i>Ish vaqti: Dushanba – Juma, 09:00 dan 18:00 gacha</i>"
)
