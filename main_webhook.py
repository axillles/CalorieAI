"""
Основной файл для запуска в Railway с веб-хук сервером как основным процессом
"""
import asyncio
import logging
import threading
import time
import os
from webhook_server import webhook_app
import uvicorn
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from config.settings import settings
from handlers.command_handler import CommandHandler as BotCommandHandler
from handlers.message_handler import MessageHandler as BotMessageHandler
from services.subscription_monitor import SubscriptionMonitor
from telegram import Update

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def run_telegram_bot():
    """Запуск Telegram бота в отдельном потоке"""
    try:
        # Проверяем наличие необходимых переменных окружения
        logger.info(f"🔑 TELEGRAM_BOT_TOKEN: {'установлен' if settings.TELEGRAM_BOT_TOKEN and settings.TELEGRAM_BOT_TOKEN != 'your_telegram_bot_token_here' else 'НЕ УСТАНОВЛЕН'}")
        logger.info(f"🔑 OPENAI_API_KEY: {'установлен' if settings.OPENAI_API_KEY and settings.OPENAI_API_KEY != 'your_openai_api_key_here' else 'НЕ УСТАНОВЛЕН'}")
        logger.info(f"🔑 SUPABASE_URL: {'установлен' if settings.SUPABASE_URL and settings.SUPABASE_URL != 'https://your-project-id.supabase.co' else 'НЕ УСТАНОВЛЕН'}")
        
        if not settings.TELEGRAM_BOT_TOKEN or settings.TELEGRAM_BOT_TOKEN == "your_telegram_bot_token_here":
            logger.error("❌ TELEGRAM_BOT_TOKEN не установлен")
            return
        
        if not settings.OPENAI_API_KEY or settings.OPENAI_API_KEY == "your_openai_api_key_here":
            logger.error("❌ OPENAI_API_KEY не установлен")
            return
        
        logger.info("Запуск Telegram бота...")
        
        # Создаем экземпляры обработчиков
        command_handler = BotCommandHandler()
        message_handler = BotMessageHandler()
        
        # Инициализируем мониторинг подписок
        subscription_monitor = SubscriptionMonitor()
        
        # Создаем приложение без JobQueue
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
            logger.info("Бот готов к работе!")
            await application.run_polling(allowed_updates=Update.ALL_TYPES, close_loop=False)
        finally:
            # Останавливаем мониторинг при завершении
            subscription_monitor.stop_monitoring()
            
    except Exception as e:
        logger.error(f"Ошибка запуска Telegram бота: {e}")
        import traceback
        traceback.print_exc()

def start_telegram_bot():
    """Запуск Telegram бота в отдельном потоке"""
    def run_bot():
        try:
            # Исправление для Windows и Python 3.13
            try:
                asyncio.run(run_telegram_bot())
            except RuntimeError as e:
                if "event loop is already running" in str(e):
                    # Если event loop уже запущен, используем другой подход
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        loop.run_until_complete(run_telegram_bot())
                    finally:
                        loop.close()
                else:
                    raise
        except Exception as e:
            logger.error(f"Ошибка в потоке Telegram бота: {e}")
            logger.info("Веб-хук сервер продолжит работать без Telegram бота")
    
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    logger.info("Telegram бот запущен в отдельном потоке")

if __name__ == "__main__":
    logger.info("🚀 Запуск веб-хук сервера с Telegram ботом...")
    
    # Запускаем веб-хук сервер как основной процесс СНАЧАЛА
    port = int(os.getenv("PORT", 8001))
    logger.info(f"🌐 Запуск веб-хук сервера на порту {port}")
    logger.info(f"🔗 Health check будет доступен по адресу: http://0.0.0.0:{port}/health")
    
    # Запускаем Telegram бот в отдельном потоке
    start_telegram_bot()
    
    try:
        uvicorn.run(
            webhook_app, 
            host="0.0.0.0", 
            port=port, 
            log_level="info",
            access_log=True
        )
    except Exception as e:
        logger.error(f"❌ Ошибка запуска веб-хук сервера: {e}")
        import traceback
        traceback.print_exc()
