import uvicorn
import logging
from fastapi import FastAPI

logger = logging.getLogger(__name__)

# Создаем FastAPI приложение для веб-хуков
webhook_app = FastAPI()

@webhook_app.get("/health")
async def health_check():
    """Проверка состояния веб-хук сервера"""
    return {"status": "ok", "message": "TGCal Webhook Server is running"}

@webhook_app.get("/")
async def root():
    """Корневой endpoint"""
    return {"message": "TGCal Webhook Server", "health": "/health"}

def run_webhook_server(host="0.0.0.0", port=8001):
    """Запустить сервер веб-хуков"""
    logger.info(f"Запуск сервера веб-хуков на {host}:{port}")
    uvicorn.run(webhook_app, host=host, port=port)

if __name__ == "__main__":
    run_webhook_server()