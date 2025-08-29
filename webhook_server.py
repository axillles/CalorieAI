import stripe
import uvicorn
import logging
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from config.settings import settings
from services.stripe_service import StripeService

logger = logging.getLogger(__name__)

# Создаем FastAPI приложение для веб-хуков
webhook_app = FastAPI()

stripe_service = StripeService()

@webhook_app.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    """Обработчик веб-хуков Stripe"""
    payload = await request.body()
    sig_header = request.headers.get('stripe-signature')
    
    if not sig_header:
        logger.error("Отсутствует заголовок Stripe Signature")
        raise HTTPException(status_code=400, detail="Missing signature")
    
    try:
        # Проверяем подпись веб-хука
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        logger.error(f"Неверный payload: {e}")
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError as e:
        logger.error(f"Неверная подпись веб-хука: {e}")
        raise HTTPException(status_code=400, detail="Invalid signature")
    
    # Обрабатываем событие
    event_type = event['type']
    event_data = event['data']['object']
    
    try:
        if event_type == 'checkout.session.completed':
            # Успешная оплата
            await handle_checkout_completed(event_data)
            
        elif event_type == 'customer.subscription.updated':
            # Обновление подписки (продление, изменение статуса)
            await handle_subscription_updated(event_data)
            
        elif event_type == 'customer.subscription.deleted':
            # Отмена подписки
            await handle_subscription_deleted(event_data)
            
        elif event_type == 'invoice.payment_failed':
            # Неудачная оплата
            await handle_payment_failed(event_data)
            
        else:
            logger.info(f"Неизвестный тип события: {event_type}")
    
    except Exception as e:
        logger.error(f"Ошибка обработки веб-хука {event_type}: {e}")
        raise HTTPException(status_code=500, detail="Webhook processing error")
    
    return JSONResponse(content={"status": "success"})

async def handle_checkout_completed(session_data):
    """Обработать завершение оплаты"""
    session_id = session_data['id']
    logger.info(f"Обработка завершения оплаты для сессии: {session_id}")
    
    success = await stripe_service.handle_successful_payment(session_id)
    if not success:
        logger.error(f"Ошибка активации подписки для сессии {session_id}")

async def handle_subscription_updated(subscription_data):
    """Обработать обновление подписки"""
    subscription_id = subscription_data['id']
    status = subscription_data['status']
    logger.info(f"Обработка обновления подписки {subscription_id}: {status}")
    
    await stripe_service.handle_subscription_updated(subscription_data)

async def handle_subscription_deleted(subscription_data):
    """Обработать удаление подписки"""
    subscription_id = subscription_data['id']
    logger.info(f"Обработка удаления подписки: {subscription_id}")
    
    # Помечаем подписку как отмененную
    subscription_data['status'] = 'canceled'
    await stripe_service.handle_subscription_updated(subscription_data)

async def handle_payment_failed(invoice_data):
    """Обработать неудачную оплату"""
    subscription_id = invoice_data.get('subscription')
    logger.warning(f"Неудачная оплата для подписки: {subscription_id}")
    
    # Можно добавить логику для уведомления пользователя
    # о проблемах с оплатой

@webhook_app.get("/health")
async def health_check():
    """Проверка состояния веб-хук сервера"""
    return {"status": "ok"}

def run_webhook_server(host="0.0.0.0", port=8001):
    """Запустить сервер веб-хуков"""
    logger.info(f"Запуск сервера веб-хуков на {host}:{port}")
    uvicorn.run(webhook_app, host=host, port=port)

if __name__ == "__main__":
    run_webhook_server()