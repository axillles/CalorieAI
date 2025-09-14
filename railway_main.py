#!/usr/bin/env python3
"""
Основной файл для Railway с приоритетом веб-сервера
"""
import asyncio
import logging
import threading
import time
import os
from fastapi import FastAPI
import uvicorn

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Создаем FastAPI приложение
app = FastAPI()

@app.get("/health")
async def health_check():
    """Проверка состояния сервера"""
    return {"status": "ok", "message": "TGCal Server is running"}

@app.get("/")
async def root():
    """Корневой endpoint"""
    return {"message": "TGCal Webhook Server", "health": "/health"}

def start_telegram_bot():
    """Запуск Telegram бота в отдельном потоке"""
    def run_bot():
        try:
            # Импортируем только когда нужно
            from main_webhook import run_telegram_bot
            # Создаем новый event loop для потока
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(run_telegram_bot())
            finally:
                loop.close()
        except Exception as e:
            logger.error(f"Ошибка запуска Telegram бота: {e}")
            logger.info("Веб-сервер продолжит работать без Telegram бота")
    
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    logger.info("Telegram бот запущен в отдельном потоке")

if __name__ == "__main__":
    logger.info("🚀 Запуск TGCal сервера...")
    
    # Запускаем веб-сервер как основной процесс
    port = int(os.getenv("PORT", 8001))
    logger.info(f"🌐 Запуск веб-сервера на порту {port}")
    logger.info(f"🔗 Health check: http://0.0.0.0:{port}/health")
    
    # Запускаем Telegram бот в отдельном потоке
    start_telegram_bot()
    
    try:
        uvicorn.run(
            app, 
            host="0.0.0.0", 
            port=port, 
            log_level="info",
            access_log=True
        )
    except Exception as e:
        logger.error(f"❌ Ошибка запуска веб-сервера: {e}")
        import traceback
        traceback.print_exc()
