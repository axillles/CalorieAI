# 🤖 КБЖУ Анализатор - Telegram Bot

Телеграм бот для анализа калорийности и состава пищи по фотографиям с использованием OpenAI Vision API.

## 🚀 Возможности

- 📸 Анализ КБЖУ по фотографиям еды (первое фото бесплатно!)
- 💧 Отслеживание потребления воды
- 📊 Дневная статистика потребления
- 📈 Недельные отчеты с графиками
- 🎯 Персональные цели питания и воды
- 💳 Система подписок для неограниченного анализа фото
- 📊 Отслеживание использования и лимитов
- 💾 Сохранение данных в Supabase
- 🎨 Красивые отчеты с прогресс-барами
- 🔘 Интерактивные кнопки и меню

## 🛠️ Технологии

- **Python 3.8+**
- **python-telegram-bot** - Telegram Bot API
- **OpenAI GPT-4 Vision** - Анализ изображений
- **Supabase** - База данных и хранение
- **Pillow** - Обработка изображений

## 📋 Требования

- Python 3.8 или выше
- Telegram Bot Token
- OpenAI API Key
- Supabase проект (опционально)

## 🔧 Быстрая установка

### 1. Клонирование репозитория
```bash
git clone <repository-url>
cd TGCal
```

### 2. Установка зависимостей
```bash
pip install -r requirements.txt
```

### 3. Проверка установки
```bash
python test_imports.py
```

### 4. Настройка переменных окружения
Создайте файл `.env` на основе `env_example.txt`:

```bash
cp env_example.txt .env
```

Заполните переменные в файле `.env`:

```env
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
OPENAI_API_KEY=your_openai_api_key_here
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your_supabase_anon_key_here
```

### 5. Проверка конфигурации
```bash
python check_config.py
```

### 6. Тестирование токена (опционально)
```bash
python test_token.py
```

### 7. Запуск

#### Для Windows:
```bash
# Стандартный запуск с nest_asyncio
python run_bot.py
python main.py
```

#### Для Linux/Mac:
```bash
python main.py
```

## 📖 Подробная настройка

Для подробной инструкции по настройке см. [SETUP.md](SETUP.md)

## 🗄️ Настройка Supabase

### Создание таблиц
Выполните SQL из `setup_supabase_fixed.sql` в SQL Editor Supabase (рекомендуется):

```sql
-- Используйте setup_supabase_fixed.sql для избежания проблем с RLS
```

**⚠️ Важно**: Если используете оригинальный `setup_supabase.sql`, может возникнуть ошибка RLS. См. [FIX_SUPABASE_RLS.md](FIX_SUPABASE_RLS.md) для исправления.

## 💳 Система подписок

### 🆓 Бесплатный план:
- **1 фото** для анализа бесплатно
- Базовые функции бота

### 💰 Платные планы:
- **Месячная подписка**: $4.99/месяц
- **Годовая подписка**: $49.99/год (экономия 17%)
- **Безлимитный анализ** фото
- Все функции бота

### 🔧 Настройка платежей (крипто):
Сейчас включен только перевод на криптокошелёк (TON/USDT TRC20).

1) В `.env` добавьте адреса:

```
# Crypto
CRYPTO_TON_ADDRESS=ton_your_address_here
CRYPTO_TRC20_USDT_ADDRESS=TRC20_your_address_here

# Провайдеры
ENABLED_PAYMENT_PROVIDERS=crypto
PRIMARY_PAYMENT_PROVIDER=crypto
```

2) Где взять адреса:
- TG Wallet (TON): откройте Telegram Wallet и скопируйте адрес TON.
- Bybit (USDT TRC20): Wallet → Deposits → USDT → сеть TRON (TRC20) → скопируйте адрес.

3) Как это работает:
- Пользователь выбирает план, видит адрес(а) TON/TRC20 и кнопку «Я оплатил».
- Переводит эквивалент суммы и подтверждает.
- Бот сразу активирует подписку (доверительный режим).

Примечание: Автопроверки транзакций нет. При необходимости сверяйте поступления вручную.

```sql
-- Таблица пользователей
CREATE TABLE users (
    id BIGSERIAL PRIMARY KEY,
    telegram_id BIGINT UNIQUE NOT NULL,
    username VARCHAR(255),
    daily_calories_goal INTEGER DEFAULT 2000,
    daily_protein_goal INTEGER DEFAULT 150,
    daily_fats_goal INTEGER DEFAULT 65,
    daily_carbs_goal INTEGER DEFAULT 250,
    daily_water_goal_ml INTEGER DEFAULT 2000,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Таблица потребления воды
CREATE TABLE water_intake (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
    amount_ml INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Остальные таблицы см. setup_supabase_fixed.sql
```

## 📱 Использование

### Команды бота:
- `/start` - Начать работу с ботом
- `/stats` - Показать статистику за сегодня
- `/week` - Показать статистику за неделю
- `/help` - Справка по использованию

### Интерактивные кнопки:
- **➕ Вода +250мл** - Добавить 250мл воды к дневной норме
- **📋 Меню** - Открыть главное меню с разделами
- **📊 День** - Показать дневную статистику КБЖУ + вода
- **📈 Неделя** - Показать недельную статистику с графиком воды
- **⚙️ Настройки воды** - Изменить дневную норму воды (1500/2000/2500/3000мл)

### Анализ фотографий:
1. Отправьте фотографию еды боту
2. Дождитесь анализа (обычно 5-10 секунд)
3. Получите результат с КБЖУ и кнопками
4. Данные автоматически сохраняются в ваш дневник

### Отслеживание воды:
1. Нажмите кнопку "➕ Вода +250мл" для добавления воды
2. Используйте "📋 Меню" для навигации
3. Просматривайте статистику воды в дневных и недельных отчётах
4. Настройте дневную норму воды в разделе "⚙️ Настройки воды"

## 📊 Структура проекта

```
TGCal/
├── config/
│   ├── settings.py          # Настройки приложения
│   └── database.py          # Подключение к БД
├── models/
│   └── data_models.py       # Модели данных
├── services/
│   ├── supabase_service.py  # Работа с Supabase
│   └── openai_service.py    # Работа с OpenAI
├── handlers/
│   ├── command_handler.py   # Обработка команд
│   └── message_handler.py   # Обработка сообщений
├── utils/
│   └── report_generator.py  # Генерация отчетов
├── main.py                  # Главный файл
├── test_imports.py          # Тесты импортов
├── check_config.py          # Проверка конфигурации
├── test_token.py            # Тест токена бота
├── requirements.txt         # Зависимости
├── env_example.txt          # Пример переменных окружения
├── setup_supabase.sql       # SQL для настройки БД
├── SETUP.md                 # Подробная инструкция
└── README.md               # Документация
```

## 💰 Стоимость

### OpenAI Vision API:
- ~$0.01-0.03 за изображение
- Зависит от размера изображения

### Supabase:
- Бесплатный тариф: 500MB БД, 50K запросов/месяц
- $25/месяц при росте (50GB БД, 500K запросов)

## 🔧 Настройка и кастомизация

### Изменение целей питания
Отредактируйте значения в `config/settings.py`:

```python
DEFAULT_DAILY_CALORIES = 2000
DEFAULT_DAILY_PROTEIN = 150
DEFAULT_DAILY_FATS = 65
DEFAULT_DAILY_CARBS = 250
```

### Настройка промпта для OpenAI
Отредактируйте метод `_create_prompt()` в `services/openai_service.py`

## 🐛 Устранение неполадок

### Проверка установки
```bash
python test_imports.py
```

### Проверка конфигурации
```bash
python check_config.py
```

### Тестирование токена
```bash
python test_token.py
```

### Ошибка "Only timezones from the pytz library are supported"
✅ **РЕШЕНО**: Установлены правильные версии pytz и APScheduler

### Ошибка "Cannot close a running event loop"
✅ **РЕШЕНО**: Добавлена проверка токена и улучшена обработка ошибок

### Ошибка подключения к Supabase
- Проверьте правильность URL и ключа
- Убедитесь, что проект активен

### Ошибка анализа изображений
- 429 insufficient_quota: превышена квота OpenAI — пополните баланс/тариф
- Убедитесь в правильности API ключа

### Ошибки в логах
Проверьте логи приложения для детальной информации об ошибках.

## 🚀 Развертывание

### Локальный запуск
```bash
python main.py
```

### Запуск в фоне (Linux/Mac)
```bash
nohup python main.py > bot.log 2>&1 &
```

### Docker (опционально)
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "main.py"]
```

## 📝 Лицензия

MIT License

## 🤝 Поддержка

При возникновении проблем:

1. Запустите `python test_imports.py`
2. Запустите `python check_config.py`
3. Проверьте настройки в `.env`
4. Ознакомьтесь с [SETUP.md](SETUP.md)
5. Создайте issue в репозитории

## 🎉 Готово!

Ваш КБЖУ Анализатор готов к использованию! 

**Следующие шаги:**
1. Получите API ключи (см. SETUP.md)
2. Настройте Supabase (опционально)
3. Запустите бота: `python main.py`
4. Отправьте фото еды и получите анализ! 🍽️

## ✅ Статус разработки

- ✅ Все зависимости установлены
- ✅ Импорты работают корректно
- ✅ Конфигурация проверена
- ✅ Токен бота протестирован
- ✅ Готов к запуску
#   C a l o r i e A I 
 
 