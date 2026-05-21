@echo off
chcp 65001 >nul
title "YaMusicLyrics - Установка"
color 0A
cd /d "%~dp0"

echo ========================================
echo   YaMusicLyrics Discord Status
echo ========================================
echo.

:: Проверяем Python
echo [ПРОВЕРКА] Ищу Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo [ОШИБКА] Python не найден!
    echo.
    echo 1. Скачай: https://www.python.org/downloads/
    echo 2. При установке ОТМЕТЬ ГАЛОЧКУ:
    echo    "Add Python to PATH"
    echo.
    pause
    exit /b 1
)

echo [OK] Python найден
python --version
echo.

if exist ".venv" (
    echo [OK] Виртуальное окружение найдено
    echo.
    echo [ЗАПУСК] Начинаю...
    echo ========================================
    echo.
    call .venv\Scripts\activate.bat
    python main.py
) else (
    echo [УСТАНОВКА] Создаю окружение...
    python -m venv .venv
    if errorlevel 1 (
        echo [ОШИБКА] Не удалось создать .venv
        pause
        exit /b 1
    )
    
    echo [УСТАНОВКА] Устанавливаю библиотеки...
    echo (это займёт 1-2 минуты, не закрывай окно)
    call .venv\Scripts\activate.bat
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [ОШИБКА] Не удалось установить библиотеки
        pause
        exit /b 1
    )
    
    echo.
    echo [OK] Готово! Создаю config.json...
    (
        echo {
        echo   "discord_token": "",
        echo   "time_offset": 2.0
        echo }
    ) > config.json
    
    echo.
    echo ========================================
    echo   ТЕПЕРЬ ВСТАВЬ ТОКЕН В config.json
    echo ========================================
    echo.
    echo 1. Открой config.json
    echo 2. Вставь токен между кавычками
    echo 3. Сохрани
    echo 4. Запусти этот файл ещё раз
    echo.
    notepad config.json
    
    echo.
    pause
)

echo.
pause