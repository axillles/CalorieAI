#!/bin/bash

# Скрипт для быстрого деплоя на Railway

echo "🚀 Подготовка к деплою на Railway..."

# Проверяем наличие Railway CLI
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI не установлен"
    echo "Установите: npm install -g @railway/cli"
    exit 1
fi

# Проверяем логин
if ! railway whoami &> /dev/null; then
    echo "🔐 Войдите в Railway:"
    railway login
fi

# Создаем проект если не существует
if [ ! -f ".railway/project.json" ]; then
    echo "📦 Создание нового проекта Railway..."
    railway new
fi

# Устанавливаем переменные окружения
echo "🔧 Настройка переменных окружения..."
echo "Введите ваши данные:"

read -p "TELEGRAM_BOT_TOKEN: " TELEGRAM_BOT_TOKEN
read -p "OPENAI_API_KEY: " OPENAI_API_KEY
read -p "SUPABASE_URL: " SUPABASE_URL
read -p "SUPABASE_KEY: " SUPABASE_KEY

# Устанавливаем переменные
railway variables set TELEGRAM_BOT_TOKEN="$TELEGRAM_BOT_TOKEN"
railway variables set OPENAI_API_KEY="$OPENAI_API_KEY"
railway variables set SUPABASE_URL="$SUPABASE_URL"
railway variables set SUPABASE_KEY="$SUPABASE_KEY"

# Опциональные переменные
read -p "OPENAI_ORG_ID (опционально): " OPENAI_ORG_ID
if [ ! -z "$OPENAI_ORG_ID" ]; then
    railway variables set OPENAI_ORG_ID="$OPENAI_ORG_ID"
fi

read -p "CRYPTO_TON_ADDRESS (опционально): " CRYPTO_TON_ADDRESS
if [ ! -z "$CRYPTO_TON_ADDRESS" ]; then
    railway variables set CRYPTO_TON_ADDRESS="$CRYPTO_TON_ADDRESS"
fi

read -p "CRYPTO_TRC20_USDT_ADDRESS (опционально): " CRYPTO_TRC20_USDT_ADDRESS
if [ ! -z "$CRYPTO_TRC20_USDT_ADDRESS" ]; then
    railway variables set CRYPTO_TRC20_USDT_ADDRESS="$CRYPTO_TRC20_USDT_ADDRESS"
fi

# Деплой
echo "🚀 Запуск деплоя..."
railway up

echo "✅ Деплой завершен!"
echo "📊 Проверьте статус: railway status"
echo "📝 Логи: railway logs"
echo "🌐 URL: railway domain"
