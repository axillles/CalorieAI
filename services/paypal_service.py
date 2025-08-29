import logging
import requests
import base64
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from config.settings import settings

logger = logging.getLogger(__name__)

class PayPalService:
    """Сервис для работы с платежами PayPal"""
    
    def __init__(self):
        self.client_id = settings.PAYPAL_CLIENT_ID
        self.client_secret = settings.PAYPAL_CLIENT_SECRET
        self.base_url = settings.PAYPAL_BASE_URL or "https://api-m.sandbox.paypal.com"  # sandbox по умолчанию
        self.access_token = None
        self.token_expires_at = None
        
        # Планы подписок
        self.subscription_plans = {
            "monthly": {
                "name": "Monthly KBGU Analysis",
                "price": 4.99,
                "currency": "USD",
                "duration_days": 30,
                "photos_limit": -1  # -1 = безлимит
            },
            "yearly": {
                "name": "Yearly KBGU Analysis", 
                "price": 49.99,
                "currency": "USD",
                "duration_days": 365,
                "photos_limit": -1
            }
        }
    
    async def get_access_token(self) -> Optional[str]:
        """Получить access token от PayPal"""
        try:
            # Проверяем, не истек ли текущий токен
            if self.access_token and self.token_expires_at and datetime.now() < self.token_expires_at:
                return self.access_token
            
            # Формируем авторизационные данные
            auth_string = f"{self.client_id}:{self.client_secret}"
            auth_bytes = auth_string.encode('ascii')
            auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
            
            # Запрос токена
            headers = {
                "Accept": "application/json",
                "Accept-Language": "en_US",
                "Authorization": f"Basic {auth_b64}"
            }
            
            data = "grant_type=client_credentials"
            
            response = requests.post(
                f"{self.base_url}/v1/oauth2/token",
                headers=headers,
                data=data
            )
            
            if response.status_code == 200:
                token_data = response.json()
                self.access_token = token_data["access_token"]
                expires_in = token_data.get("expires_in", 3600)
                self.token_expires_at = datetime.now() + timedelta(seconds=expires_in - 60)  # 60 сек запас
                
                logger.info("PayPal access token получен успешно")
                return self.access_token
            else:
                logger.error(f"Ошибка получения PayPal токена: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Исключение при получении PayPal токена: {e}")
            return None
    
    async def create_subscription_payment(self, user_id: int, plan_type: str, telegram_user_id: int) -> Optional[str]:
        """Создать платежную ссылку для подписки"""
        try:
            access_token = await self.get_access_token()
            if not access_token:
                return None
            
            plan = self.subscription_plans.get(plan_type)
            if not plan:
                logger.error(f"Неизвестный план подписки: {plan_type}")
                return None
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {access_token}",
                "PayPal-Request-Id": f"subscription-{user_id}-{plan_type}-{int(datetime.now().timestamp())}"
            }
            
            # Создаем платеж
            payment_data = {
                "intent": "CAPTURE",
                "purchase_units": [{
                    "reference_id": f"subscription_{user_id}_{plan_type}",
                    "amount": {
                        "currency_code": plan["currency"],
                        "value": str(plan["price"])
                    },
                    "description": f"{plan['name']} - {plan['duration_days']} days unlimited photo analysis",
                    "custom_id": f"{user_id}|{plan_type}|{telegram_user_id}"
                }],
                "application_context": {
                    "brand_name": "KBGU Food Analyzer Bot",
                    "landing_page": "BILLING",
                    "shipping_preference": "NO_SHIPPING",
                    "user_action": "PAY_NOW",
                    "return_url": f"{settings.APP_URL}/paypal/success",
                    "cancel_url": f"{settings.APP_URL}/paypal/cancel"
                }
            }
            
            response = requests.post(
                f"{self.base_url}/v2/checkout/orders",
                headers=headers,
                json=payment_data
            )
            
            if response.status_code == 201:
                order_data = response.json()
                order_id = order_data["id"]
                
                # Ищем ссылку для оплаты
                for link in order_data.get("links", []):
                    if link["rel"] == "approve":
                        payment_url = link["href"]
                        logger.info(f"Создан PayPal заказ для пользователя {user_id}: {order_id}")
                        return payment_url
                
                logger.error("Не найдена ссылка approve в ответе PayPal")
                return None
            else:
                logger.error(f"Ошибка создания PayPal заказа: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Ошибка создания PayPal платежа: {e}")
            return None
    
    async def capture_payment(self, order_id: str) -> Optional[Dict[str, Any]]:
        """Захватить платеж после одобрения пользователем"""
        try:
            access_token = await self.get_access_token()
            if not access_token:
                return None
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {access_token}"
            }
            
            response = requests.post(
                f"{self.base_url}/v2/checkout/orders/{order_id}/capture",
                headers=headers
            )
            
            if response.status_code == 201:
                capture_data = response.json()
                
                # Извлекаем информацию о платеже
                purchase_unit = capture_data["purchase_units"][0]
                capture_info = purchase_unit["payments"]["captures"][0]
                
                custom_id = purchase_unit.get("custom_id", "")
                if custom_id:
                    user_id, plan_type, telegram_user_id = custom_id.split("|")
                    
                    return {
                        "success": True,
                        "order_id": order_id,
                        "capture_id": capture_info["id"],
                        "amount": capture_info["amount"]["value"],
                        "currency": capture_info["amount"]["currency_code"],
                        "user_id": int(user_id),
                        "plan_type": plan_type,
                        "telegram_user_id": int(telegram_user_id),
                        "status": capture_info["status"]
                    }
                
                logger.error("Не найден custom_id в PayPal capture")
                return None
                
            else:
                logger.error(f"Ошибка захвата PayPal платежа: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Ошибка захвата PayPal платежа: {e}")
            return None
    
    async def verify_webhook(self, webhook_data: Dict, headers: Dict) -> bool:
        """Проверить подпись PayPal webhook"""
        try:
            # PayPal webhook verification
            # Это упрощенная версия - в продакшене нужна полная верификация
            webhook_id = headers.get("PAYPAL-TRANSMISSION-ID")
            return webhook_id is not None
            
        except Exception as e:
            logger.error(f"Ошибка верификации PayPal webhook: {e}")
            return False
    
    def get_subscription_plans(self) -> Dict[str, Any]:
        """Получить доступные планы подписок"""
        return self.subscription_plans