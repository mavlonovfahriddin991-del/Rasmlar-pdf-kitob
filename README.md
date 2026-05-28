# 📚 Telegram Bot: Rasmlardan PDF Kitob Yaratuvchi Bot

Ushbu loyiha foydalanuvchilar tomonidan yuborilgan rasmlarni professional, kitob ko'rinishidagi PDF faylga aylantirib beruvchi Telegram botdir.

## 🚀 Qanday ishga tushiriladi?

Windows tizimida botni juda oson ishga tushirishingiz mumkin:

1. Kompyuteringizda **Python** o'rnatilganligiga ishonch hosil qiling. Agar yo'q bo'lsa, uni [python.org](https://www.python.org/downloads/) saytidan yuklab oling va o'rnatayotganda **"Add Python to PATH"** bandini belgilang.
2. Loyiha papkasidagi **`run.bat`** faylini ikki marta bosing (double-click).
3. Ushbu skript avtomatik ravishda barcha kerakli kutubxonalarni (`pyTelegramBotAPI`, `reportlab`, `pillow`) o'rnatadi va botni ishga tushiradi.
4. Bot ishga tushgach, Telegram-da botingiz bilan muloqotni boshlashingiz mumkin!

## 📖 Botdan foydalanish yo'riqnomasi

1. Telegram-da botga kirib `/start` yoki `/new` buyrug'ini yuboring.
2. Bot sizdan **Kitob nomi**ni so'raydi (masalan: *Mening yozgi xotiralarim*). Uni yozib yuboring.
3. Keyin **Muallif ismi**ni so'raydi (masalan: *Ali Valiyev*). Uni yozib yuboring.
4. **Kitob dizayni (Mavzu)**ni tanlang:
   - **Klassik (Classic) 🏛**: Times-Roman shrifti, nafis hoshiya va klassik kitob ko'rinishi.
   - **Zamonaviy (Modern) 📱**: Helvetica shrifti, chap tomonda rangli chiziq va minimalist uslub.
   - **Quvnoq (Playful) 🎨**: Courier shrifti va yorqin rangli bolalarcha hoshiyalar.
5. Kitobga qo'shmoqchi bo'lgan **rasmlaringizni yuboring**. Rasmlarni bittalab yoki hammasini birdaniga yuborishingiz mumkin.
6. Rasmlarni yuborganingizdan so'ng, boshqaruv paneli orqali:
   - Har bir rasm ostiga alohida **izoh (caption) yozishingiz** mumkin.
   - Kitobning **muqovasi (bosh sahifasi) uchun rasm tanlashingiz** mumkin.
7. Barchasi tayyor bo'lgach, **"📚 PDF Kitobni yaratish"** tugmasini bosing.
8. Bot sizga tayyor PDF kitobingizni bir necha soniyada yaratib, yuboradi.

## 📂 Loyiha tarkibi

- **`bot.py`**: Telegram bot logikasi, foydalanuvchi holatlari (State Machine) va PDF shakllantiruvchi qism.
- **`requirements.txt`**: Bot ishlashi uchun zarur bo'lgan Python kutubxonalari ro'yxati.
- **`run.bat`**: Botni Windows tizimida bir marta bosish orqali ishga tushiradigan skript.
- **`temp/`**: Rasmlar yuklanganda va PDF tayyorlanayotganda vaqtinchalik ma'lumotlar saqlanadigan papka. (PDF yuborilgach, ushbu ma'lumotlar avtomatik tozalab tashlanadi).
