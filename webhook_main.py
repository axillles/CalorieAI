"""
Отдельный запуск веб-хук сервера для Railway
"""
import uvicorn
import logging
import os
from webhook_server import webhook_app

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logger.info("Запуск веб-хук сервера для Railway")
    uvicorn.run(
        webhook_app, 
        host="0.0.0.0", 
        port=int(os.getenv("PORT", 8001)),
        log_level="info"
    )
