# 💳 Настройка Telegram Payments для бота

## 🚀 Что нужно сделать:

### 1. **Создать платежного провайдера в @BotFather**

1. Отправьте `/mybots` в @BotFather
2. Выберите вашего бота
3. Нажмите "Payments"
4. Выберите провайдера (рекомендуется **Stripe** для международных платежей)
5. Следуйте инструкциям по настройке

### 2. **Получить платежные данные**

После настройки вы получите:
- `PAYMENT_PROVIDER_TOKEN` - токен для платежей
- `PAYMENT_PROVIDER_NAME` - название провайдера

### 3. **Добавить в .env файл**

```env
# Telegram Payments
PAYMENT_PROVIDER_TOKEN=your_payment_provider_token_here
PAYMENT_PROVIDER_NAME=stripe
```

### 4. **Обновить config/settings.py**

Добавьте в `config/settings.py`:

```python
# Telegram Payments
PAYMENT_PROVIDER_TOKEN = os.getenv("PAYMENT_PROVIDER_TOKEN")
PAYMENT_PROVIDER_NAME = os.getenv("PAYMENT_PROVIDER_NAME", "stripe")
```

### 5. **Интеграция в код**

В `handlers/command_handler.py` в методе `_handle_subscription_request`:

```python
# Создаем инвойс для оплаты
from telegram import LabeledPrice

prices = [LabeledPrice(plan['name'], int(plan['price'] * 100))]  # Цена в центах

await context.bot.send_invoice(
    chat_id=query.from_user.id,
    title=plan['name'],
    description=f"Подписка на {plan['duration_days']} дней",
    payload=f"subscription_{plan_type}",
    provider_token=settings.PAYMENT_PROVIDER_TOKEN,
    currency=plan['currency'],
    prices=prices,
    start_parameter="subscription_start"
)
```

### 6. **Обработка успешной оплаты**

Добавьте в `main.py`:

```python
from telegram.ext import PreCheckoutQueryHandler, MessageHandler, filters

# Обработка pre-checkout
application.add_handler(PreCheckoutQueryHandler(self.pre_checkout_handler))

# Обработка успешной оплаты
application.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, self.successful_payment_handler))
```

## 💰 Рекомендуемые провайдеры:

### **Stripe** (Рекомендуется)
- ✅ Поддерживает большинство стран
- ✅ Низкие комиссии (2.9% + $0.30)
- ✅ Простая интеграция
- ✅ Хорошая документация

### **ЮKassa** (Для России)
- ✅ Низкие комиссии для РФ
- ✅ Поддержка российских карт
- ❌ Только для резидентов РФ

### **Payme** (Для Узбекистана)
- ✅ Низкие комиссии для UZ
- ❌ Ограниченная география

## 🔧 Тестирование платежей:

### **Тестовые карты Stripe:**
- **Visa:** 4242 4242 4242 4242
- **Mastercard:** 5555 5555 5555 4444
- **Expiry:** Любая будущая дата
- **CVC:** Любые 3 цифры

### **Тестовый режим:**
- Всегда используйте тестовые ключи для разработки
- Переключайтесь на продакшн только после полного тестирования

## 📱 UX для пользователей:

### **После исчерпания бесплатного фото:**
1. Показываем планы подписки
2. Пользователь выбирает план
3. Создается инвойс для оплаты
4. После оплаты активируется подписка
5. Пользователь может анализировать неограниченное количество фото

### **Команды для управления подпиской:**
- `/subscription` - показать текущую подписку
- `/upgrade` - показать планы подписки
- `/cancel` - отменить подписку

## 🚨 Важные моменты:

1. **Безопасность:** Никогда не храните платежные данные в коде
2. **Тестирование:** Всегда тестируйте на тестовых картах
3. **Логирование:** Логируйте все платежные операции
4. **Обработка ошибок:** Обрабатывайте все возможные ошибки платежей
5. **Возвраты:** Продумайте политику возвратов

## 📞 Поддержка:

При возникновении проблем:
1. Проверьте логи бота
2. Убедитесь в правильности токенов
3. Проверьте настройки провайдера
4. Обратитесь в поддержку провайдера

---

**Готово!** После настройки ваш бот сможет принимать платежи за подписки! 🎉
