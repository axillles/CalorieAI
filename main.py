import asyncio
import logging
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from config.settings import settings
from handlers.command_handler import CommandHandler as BotCommandHandler
from handlers.message_handler import MessageHandler as BotMessageHandler
from services.subscription_monitor import SubscriptionMonitor
from telegram import Update
import threading
import uvicorn

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def main():
    """Главная функция приложения"""
    try:
        # Проверяем наличие необходимых переменных окружения
        if not settings.TELEGRAM_BOT_TOKEN or settings.TELEGRAM_BOT_TOKEN == "your_telegram_bot_token_here":
            logger.error("TELEGRAM_BOT_TOKEN не установлен или установлен неправильно")
            logger.info("Создайте файл .env и добавьте TELEGRAM_BOT_TOKEN=your_real_token_here")
            logger.info("Получите токен у @BotFather в Telegram")
            return
        
        if not settings.OPENAI_API_KEY or settings.OPENAI_API_KEY == "your_openai_api_key_here":
            logger.error("OPENAI_API_KEY не установлен или установлен неправильно")
            logger.info("Создайте файл .env и добавьте OPENAI_API_KEY=your_real_key_here")
            logger.info("Получите ключ на https://platform.openai.com/api-keys")
            return
        
        if not settings.SUPABASE_URL or settings.SUPABASE_URL == "https://your-project-id.supabase.co":
            logger.warning("SUPABASE_URL не установлен или установлен неправильно")
            logger.info("Бот будет работать без базы данных (только анализ изображений)")
            logger.info("Для полной функциональности настройте Supabase")
        
        if not settings.SUPABASE_KEY or settings.SUPABASE_KEY == "your_supabase_anon_key_here":
            logger.warning("SUPABASE_KEY не установлен или установлен неправильно")
            logger.info("Бот будет работать без базы данных (только анализ изображений)")
        
        # Check payment provider settings
        enabled_providers = settings.ENABLED_PAYMENT_PROVIDERS
        
        # Only check Stripe if it's enabled
        if "stripe" in enabled_providers:
            if not settings.STRIPE_SECRET_KEY:
                logger.warning("STRIPE_SECRET_KEY не установлен, Stripe будет отключен")
            
            if not settings.STRIPE_WEBHOOK_SECRET:
                logger.warning("STRIPE_WEBHOOK_SECRET не установлен")
                logger.info("Для работы веб-хуков Stripe добавьте STRIPE_WEBHOOK_SECRET в .env")
            
            if not settings.STRIPE_PRICE_ID_MONTHLY or not settings.STRIPE_PRICE_ID_YEARLY:
                logger.warning("Не настроены Price ID для планов подписок Stripe")
                logger.info("Добавьте STRIPE_PRICE_ID_MONTHLY и STRIPE_PRICE_ID_YEARLY в .env")
        
        # Check PayPal if enabled
        if "paypal" in enabled_providers:
            if not settings.PAYPAL_CLIENT_ID or not settings.PAYPAL_CLIENT_SECRET:
                logger.warning("PayPal credentials не настроены")
                logger.info("Добавьте PAYPAL_CLIENT_ID и PAYPAL_CLIENT_SECRET в .env")
        
        logger.info(f"Включенные провайдеры платежей: {', '.join(enabled_providers)}")
        
        # Создаем экземпляры обработчиков
        command_handler = BotCommandHandler()
        message_handler = BotMessageHandler()
        
        # Инициализируем мониторинг подписок
        subscription_monitor = SubscriptionMonitor()
        
        # Запускаем веб-хук сервер в отдельном потоке
        import os
        def run_webhook_server():
            try:
                from webhook_server import webhook_app
                port = int(os.getenv("PORT", 8001))
                uvicorn.run(webhook_app, host="0.0.0.0", port=port, log_level="info")
            except Exception as e:
                logger.error(f"Ошибка запуска веб-хук сервера: {e}")
        
        webhook_thread = threading.Thread(target=run_webhook_server, daemon=True)
        webhook_thread.start()
        logger.info("Веб-хук сервер запущен")
        
        # Небольшая задержка для запуска веб-хук сервера
        import time
        time.sleep(2)
        
        # Создаем приложение без JobQueue для избежания проблем с pytz
        application = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).job_queue(None).build()
        
        # Регистрируем обработчики команд
        application.add_handler(CommandHandler("start", command_handler.start_command))
        application.add_handler(CommandHandler("help", command_handler.help_command))
        application.add_handler(CommandHandler("stats", command_handler.stats_command))
        application.add_handler(CommandHandler("week", command_handler.week_command))
        
        # Callback-кнопки
        from telegram.ext import CallbackQueryHandler, PreCheckoutQueryHandler
        application.add_handler(CallbackQueryHandler(command_handler.callback_query_handler))
        
        # Обработчики платежей Telegram Stars
        application.add_handler(PreCheckoutQueryHandler(command_handler.handle_pre_checkout_query))
        application.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, command_handler.handle_successful_payment))
        
        # Регистрируем обработчики сообщений
        application.add_handler(MessageHandler(filters.PHOTO, message_handler.handle_photo))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler.handle_text))
        
        # Запускаем мониторинг подписок
        subscription_monitor.start_monitoring()
        
        try:
            # Запускаем бота
            logger.info("Запуск бота...")
            logger.info("Бот готов к работе! Отправьте /start в Telegram для начала.")
            logger.info(f"Веб-хук URL: {settings.APP_URL}/webhook/stripe")
            await application.run_polling(allowed_updates=Update.ALL_TYPES, close_loop=False)
        finally:
            # Останавливаем мониторинг при завершении
            subscription_monitor.stop_monitoring()
        
    except Exception as e:
        logger.error(f"Ошибка запуска приложения: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Исправление для Windows и Python 3.13
    try:
        asyncio.run(main())
    except RuntimeError as e:
        if "event loop is already running" in str(e):
            # Если event loop уже запущен, используем другой подход
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(main())
            finally:
                loop.close()
        else:
            raise
