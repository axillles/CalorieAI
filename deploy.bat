@echo off
echo 🚀 Подготовка к деплою на Railway...

REM Проверяем наличие Railway CLI
where railway >nul 2>nul
if %errorlevel% neq 0 (
    echo ❌ Railway CLI не установлен
    echo Установите: npm install -g @railway/cli
    pause
    exit /b 1
)

REM Проверяем логин
railway whoami >nul 2>nul
if %errorlevel% neq 0 (
    echo 🔐 Войдите в Railway:
    railway login
)

REM Создаем проект если не существует
if not exist ".railway\project.json" (
    echo 📦 Создание нового проекта Railway...
    railway new
)

echo 🔧 Настройка переменных окружения...
echo Введите ваши данные:

set /p TELEGRAM_BOT_TOKEN="TELEGRAM_BOT_TOKEN: "
set /p OPENAI_API_KEY="OPENAI_API_KEY: "
set /p SUPABASE_URL="SUPABASE_URL: "
set /p SUPABASE_KEY="SUPABASE_KEY: "

REM Устанавливаем переменные
railway variables set TELEGRAM_BOT_TOKEN=%TELEGRAM_BOT_TOKEN%
railway variables set OPENAI_API_KEY=%OPENAI_API_KEY%
railway variables set SUPABASE_URL=%SUPABASE_URL%
railway variables set SUPABASE_KEY=%SUPABASE_KEY%

REM Опциональные переменные
set /p OPENAI_ORG_ID="OPENAI_ORG_ID (опционально): "
if not "%OPENAI_ORG_ID%"=="" (
    railway variables set OPENAI_ORG_ID=%OPENAI_ORG_ID%
)

set /p CRYPTO_TON_ADDRESS="CRYPTO_TON_ADDRESS (опционально): "
if not "%CRYPTO_TON_ADDRESS%"=="" (
    railway variables set CRYPTO_TON_ADDRESS=%CRYPTO_TON_ADDRESS%
)

set /p CRYPTO_TRC20_USDT_ADDRESS="CRYPTO_TRC20_USDT_ADDRESS (опционально): "
if not "%CRYPTO_TRC20_USDT_ADDRESS%"=="" (
    railway variables set CRYPTO_TRC20_USDT_ADDRESS=%CRYPTO_TRC20_USDT_ADDRESS%
)

set /p ENABLE_TRC20_MONITOR="ENABLE_TRC20_MONITOR (true/false, опционально): "
if not "%ENABLE_TRC20_MONITOR%"=="" (
    railway variables set ENABLE_TRC20_MONITOR=%ENABLE_TRC20_MONITOR%
)

set /p TRONGRID_API_KEY="TRONGRID_API_KEY (опционально): "
if not "%TRONGRID_API_KEY%"=="" (
    railway variables set TRONGRID_API_KEY=%TRONGRID_API_KEY%
)

set /p ENABLE_G4F_FALLBACK="ENABLE_G4F_FALLBACK (true/false, опционально): "
if not "%ENABLE_G4F_FALLBACK%"=="" (
    railway variables set ENABLE_G4F_FALLBACK=%ENABLE_G4F_FALLBACK%
)

set /p APP_URL="APP_URL (опционально): "
if not "%APP_URL%"=="" (
    railway variables set APP_URL=%APP_URL%
)

REM Деплой
echo 🚀 Запуск деплоя...
railway up

echo ✅ Деплой завершен!
echo 📊 Проверьте статус: railway status
echo 📝 Логи: railway logs
echo 🌐 URL: railway domain
pause
