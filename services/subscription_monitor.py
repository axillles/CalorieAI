import asyncio
import logging
from datetime import datetime, timedelta
from services.subscription_service import SubscriptionService
from services.stripe_service import StripeService
from services.supabase_service import SupabaseService
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import stripe

logger = logging.getLogger(__name__)

class SubscriptionMonitor:
    """Сервис для мониторинга и проверки подписок"""
    
    def __init__(self):
        self.subscription_service = SubscriptionService()
        self.stripe_service = StripeService()
        self.supabase_service = SupabaseService()
        self.scheduler = AsyncIOScheduler()
        
    def start_monitoring(self):
        """Запустить мониторинг подписок"""
        logger.info("Запуск мониторинга подписок...")
        
        # Проверяем подписки каждый час
        self.scheduler.add_job(
            self.check_subscription_status,
            CronTrigger(minute=0),  # Каждый час в начале часа
            id='subscription_status_check',
            name='Проверка статуса подписок',
            replace_existing=True
        )
        
        # Синхронизируем с Stripe каждые 6 часов
        self.scheduler.add_job(
            self.sync_with_stripe,
            CronTrigger(hour='*/6'),  # Каждые 6 часов
            id='stripe_sync',
            name='Синхронизация с Stripe',
            replace_existing=True
        )
        
        # Обновляем истекшие подписки каждые 30 минут
        self.scheduler.add_job(
            self.update_expired_subscriptions,
            CronTrigger(minute='*/30'),  # Каждые 30 минут
            id='expired_subscriptions_update',
            name='Обновление истекших подписок',
            replace_existing=True
        )
        
        self.scheduler.start()
        logger.info("Мониторинг подписок запущен успешно")
    
    def stop_monitoring(self):
        """Остановить мониторинг подписок"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Мониторинг подписок остановлен")
    
    async def check_subscription_status(self):
        """Проверить статус всех активных подписок"""
        try:
            logger.info("Начало проверки статуса подписок...")
            
            # Получаем всех пользователей с активными подписками
            active_users = self.supabase_service.supabase.table("users").select("*").eq(
                "subscription_status", "active"
            ).execute()
            
            checked_count = 0
            updated_count = 0
            
            for user_data in active_users.data:
                try:
                    user_id = user_data["id"]
                    stripe_subscription_id = user_data.get("stripe_subscription_id")
                    
                    if not stripe_subscription_id:
                        logger.warning(f"Пользователь {user_id} имеет активную подписку, но нет Stripe ID")
                        continue
                    
                    # Проверяем статус в Stripe
                    subscription = stripe.Subscription.retrieve(stripe_subscription_id)
                    checked_count += 1
                    
                    # Проверяем, изменился ли статус
                    if subscription.status != "active":\n                        logger.info(f"Обновление статуса подписки для пользователя {user_id}: {subscription.status}")\n                        \n                        # Обновляем статус в нашей БД\n                        await self._update_user_subscription_status(user_id, subscription)\n                        updated_count += 1\n                    \n                    # Проверяем истечение периода\n                    current_period_end = datetime.fromtimestamp(subscription.current_period_end)\n                    if current_period_end < datetime.now():\n                        logger.info(f"Подписка пользователя {user_id} истекла")\n                        await self._handle_subscription_expired(user_id)\n                        updated_count += 1\n                    \n                except stripe.error.StripeError as e:\n                    logger.error(f"Ошибка Stripe при проверке подписки пользователя {user_data['id']}: {e}")\n                except Exception as e:\n                    logger.error(f"Ошибка при проверке подписки пользователя {user_data['id']}: {e}")\n            \n            logger.info(f"Проверка завершена. Проверено: {checked_count}, обновлено: {updated_count}")\n            \n        except Exception as e:\n            logger.error(f"Общая ошибка при проверке статуса подписок: {e}")\n    \n    async def sync_with_stripe(self):\n        """Синхронизировать данные о подписках с Stripe"""\n        try:\n            logger.info("Начало синхронизации с Stripe...")\n            \n            # Получаем всех пользователей с Stripe подписками\n            users_with_stripe = self.supabase_service.supabase.table("users").select("*").not_.is_(\n                "stripe_subscription_id", "null"\n            ).execute()\n            \n            synced_count = 0\n            \n            for user_data in users_with_stripe.data:\n                try:\n                    user_id = user_data["id"]\n                    stripe_subscription_id = user_data["stripe_subscription_id"]\n                    \n                    # Получаем актуальную информацию из Stripe\n                    subscription = stripe.Subscription.retrieve(stripe_subscription_id)\n                    \n                    # Обновляем информацию в нашей БД\n                    await self._sync_subscription_data(user_id, subscription)\n                    synced_count += 1\n                    \n                except stripe.error.StripeError as e:\n                    if e.code == 'resource_missing':\n                        logger.warning(f"Подписка не найдена в Stripe для пользователя {user_id}, очищаем данные")\n                        await self._clear_stripe_subscription_data(user_id)\n                    else:\n                        logger.error(f"Ошибка Stripe при синхронизации пользователя {user_id}: {e}")\n                except Exception as e:\n                    logger.error(f"Ошибка при синхронизации пользователя {user_id}: {e}")\n            \n            logger.info(f"Синхронизация завершена. Синхронизировано: {synced_count}")\n            \n        except Exception as e:\n            logger.error(f"Общая ошибка при синхронизации с Stripe: {e}")\n    \n    async def update_expired_subscriptions(self):\n        """Обновить истекшие подписки"""\n        try:\n            logger.info("Проверка истекших подписок...")\n            \n            expired_count = await self.subscription_service.check_and_update_expired_subscriptions()\n            \n            if expired_count > 0:\n                logger.info(f"Обновлено {expired_count} истекших подписок")\n            \n        except Exception as e:\n            logger.error(f"Ошибка при обновлении истекших подписок: {e}")\n    \n    async def _update_user_subscription_status(self, user_id: int, subscription):\n        """Обновить статус подписки пользователя на основе данных Stripe"""\n        try:\n            status_mapping = {\n                "active": "active",\n                "canceled": "canceled", \n                "unpaid": "expired",\n                "past_due": "expired",\n                "incomplete": "expired",\n                "incomplete_expired": "expired"\n            }\n            \n            new_status = status_mapping.get(subscription.status, "expired")\n            \n            update_data = {\n                "subscription_status": new_status,\n                "subscription_start": datetime.fromtimestamp(subscription.current_period_start).isoformat(),\n                "subscription_end": datetime.fromtimestamp(subscription.current_period_end).isoformat()\n            }\n            \n            # Если подписка отменена или истекла, сбрасываем счетчик фото\n            if new_status in ["expired", "canceled"]:\n                update_data["photos_analyzed"] = 0\n            \n            self.supabase_service.supabase.table("users").update(update_data).eq("id", user_id).execute()\n            \n            logger.info(f"Обновлен статус подписки пользователя {user_id}: {new_status}")\n            \n        except Exception as e:\n            logger.error(f"Ошибка обновления статуса подписки пользователя {user_id}: {e}")\n    \n    async def _handle_subscription_expired(self, user_id: int):\n        """Обработать истечение подписки"""\n        try:\n            # Обновляем статус на "expired" и сбрасываем счетчик фото\n            update_data = {\n                "subscription_status": "expired",\n                "photos_analyzed": 0\n            }\n            \n            self.supabase_service.supabase.table("users").update(update_data).eq("id", user_id).execute()\n            \n            logger.info(f"Подписка истекла для пользователя {user_id}")\n            \n        except Exception as e:\n            logger.error(f"Ошибка обработки истечения подписки пользователя {user_id}: {e}")\n    \n    async def _sync_subscription_data(self, user_id: int, subscription):\n        """Синхронизировать данные подписки с Stripe"""\n        try:\n            update_data = {\n                "subscription_status": "active" if subscription.status == "active" else "expired",\n                "subscription_start": datetime.fromtimestamp(subscription.current_period_start).isoformat(),\n                "subscription_end": datetime.fromtimestamp(subscription.current_period_end).isoformat(),\n                "stripe_customer_id": subscription.customer\n            }\n            \n            # Определяем тип плана по цене\n            if subscription.items.data:\n                price_id = subscription.items.data[0].price.id\n                if price_id == self.stripe_service.subscription_plans["monthly"]["stripe_price_id"]:\n                    update_data["subscription_plan"] = "monthly"\n                elif price_id == self.stripe_service.subscription_plans["yearly"]["stripe_price_id"]:\n                    update_data["subscription_plan"] = "yearly"\n            \n            self.supabase_service.supabase.table("users").update(update_data).eq("id", user_id).execute()\n            \n        except Exception as e:\n            logger.error(f"Ошибка синхронизации данных подписки пользователя {user_id}: {e}")\n    \n    async def _clear_stripe_subscription_data(self, user_id: int):\n        """Очистить данные Stripe подписки"""\n        try:\n            update_data = {\n                "subscription_status": "free",\n                "subscription_plan": None,\n                "stripe_subscription_id": None,\n                "stripe_customer_id": None,\n                "subscription_start": None,\n                "subscription_end": None,\n                "photos_analyzed": 0\n            }\n            \n            self.supabase_service.supabase.table("users").update(update_data).eq("id", user_id).execute()\n            \n            logger.info(f"Очищены данные Stripe для пользователя {user_id}")\n            \n        except Exception as e:\n            logger.error(f"Ошибка очистки данных Stripe пользователя {user_id}: {e}")\n    \n    async def force_check_user_subscription(self, user_id: int) -> bool:\n        """Принудительно проверить подписку конкретного пользователя"""\n        try:\n            user_result = self.supabase_service.supabase.table("users").select("*").eq("id", user_id).execute()\n            \n            if not user_result.data:\n                return False\n            \n            user_data = user_result.data[0]\n            stripe_subscription_id = user_data.get("stripe_subscription_id")\n            \n            if not stripe_subscription_id:\n                return True  # Нет подписки - все в порядке\n            \n            # Проверяем в Stripe\n            subscription = stripe.Subscription.retrieve(stripe_subscription_id)\n            await self._update_user_subscription_status(user_id, subscription)\n            \n            return True\n            \n        except Exception as e:\n            logger.error(f"Ошибка принудительной проверки подписки пользователя {user_id}: {e}")\n            return False