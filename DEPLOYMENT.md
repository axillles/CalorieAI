# 🚀 Деплой Telegram Nutrition Bot на Railway

## 📋 Подготовка к деплою

### 1. Создание аккаунта и проекта

1. **Зарегистрируйтесь на Railway**: https://railway.app
2. **Подключите GitHub**: Свяжите ваш GitHub аккаунт с Railway
3. **Создайте новый проект**: "New Project" → "Deploy from GitHub repo"

### 2. Настройка переменных окружения

В Railway Dashboard → Variables добавьте следующие переменные:

#### Обязательные переменные:
```bash
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
OPENAI_API_KEY=your_openai_api_key_here
SUPABASE_URL=your_supabase_url_here
SUPABASE_KEY=your_supabase_key_here
```

#### Дополнительные переменные (опционально):
```bash
OPENAI_ORG_ID=your_openai_org_id_here
ENABLE_G4F_FALLBACK=true
APP_URL=https://your-app-name.railway.app
CRYPTO_TON_ADDRESS=your_ton_address_here
CRYPTO_TRC20_USDT_ADDRESS=your_trc20_usdt_address_here
```

### 3. Настройка базы данных

1. **Создайте проект в Supabase**: https://supabase.com
2. **Выполните SQL скрипты** в Supabase SQL Editor:
   - `setup_supabase_fixed.sql` - основная схема
   - `add_total_photos_column.sql` - дополнительные колонки
   - `update_database_schema.sql` - обновления схемы

### 4. Деплой

1. **Выберите репозиторий**: Выберите ваш GitHub репозиторий с ботом
2. **Railway автоматически определит настройки** из `railway.json`
3. **Деплой запустится автоматически** после push в main ветку

## 🔧 Альтернативные платформы

### Heroku (бесплатный план недоступен)
```bash
# Создайте Procfile
echo "web: python run_bot.py" > Procfile

# Деплой через Heroku CLI
heroku create your-bot-name
heroku config:set TELEGRAM_BOT_TOKEN=your_token
heroku config:set OPENAI_API_KEY=your_key
# ... остальные переменные
git push heroku main
```

### Render
1. Подключите GitHub репозиторий
2. Выберите "Web Service"
3. Build Command: `pip install -r requirements.txt`
4. Start Command: `python run_bot.py`
5. Добавьте переменные окружения

### DigitalOcean App Platform
1. Создайте App из GitHub
2. Выберите Python
3. Build Command: `pip install -r requirements.txt`
4. Run Command: `python run_bot.py`
5. Настройте переменные окружения

## 📊 Мониторинг

### Railway Dashboard
- **Logs**: Просмотр логов в реальном времени
- **Metrics**: CPU, память, сеть
- **Deployments**: История деплоев

### Health Check
Бот автоматически предоставляет health check endpoint:
```
GET https://your-app.railway.app/health
```

## 🔄 Обновления

### Автоматический деплой
При push в main ветку Railway автоматически:
1. Скачает новый код
2. Установит зависимости
3. Перезапустит приложение

### Ручной деплой
```bash
# В Railway Dashboard
Deployments → Deploy Latest
```

## 🐛 Отладка

### Логи
```bash
# В Railway Dashboard
Deployments → View Logs
```

### Локальная отладка
```bash
# Установите Railway CLI
npm install -g @railway/cli

# Логин
railway login

# Подключитесь к проекту
railway link

# Просмотр логов
railway logs
```

## 💰 Стоимость

### Railway
- **Бесплатный план**: $5 кредитов в месяц
- **Pro план**: $5/месяц + использование
- **Хватит для небольшого бота**: ~1000 пользователей

### Альтернативы
- **Render**: Бесплатный план с ограничениями
- **Heroku**: Только платные планы
- **DigitalOcean**: $5/месяц

## 🔒 Безопасность

### Переменные окружения
- ✅ Никогда не коммитьте `.env` файлы
- ✅ Используйте Railway Variables для секретов
- ✅ Регулярно ротируйте API ключи

### Supabase
- ✅ Настройте RLS (Row Level Security)
- ✅ Ограничьте доступ к API ключам
- ✅ Используйте отдельную базу для продакшена

## 📈 Масштабирование

### При росте пользователей:
1. **Upgrade Railway план**
2. **Настройте Supabase Pro**
3. **Добавьте кэширование**
4. **Оптимизируйте запросы к БД**

### Мониторинг производительности:
- Railway Metrics
- Supabase Dashboard
- Telegram Bot Analytics

## 🆘 Поддержка

### Полезные ссылки:
- [Railway Docs](https://docs.railway.app)
- [Supabase Docs](https://supabase.com/docs)
- [Telegram Bot API](https://core.telegram.org/bots/api)

### Частые проблемы:
1. **Бот не отвечает**: Проверьте TELEGRAM_BOT_TOKEN
2. **Ошибки БД**: Проверьте SUPABASE_URL и SUPABASE_KEY
3. **OpenAI ошибки**: Проверьте OPENAI_API_KEY и лимиты
4. **Деплой не работает**: Проверьте логи в Railway Dashboard
