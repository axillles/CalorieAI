#!/usr/bin/env python3
"""
Альтернативный способ запуска бота для Windows с исправленной обработкой event loop
"""

import asyncio
import logging
import sys
import os
import nest_asyncio
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from config.settings import settings
from handlers.command_handler import CommandHandler as BotCommandHandler
from handlers.message_handler import MessageHandler as BotMessageHandler
from telegram import Update

# Применяем nest_asyncio для решения проблем с event loop
nest_asyncio.apply()

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
        logger.info(f"Включенные провайдеры платежей: {', '.join(enabled_providers)}")
        
        # Only check Stripe if it's enabled
        if "stripe" in enabled_providers:
            if not settings.STRIPE_SECRET_KEY:
                logger.warning("STRIPE_SECRET_KEY не установлен, Stripe будет отключен")
        
        # Check PayPal if enabled
        if "paypal" in enabled_providers:
            if not settings.PAYPAL_CLIENT_ID or not settings.PAYPAL_CLIENT_SECRET:
                logger.warning("PayPal credentials не настроены")
                logger.info("Добавьте PAYPAL_CLIENT_ID и PAYPAL_CLIENT_SECRET в .env")
        
        # Telegram Stars работает автоматически
        if "telegram_stars" in enabled_providers:
            logger.info("✅ Telegram Stars включен и готов к работе")
        
        # Создаем экземпляры обработчиков
        command_handler = BotCommandHandler()
        message_handler = BotMessageHandler()
        
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
        logger.info("✅ CallbackQueryHandler зарегистрирован")
        
        # Обработчики платежей Telegram Stars
        application.add_handler(PreCheckoutQueryHandler(command_handler.handle_pre_checkout_query))
        application.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, command_handler.handle_successful_payment))
        logger.info("✅ Telegram Stars payment handlers зарегистрированы")
        
        # Регистрируем обработчики сообщений
        application.add_handler(MessageHandler(filters.PHOTO, message_handler.handle_photo))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler.handle_text))
        logger.info("✅ MessageHandler зарегистрирован")
        
        # Запускаем бота
        logger.info("🚀 Запуск бота...")
        logger.info("✅ Бот готов к работе! Отправьте /start в Telegram для начала.")
        logger.info("🔘 Callback-кнопки активны и готовы к работе")
        
        # Используем start_polling вместо run_polling
        await application.initialize()
        await application.start()
        await application.updater.start_polling()
        
        # Ждем завершения
        try:
            await asyncio.Event().wait()  # Бесконечное ожидание
        except KeyboardInterrupt:
            logger.info("Получен сигнал остановки...")
        finally:
            await application.updater.stop()
            await application.stop()
            await application.shutdown()
        
    except Exception as e:
        logger.error(f"Ошибка запуска приложения: {e}")
        import traceback
        traceback.print_exc()

def run_bot():
    """Функция для запуска бота с правильной обработкой event loop"""
    if sys.platform == "win32":
        # Для Windows используем ProactorEventLoop
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    try:
        # Создаем новый event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Запускаем main в новом loop
        loop.run_until_complete(main())
        
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
    finally:
        try:
            # Закрываем loop
            pending = asyncio.all_tasks(loop)
            loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
            loop.close()
        except:
            pass

if __name__ == "__main__":
    run_bot()
