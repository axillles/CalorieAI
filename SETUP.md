# 🚀 Инструкция по настройке КБЖУ Анализатора

## ✅ Проверка установки

Перед настройкой убедитесь, что все зависимости установлены:

```bash
python test_imports.py
```

Если все тесты пройдены, можно переходить к настройке.

## 🔧 Настройка API ключей

### 1. Создание файла .env

Создайте файл `.env` в корневой папке проекта:

```env
# Telegram Bot Token (получить у @BotFather)
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here

# OpenAI API Key (получить на https://platform.openai.com/api-keys)
OPENAI_API_KEY=your_openai_api_key_here

# Supabase Configuration (получить в настройках проекта Supabase)
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your_supabase_anon_key_here
```

### 2. Получение Telegram Bot Token

1. Напишите [@BotFather](https://t.me/BotFather) в Telegram
2. Выполните команду `/newbot`
3. Следуйте инструкциям для создания бота
4. Скопируйте полученный токен в `.env`

### 3. Получение OpenAI API Key

1. Зайдите на [platform.openai.com](https://platform.openai.com)
2. Создайте аккаунт или войдите
3. Перейдите в раздел API Keys
4. Создайте новый ключ
5. Скопируйте ключ в `.env`

### 4. Настройка Supabase (опционально)

Если хотите сохранять данные в базу данных:

1. Зайдите на [supabase.com](https://supabase.com)
2. Создайте новый проект
3. Получите URL и API ключ в настройках проекта
4. Выполните SQL из `setup_supabase_fixed.sql` в SQL Editor (рекомендуется) и `update_database_minimal.sql`
5. Скопируйте данные в `.env`

## 🗄️ Настройка базы данных Supabase

### Выполнение SQL скрипта

1. Откройте ваш проект Supabase
2. Перейдите в SQL Editor
3. Скопируйте содержимое файла `setup_supabase_fixed.sql`
4. Выполните скрипт

### Структура таблиц

- **users** - пользователи бота
- **food_images** - фотографии еды
- **nutrition_data** - данные о питании
- **daily_reports** - дневные отчеты

## 🚀 Запуск бота

### Тестовый запуск

```bash
python test_imports.py
```

### Основной запуск

```bash
python main.py
```

### Запуск в фоне (Linux/Mac)

```bash
nohup python main.py > bot.log 2>&1 &
```

### Запуск через systemd (Linux)

Создайте файл `/etc/systemd/system/tgcal-bot.service`:

```ini
[Unit]
Description=TGCal Nutrition Bot
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/TGCal
ExecStart=/usr/bin/python3 main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Затем:
```bash
sudo systemctl enable tgcal-bot
sudo systemctl start tgcal-bot
```

## 📱 Использование бота

### Команды

- `/start` - Начать работу с ботом
- `/stats` - Показать статистику за сегодня
- `/week` - Показать статистику за неделю
- `/help` - Справка по использованию

### Анализ фотографий

1. Отправьте фотографию еды боту
2. Дождитесь анализа (5-10 секунд)
3. Получите результат с КБЖУ
4. Данные автоматически сохраняются

## 🔍 Отладка

### Проверка логов

```bash
tail -f bot.log
```

### Проверка статуса (systemd)

```bash
sudo systemctl status tgcal-bot
```

### Проверка подключения к БД

```bash
python -c "from config.database import db_manager; print('DB OK' if db_manager.get_client() else 'DB Error')"
```

## 🐛 Устранение неполадок

### Ошибка "TELEGRAM_BOT_TOKEN не установлен"

- Проверьте файл `.env`
- Убедитесь, что токен скопирован правильно
- Проверьте права доступа к файлу

### Ошибка "OPENAI_API_KEY не установлен"

- Проверьте файл `.env`
- Убедитесь, что ключ скопирован правильно
- Проверьте баланс OpenAI API

### Ошибка подключения к Supabase

- Проверьте URL и ключ в `.env`
- Убедитесь, что проект активен
- Проверьте настройки RLS

### Ошибка анализа изображений

- Проверьте баланс OpenAI API
- Убедитесь в правильности API ключа
- Проверьте размер изображения (макс. 20MB)

## 💰 Стоимость

### OpenAI Vision API
- ~$0.01-0.03 за изображение
- Зависит от размера изображения

### Supabase
- Бесплатный тариф: 500MB БД, 50K запросов/месяц
- $25/месяц при росте (50GB БД, 500K запросов)

## 📞 Поддержка

При возникновении проблем:

1. Проверьте логи бота
2. Запустите `python test_imports.py`
3. Проверьте настройки в `.env`
4. Обратитесь к разработчику

## 🔄 Обновления

Для обновления бота:

```bash
git pull origin main
pip install -r requirements.txt
python test_imports.py
```

## 📝 Лицензия

MIT License - используйте свободно!
