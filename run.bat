@echo off
title Telegram Bot - Rasmlar PDF Kitob
echo ==================================================
echo       Telegram Bot: Rasmlar PDF Kitob
echo ==================================================
echo.

:: Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [XATOLIK] Tizimda Python topilmadi!
    echo Iltimos, Python-ni o'rnating va uni PATH-ga qo'shing.
    echo Yuklab olish: https://www.python.org/downloads/
    echo.
    pause
    exit /b
)

echo [OK] Python topildi.
echo.
echo [INFO] Zarur kutubxonalarni tekshirish va o'rnatish...
python -m pip install --upgrade pip
pip install -r requirements.txt

if %errorlevel% neq 0 (
    echo.
    echo [XATOLIK] Kutubxonalarni o'rnatishda muammo yuz berdi.
    echo Internet aloqasini tekshiring.
    echo.
    pause
    exit /b
)

echo.
echo [OK] Barcha kutubxonalar tayyor!
echo [INFO] Bot ishga tushirilmoqda...
echo.
python bot.py

pause
