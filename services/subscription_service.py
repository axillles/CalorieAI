import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from models.data_models import Subscription, Payment, User
from services.supabase_service import SupabaseService
from services.stripe_service import StripeService
from config.settings import settings

logger = logging.getLogger(__name__)

class SubscriptionService:
    """Сервис для управления подписками через Stripe"""
    
    def __init__(self):
        self.supabase_service = SupabaseService()
        self.stripe_service = StripeService()
        
        # Планы подписок - получаем из StripeService
        self.subscription_plans = self.stripe_service.get_subscription_plans()
    
    async def can_analyze_photo(self, user_id: int) -> Dict[str, Any]:
        """Проверить, может ли пользователь анализировать фото"""
        try:
            user = await self.supabase_service.get_user_by_telegram_id(user_id)
            if not user:
                return {"can_analyze": False, "reason": "user_not_found"}
            
            # Проверяем активную подписку
            if user.subscription_status == "active":
                # Дополнительно проверяем, не истекла ли подписка
                if user.subscription_end and user.subscription_end < datetime.now():
                    # Обновляем статус подписки как истекшую
                    await self._update_subscription_status(user.id, "expired")
                    return {
                        "can_analyze": False, 
                        "reason": "subscription_expired",
                        "photos_analyzed": user.photos_analyzed,
                        "subscription_plans": self.subscription_plans
                    }
                return {"can_analyze": True, "reason": "active_subscription"}
            
            # Проверяем бесплатный лимит (первое фото бесплатно)
            if user.photos_analyzed < settings.FREE_PHOTO_LIMIT:
                return {"can_analyze": True, "reason": "free_photo"}
            
            return {
                "can_analyze": False, 
                "reason": "subscription_required",
                "photos_analyzed": user.photos_analyzed,
                "subscription_plans": self.subscription_plans
            }
            
        except Exception as e:
            logger.error(f"Ошибка проверки возможности анализа: {e}")
            return {"can_analyze": False, "reason": "error"}
    
    async def increment_photos_analyzed(self, user_id: int) -> bool:
        """Увеличить счетчик проанализированных фото"""
        try:
            # Получаем текущий счетчик
            user_result = self.supabase_service.supabase.table("users").select("photos_analyzed").eq("id", user_id).execute()
            
            if not user_result.data:
                logger.error(f"Пользователь {user_id} не найден")
                return False
            
            current_count = user_result.data[0]["photos_analyzed"]
            
            # Увеличиваем счетчик
            result = self.supabase_service.supabase.table("users").update({
                "photos_analyzed": current_count + 1
            }).eq("id", user_id).execute()
            
            return True
        except Exception as e:
            logger.error(f"Ошибка увеличения счетчика фото: {e}")
            return False
    
    async def create_payment_link(self, user_id: int, plan_type: str, telegram_user_id: int) -> Optional[str]:
        """Создать ссылку на оплату Stripe"""
        try:
            if plan_type not in self.subscription_plans:
                logger.error(f"Неизвестный план подписки: {plan_type}")
                return None
            
            # Создаем Checkout Session через StripeService
            payment_url = await self.stripe_service.create_checkout_session(
                user_id=user_id,
                plan_type=plan_type,
                telegram_user_id=telegram_user_id
            )
            
            if payment_url:
                logger.info(f"Создана ссылка на оплату для пользователя {user_id}: {plan_type}")
                return payment_url
            else:
                logger.error(f"Ошибка создания ссылки на оплату для пользователя {user_id}")
                return None
                
        except Exception as e:
            logger.error(f"Ошибка создания ссылки на оплату: {e}")
            return None
    
    async def get_user_subscription(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Получить информацию о подписке пользователя"""
        try:
            user = await self.supabase_service.get_user_by_telegram_id(user_id)
            if not user:
                return None
            
            # Если у пользователя есть Stripe подписка, получаем актуальную информацию
            if user.stripe_subscription_id:
                stripe_info = await self.stripe_service.get_subscription_info(user_id)
                if stripe_info:
                    return stripe_info
            
            # Иначе возвращаем информацию из нашей БД
            return {
                "status": user.subscription_status,
                "plan": user.subscription_plan,
                "photos_analyzed": user.photos_analyzed,
                "photos_limit": settings.FREE_PHOTO_LIMIT if user.subscription_status == "free" else -1,
                "subscription_start": user.subscription_start,
                "subscription_end": user.subscription_end
            }
            
        except Exception as e:
            logger.error(f"Ошибка получения подписки: {e}")
            return None
    
    async def cancel_subscription(self, user_id: int) -> bool:
        """Отменить подписку пользователя"""
        try:
            return await self.stripe_service.cancel_subscription(user_id)
        except Exception as e:
            logger.error(f"Ошибка отмены подписки: {e}")
            return False
    
    async def _update_subscription_status(self, user_id: int, status: str) -> bool:
        """Обновить статус подписки в БД"""
        try:
            result = self.supabase_service.supabase.table("users").update({
                "subscription_status": status
            }).eq("id", user_id).execute()
            
            return True
        except Exception as e:
            logger.error(f"Ошибка обновления статуса подписки: {e}")
            return False
    
    async def check_and_update_expired_subscriptions(self) -> int:
        """Проверить и обновить истекшие подписки"""
        try:
            # Получаем всех пользователей с активными подписками
            active_users = self.supabase_service.supabase.table("users").select("*").eq(
                "subscription_status", "active"
            ).execute()
            
            expired_count = 0
            current_time = datetime.now()
            
            for user_data in active_users.data:
                subscription_end = None
                if user_data.get("subscription_end"):
                    subscription_end = datetime.fromisoformat(user_data["subscription_end"].replace('Z', '+00:00'))
                
                # Проверяем истечение подписки
                if subscription_end and subscription_end < current_time:
                    await self._update_subscription_status(user_data["id"], "expired")
                    expired_count += 1
                    logger.info(f"Подписка истекла для пользователя {user_data['id']}")
            
            return expired_count
            
        except Exception as e:
            logger.error(f"Ошибка проверки истекших подписок: {e}")
            return 0
    
    def get_subscription_plans(self) -> Dict[str, Any]:
        """Получить доступные планы подписок"""
        return self.subscription_plans
    
    async def reset_photos_limit_for_new_billing_period(self, user_id: int) -> bool:
        """Сбросить лимит фото для нового расчетного периода (при продлении подписки)"""
        try:
            result = self.supabase_service.supabase.table("users").update({
                "photos_analyzed": 0
            }).eq("id", user_id).execute()
            
            logger.info(f"Сброшен счетчик фото для пользователя {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка сброса счетчика фото: {e}")
            return False
