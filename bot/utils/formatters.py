from datetime import datetime
from typing import Dict
from bot.constants import STATUS_BADGES, STATUS_LABELS
from bot.database.models import Appeal


def format_appeal_summary(appeal: Appeal) -> str:
    badge = STATUS_BADGES.get(appeal.status, "📌")
    status_label = STATUS_LABELS.get(appeal.status, appeal.status)
    created_str = appeal.created_at.strftime("%d.%m.%Y %H:%M")
    
    first_msg = appeal.messages[0] if appeal.messages else None
    preview = first_msg.text if first_msg and first_msg.text else "(Fayl biriktirilgan)"
    if preview and len(preview) > 60:
        preview = preview[:57] + "..."

    return f"<b>{appeal.public_id}</b> — {badge} {status_label}\n📅 {created_str}\n💬 <i>{preview}</i>"


def format_appeal_detail(appeal: Appeal, for_admin: bool = False) -> str:
    badge = STATUS_BADGES.get(appeal.status, "📌")
    status_label = STATUS_LABELS.get(appeal.status, appeal.status)
    created_str = appeal.created_at.strftime("%d.%m.%Y %H:%M")

    lines = [
        f"📋 <b>MUROJAAT: {appeal.public_id}</b>",
        f"<b>Holati:</b> {badge} {status_label}",
        f"<b>Yuborilgan vaqti:</b> {created_str}",
    ]

    if appeal.closed_at:
        closed_str = appeal.closed_at.strftime("%d.%m.%Y %H:%M")
        lines.append(f"<b>Yopilgan vaqti:</b> {closed_str}")

    if for_admin and appeal.user:
        u = appeal.user
        user_mention = f"@{u.username}" if u.username else "mavjud emas"
        full_name = f"{u.first_name or ''} {u.last_name or ''}".strip() or "Noma'lum"
        lines.extend([
            f"👤 <b>Foydalanuvchi:</b> {full_name} ({user_mention})",
            f"🆔 <b>Telegram ID:</b> <code>{u.telegram_id}</code>",
        ])

    lines.append("\n━━━━━━━━━━━━━━━━━━━━━━\n<b>📜 XABARLAR TARIXI:</b>")

    total_attachments = 0
    if not appeal.messages:
        lines.append("<i>Xabarlar mavjud emas.</i>")
    else:
        for i, msg in enumerate(appeal.messages, 1):
            time_str = msg.created_at.strftime("%d.%m %H:%M")
            att_count = len(msg.attachments)
            total_attachments += att_count

            if msg.sender_type == "ADMIN":
                header = f"<b>👔 Yoshlar bo‘limi (Admin)</b> [{time_str}]"
            else:
                header = f"<b>👤 Talaba</b> [{time_str}]"

            content = msg.text or "(Fayl yuborilgan)"
            att_info = f" <i>(📎 {att_count} ta fayl)</i>" if att_count > 0 else ""
            lines.append(f"\n{header}{att_info}:\n{content}")

    lines.append(f"\n━━━━━━━━━━━━━━━━━━━━━━\n📎 <b>Jami biriktirilgan fayllar:</b> {total_attachments} ta")
    return "\n".join(lines)


def format_admin_notification(
    appeal: Appeal, preview_text: str, attachments_count: int
) -> str:
    user = appeal.user
    if user:
        full_name = f"{user.first_name or ''} {user.last_name or ''}".strip() or "Noma'lum"
        username_part = f" (@{user.username})" if user.username else ""
        tg_id = str(user.telegram_id)
    else:
        full_name = "Noma'lum"
        username_part = ""
        tg_id = "Noma'lum"

    text = (
        "🔔 <b>YANGI MUROJAAT</b>\n\n"
        f"🆔 <b>ID:</b> <b>{appeal.public_id}</b>\n"
        f"👤 <b>Foydalanuvchi:</b> {full_name}{username_part}\n"
        f"🆔 <b>Telegram ID:</b> <code>{tg_id}</code>\n\n"
        f"📝 <b>Murojaat matni:</b>\n{preview_text}\n\n"
        f"📎 <b>Fayllar:</b> {attachments_count} ta\n"
        f"📌 <b>Status:</b> NEW"
    )
    return text


def format_statistics(stats: Dict[str, int], total_users: int) -> str:
    return (
        "📊 <b>STATISTIKA</b>\n\n"
        f"👥 <b>Foydalanuvchilar:</b> {total_users:,}\n\n"
        f"📂 <b>Jami murojaatlar:</b> {stats['total']:,}\n\n"
        f"🆕 <b>Yangi:</b> {stats['new']}\n"
        f"🔄 <b>Ko‘rib chiqilmoqda:</b> {stats['in_progress']}\n"
        f"⏳ <b>Ma’lumot kutilmoqda:</b> {stats['waiting']}\n"
        f"✅ <b>Hal qilindi:</b> {stats['resolved']}\n"
        f"🔒 <b>Yopildi:</b> {stats['closed']}"
    )
