# Yoshlar bo‘limiga murojaatlar Telegram boti

Al-Xorazmiy universiteti Yoshlar bo‘limi uchun talabalar murojaatlari, taklif va shikoyatlarini qabul qilish, boshqarish va ko‘rib chiqish tizimi.

---

## 🚀 Asosiy imkoniyatlar

### 👤 Talaba / Foydalanuvchi:
- `/start` orqali tizimdan avtomatik ro‘yxatdan o‘tish;
- **Murojaat yuborish:** matn, rasm, video, audio, ovozli xabar va hujjatlarni biriktirish;
- Bitta murojaatga bir nechta fayl/xabarni to‘plash va biriktirish;
- Har bir murojaatga unikal raqam berilishi (masalan: `#000125`);
- **Murojaatlarim:** o‘z murojaatlari holati, tarixi va biriktirilgan fayllarni ko‘rish;
- Yoshlar bo‘limi mas’ullaridan to‘g‘ridan-to‘g‘ri javob olish;
- Ochiq murojaatlarga qo‘shimcha xabarlar va fayllar yuborish.

### 👔 Administrator (Yoshlar bo‘limi):
- Maxsus **⚙️ Admin panel** (faqat belgilangan Telegram ID egalari uchun);
- **Yangi murojaatlar:** yangi kelgan arizalarni tezkor ko‘rib chiqish;
- **Barcha murojaatlar:** barcha murojaatlar ro‘yxati (sahifalash / pagination bilan);
- **Statuslarni boshqarish:** `NEW`, `IN_PROGRESS`, `WAITING`, `RESOLVED`, `CLOSED`;
- **Murojaatga javob berish:** matn, rasm, video, hujjat yoki ovozli xabar orqali talabaga qayta aloqa;
- **Qidiruv:** ID raqami (`#000125`), talaba Telegram ID yoki ismi bo‘yicha qidirish;
- **Statistika:** foydalanuvchilar va murojaatlar soni bo‘yicha to‘liq hisobot;
- **Broadcast:** barcha talabalarga ommaviy xabar yuborish (rate limit va xatoliklar hisobi bilan).

---

## 🛠 Texnologiyalar

- **Dasturlash tili:** Python 3.11+
- **Telegram Bot Framework:** [aiogram 3.x](https://docs.aiogram.dev/)
- **Asinxron Web Server:** aiohttp (Webhook rejimi uchun)
- **Ma’lumotlar bazasi:** PostgreSQL
- **ORM:** SQLAlchemy 2.0 (asinxron, asyncpg drayveri)
- **Migratsiyalar:** Alembic
- **Konfiguratsiya:** Pydantic-Settings & python-dotenv

---

## 📁 Loyiha tuzilishi

```text
BOT AKHU/
├── alembic/                      # Alembic migratsiya fayllari
│   ├── versions/
│   │   └── 001_initial_tables.py
│   ├── env.py
│   └── script.py.mako
├── bot/
│   ├── database/                 # Bazalar va modellar
│   │   ├── base.py
│   │   ├── models.py
│   │   └── session.py
│   ├── handlers/                 # Telegram hodisa qayta ishlovchilari
│   │   ├── admin.py
│   │   ├── appeal.py
│   │   ├── broadcast.py
│   │   └── common.py
│   ├── keyboards/                # Tugmalar (Reply & Inline)
│   │   ├── default.py
│   │   └── inline.py
│   ├── middlewares/              # O‘rta qatlam (DB session, Auth)
│   │   ├── auth.py
│   │   └── db.py
│   ├── services/                 # Biznes mantiq qatlami
│   │   ├── appeal_service.py
│   │   ├── broadcast_service.py
│   │   └── user_service.py
│   ├── states/                   # FSM holatlari
│   │   └── states.py
│   ├── utils/                    # Formatlash va xabarnomalar
│   │   ├── formatters.py
│   │   └── notifier.py
│   ├── config.py                 # Sozlamalar
│   └── constants.py              # Matn va status konstantalari
├── nginx/
│   └── yoshlar.akhu.uz.conf      # Nginx teskari proksi konfiguratsiyasi
├── scripts/
│   ├── backup.sh                 # Bazani avtomatik zaxiralash
│   └── deploy.sh                 # Serverga deploy skripti
├── systemd/
│   └── youth-affairs-bot.service # Systemd service fayli
├── docker-compose.yml
├── Dockerfile
├── alembic.ini
├── main.py                       # Asosiy ishga tushirish fayli
├── requirements.txt
└── .env.example
```

---

## ⚙️ Sozlash va ishga tushirish

### 1. Lokal muhitda o‘rnatish

```bash
# Virtual muhit yaratish
python -m venv venv
source venv/bin/activate  # Windows: .\venv\Scripts\activate

# Kerakli kutubxonalarni o‘rnatish
pip install -r requirements.txt

# .env faylini yaratish
cp .env.example .env
```

### 2. Konfiguratsiya (`.env`)

```env
BOT_TOKEN=telegram_bot_tokeningiz

# Ma'lumotlar bazasi
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/youth_bot

# Administrator Telegram ID lari (vergul bilan)
ADMIN_IDS=123456789,987654321

# Ishlash rejimi (Lokal sinov uchun False, serverda True)
USE_WEBHOOK=False
WEBHOOK_HOST=https://yoshlar.akhu.uz
WEBHOOK_PATH=/webhook
WEBHOOK_SECRET=maxfiy_token
WEB_SERVER_HOST=0.0.0.0
WEB_SERVER_PORT=8000
```

### 3. Migratsiyalarni qo‘llash

```bash
alembic upgrade head
```

### 4. Botni ishga tushirish

```bash
python main.py
```

---

## 🌐 Serverda Webhook va Nginx orqali ishga tushirish

1. Domain: `yoshlar.akhu.uz` (DNS 86.62.0.182 ga yo‘naltirilgan)
2. Nginx: Port 443 (HTTPS) dan VM server `192.168.1.3:8000` ga yo‘naltirilgan
3. `.env` da sozlang:
   ```env
   USE_WEBHOOK=True
   WEBHOOK_HOST=https://yoshlar.akhu.uz
   WEBHOOK_PATH=/webhook
   WEB_SERVER_HOST=0.0.0.0
   WEB_SERVER_PORT=8000
   ```
4. Systemd xizmatini yoqish:
   ```bash
   sudo cp systemd/youth-affairs-bot.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable --now youth-affairs-bot
   ```

---

## 💾 Ma’lumotlar bazasini zaxiralash (Backup)

Kunlik avtomatik backup uchun crontab ga qo‘shing:
```bash
0 3 * * * /opt/youth-bot/scripts/backup.sh >> /opt/youth-bot/logs/backup.log 2>&1
```
Bu har kecha soat 03:00 da bazani arxivlab, 14 kundan eski nusxalarni avtomatik tozalaydi.
