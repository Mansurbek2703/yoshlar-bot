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
    "🏛 <b>Al-Xorazmiy universitetining Talabalarni qo‘llab-quvvatlash va o‘quv masalalari bo‘yicha murojaatlar botiga xush kelibsiz.</b>\n\n"
    "Ushbu bot orqali o‘quv jarayoni, talabalarga yaratilgan imkoniyatlar, ariza, taklif va muammolaringiz bo‘yicha murojaat yuborishingiz mumkin."
)

CONTACT_TEXT = (
    "📞 <b>Yoshlar bo‘limi bilan bog‘lanish</b>\n\n"
    "📍 <b>Manzil:</b> Al-Xorazmiy universiteti o'quv binosi\n"
    "📞 <b>Telefon:</b> +998 62 227 71 71\n"
    "✉️ <b>Elektron pochta:</b> r.khudayberganov@akhu.uz\n"
    "🌐 <b>Universitet sayti:</b> <a href=\"https://akhu.uz/\">akhu.uz</a>\n"
    "📢 <b>Rasmiy Telegram kanal:</b> @AKHU_students_channel\n\n"
    "⏰ <i>Ish vaqti: Dushanba – Juma, 09:00 dan 18:00 gacha</i>"
)
