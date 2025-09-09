import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from models.data_models import Subscription, Payment, User
from services.supabase_service import SupabaseService
from config.settings import settings

# Импортируем сервисы платежей
try:
    from services.stripe_service import StripeService
except ImportError:
    StripeService = None

try:
    from services.paypal_service import PayPalService
except ImportError:
    PayPalService = None

try:
    from services.telegram_stars_service import TelegramStarsService
except ImportError:
    TelegramStarsService = None

try:
    from services.telegram_payments_service import TelegramPaymentsService
except ImportError:
    TelegramPaymentsService = None

logger = logging.getLogger(__name__)

class SubscriptionService:
    """Сервис для управления подписками через разные провайдеры"""
    
    def __init__(self):
        self.supabase_service = SupabaseService()
        
        # Инициализируем доступные провайдеры
        self.payment_providers = {}
        
        # Telegram Stars
        if TelegramStarsService and "telegram_stars" in settings.ENABLED_PAYMENT_PROVIDERS:
            self.payment_providers["telegram_stars"] = TelegramStarsService()
            
        # Telegram Payments (Redsys via BotFather)
        if TelegramPaymentsService and "telegram_payments" in settings.ENABLED_PAYMENT_PROVIDERS:
            self.payment_providers["telegram_payments"] = TelegramPaymentsService()

        # Убираем PayPal и Stripe из доступных провайдеров
        
        # Определяем основной провайдер
        self.primary_provider = settings.PRIMARY_PAYMENT_PROVIDER
        if self.primary_provider not in self.payment_providers:
            # Если основной недоступен, берем первый доступный
            # Принудительно используем telegram_payments, если он доступен
            if "telegram_payments" in self.payment_providers:
                self.primary_provider = "telegram_payments"
            else:
                self.primary_provider = list(self.payment_providers.keys())[0] if self.payment_providers else None
        
        # Планы подписок - получаем из основного провайдера
        if self.primary_provider and self.primary_provider in self.payment_providers:
            self.subscription_plans = self.payment_providers[self.primary_provider].get_subscription_plans()
        else:
            # Запасные планы
            self.subscription_plans = {
                "monthly": {
                    "name": "Месячная подписка",
                    "price": 4.99,
                    "currency": "USD",
                    "duration_days": 30,
                    "photos_limit": -1
                },
                "yearly": {
                    "name": "Годовая подписка",
                    "price": 49.99,
                    "currency": "USD",
                    "duration_days": 365,
                    "photos_limit": -1
                }
            }
    
    async def can_analyze_photo(self, user_id: int) -> Dict[str, Any]:
        """Проверить, может ли пользователь анализировать фото"""
        try:
            logger.info(f"🔍 Проверка подписки для telegram_id: {user_id}")
            
            user = await self.supabase_service.get_user_by_telegram_id(user_id)
            if not user:
                logger.warning(f"⚠️ Пользователь {user_id} не найден в БД")
                return {"can_analyze": False, "reason": "user_not_found"}
            
            logger.info(f"✅ Пользователь найден: db_id={user.id}")
            
            # Проверяем активную подписку (с fallback для отсутствующих полей)
            subscription_status = getattr(user, 'subscription_status', 'free')
            subscription_end = getattr(user, 'subscription_end', None)
            photos_analyzed = getattr(user, 'photos_analyzed', 0)
            
            logger.info(f"📊 Статистика: status={subscription_status}, photos_analyzed={photos_analyzed}, limit={settings.FREE_PHOTO_LIMIT}")
            
            if subscription_status == "active":
                # Дополнительно проверяем, не истекла ли подписка
                if subscription_end:
                    try:
                        if isinstance(subscription_end, str):
                            end_date = datetime.fromisoformat(subscription_end.replace('Z', '+00:00'))
                        else:
                            end_date = subscription_end
                        
                        if end_date < datetime.now():
                            # Обновляем статус подписки как истекшую
                            await self._update_subscription_status(user.id, "expired")
                            return {
                                "can_analyze": False, 
                                "reason": "subscription_expired",
                                "photos_analyzed": photos_analyzed,
                                "subscription_plans": self.subscription_plans
                            }
                    except Exception as e:
                        logger.warning(f"Ошибка проверки даты окончания подписки: {e}")
                
                return {"can_analyze": True, "reason": "active_subscription"}
            
            # Проверяем бесплатный лимит (первое фото бесплатно)
            if photos_analyzed < settings.FREE_PHOTO_LIMIT:
                logger.info(f"✅ Бесплатное фото разрешено: {photos_analyzed}/{settings.FREE_PHOTO_LIMIT}")
                return {"can_analyze": True, "reason": "free_photo"}
            
            logger.info(f"⚠️ Лимит бесплатных фото исчерпан: {photos_analyzed}/{settings.FREE_PHOTO_LIMIT}")
            return {
                "can_analyze": False, 
                "reason": "subscription_required",
                "photos_analyzed": photos_analyzed,
                "subscription_plans": self.subscription_plans
            }
            
        except Exception as e:
            logger.error(f"Ошибка проверки возможности анализа: {e}")
            # В случае ошибки разрешаем бесплатное фото для отладки
            return {"can_analyze": True, "reason": "error_fallback"}
    
    async def increment_photos_analyzed(self, telegram_user_id: int) -> bool:
        """Увеличить счетчик проанализированных фото"""
        try:
            # Получаем текущий счетчик по telegram_id
            user_result = self.supabase_service.supabase.table("users").select("id, photos_analyzed").eq("telegram_id", telegram_user_id).execute()
            
            if not user_result.data:
                logger.error(f"Пользователь {telegram_user_id} не найден")
                return False
            
            user_data = user_result.data[0]
            current_count = user_data.get("photos_analyzed", 0)
            
            # Увеличиваем счетчик
            result = self.supabase_service.supabase.table("users").update({
                "photos_analyzed": current_count + 1
            }).eq("id", user_data["id"]).execute()
            
            return True
        except Exception as e:
            logger.error(f"Ошибка увеличения счетчика фото: {e}")
            return False
    
    async def create_payment_link(self, user_id: int, plan_type: str, telegram_user_id: int, provider: str = None) -> Optional[str]:
        """Создать ссылку на оплату через указанный провайдер"""
        try:
            if plan_type not in self.subscription_plans:
                logger.error(f"Неизвестный план подписки: {plan_type}")
                return None
            
            # Определяем провайдер
            if not provider:
                provider = self.primary_provider
            
            if provider not in self.payment_providers:
                logger.error(f"Провайдер {provider} недоступен")
                return None
            
            # Создаем платеж через соответствующий сервис
            payment_service = self.payment_providers[provider]
            
            if provider == "stripe":
                payment_url = await payment_service.create_checkout_session(
                    user_id=user_id,
                    plan_type=plan_type,
                    telegram_user_id=telegram_user_id
                )
            elif provider == "paypal":
                payment_url = await payment_service.create_subscription_payment(
                    user_id=user_id,
                    plan_type=plan_type,
                    telegram_user_id=telegram_user_id
                )
            elif provider == "telegram_stars":
                # Для Telegram Stars нет прямой ссылки - они обрабатываются через инвойс
                return "telegram_stars_invoice_required"
            else:
                logger.error(f"Неподдерживаемый провайдер: {provider}")
                return None
            
            if payment_url:
                logger.info(f"Создана ссылка на оплату {provider} для пользователя {user_id}: {plan_type}")
                return payment_url
            else:
                logger.error(f"Ошибка создания ссылки на оплату {provider} для пользователя {user_id}")
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
    
    def get_available_providers(self) -> List[str]:
        """Получить список доступных провайдеров"""
        return list(self.payment_providers.keys())
    
    def get_provider_display_name(self, provider: str) -> str:
        """Получить отображаемое имя провайдера"""
        names = {
            "telegram_stars": "⭐ Telegram Stars",
            "telegram_payments": "💳 Telegram Payments (Redsys)",
        }
        return names.get(provider, provider.title())
    
    def get_payment_service(self, provider: str):
        """Получить сервис для указанного провайдера"""
        return self.payment_providers.get(provider)
    
    async def _activate_subscription(self, user_id: int, plan_type: str, provider: str, provider_payment_id: str) -> bool:
        """Активировать подписку для пользователя"""
        try:
            from datetime import datetime, timedelta
            
            plan = self.subscription_plans.get(plan_type)
            if not plan:
                logger.error(f"Неизвестный план: {plan_type}")
                return False
            
            # Рассчитываем даты подписки
            start_date = datetime.now()
            end_date = start_date + timedelta(days=plan['duration_days'])
            
            # Обновляем пользователя в БД
            result = self.supabase_service.supabase.table("users").update({
                "subscription_status": "active",
                "subscription_plan": plan_type,
                "subscription_start": start_date.isoformat(),
                "subscription_end": end_date.isoformat(),
                "payment_provider": provider,
                "provider_payment_id": provider_payment_id,
                "photos_analyzed": 0  # Сбрасываем счетчик фото
            }).eq("id", user_id).execute()
            
            if result.data:
                logger.info(f"Подписка активирована для пользователя {user_id}: {plan_type} через {provider}")
                return True
            else:
                logger.error(f"Ошибка активации подписки для пользователя {user_id}")
                return False
                
        except Exception as e:
            logger.error(f"Ошибка активации подписки: {e}")
            return False
