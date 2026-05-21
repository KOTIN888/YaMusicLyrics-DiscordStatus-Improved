@echo off
title YaMusicLyrics Discord Status
chcp 65001 >nul
echo ========================================
echo   YaMusicLyrics Discord Status
echo ========================================
echo.

:: Переходим в папку со скриптом
cd /d "%~dp0"

:: Проверяем, есть ли .venv
if not exist ".venv\Scripts\activate.bat" (
    echo [ОШИБКА] Виртуальное окружение не найдено!
    echo Создаю...
    python -m venv .venv
)

:: Активируем окружение
echo [OK] Активация окружения...
call .venv\Scripts\activate.bat

:: Устанавливаем ВСЕ необходимые модули
echo [OK] Установка модулей...
echo Это займёт 1-2 минуты...
pip install aiohttp winrt-runtime winrt-Windows.Media.Control winrt-Windows.Foundation winrt-Windows.Foundation.Collections -q

echo.
echo [OK] Запуск скрипта...
echo ========================================
echo.

:: Запускаем скрипт
python main.py

:: Не закрывать окно
echo.
pause