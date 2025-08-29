import stripe
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from config.settings import settings
from services.supabase_service import SupabaseService

logger = logging.getLogger(__name__)

class StripeService:
    """Сервис для работы с платежами Stripe"""
    
    def __init__(self):
        stripe.api_key = settings.STRIPE_SECRET_KEY
        self.supabase_service = SupabaseService()
        
        # Планы подписок с соответствующими Stripe Price ID
        self.subscription_plans = {
            "monthly": {
                "name": "Месячная подписка",
                "price": 4.99,
                "currency": "USD",
                "stripe_price_id": settings.STRIPE_PRICE_ID_MONTHLY,
                "duration_days": 30,
                "photos_limit": -1  # -1 = безлимит
            },
            "yearly": {
                "name": "Годовая подписка", 
                "price": 49.99,
                "currency": "USD",
                "stripe_price_id": settings.STRIPE_PRICE_ID_YEARLY,
                "duration_days": 365,
                "photos_limit": -1
            }
        }
    
    async def create_checkout_session(self, user_id: int, plan_type: str, telegram_user_id: int) -> Optional[str]:
        """Создать Checkout Session для подписки"""
        try:
            plan = self.subscription_plans.get(plan_type)
            if not plan:
                logger.error(f"Неизвестный план подписки: {plan_type}")
                return None
            
            if not plan["stripe_price_id"]:
                logger.error(f"Не настроен Stripe Price ID для плана {plan_type}")
                return None
            
            # Создаем Checkout Session
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price': plan["stripe_price_id"],
                    'quantity': 1,
                }],
                mode='subscription',
                success_url=f'{settings.APP_URL}/payment/success?session_id={{CHECKOUT_SESSION_ID}}',
                cancel_url=f'{settings.APP_URL}/payment/cancel',
                client_reference_id=str(user_id),
                metadata={
                    'user_id': user_id,
                    'plan_type': plan_type,
                    'telegram_user_id': telegram_user_id
                },
                subscription_data={
                    'metadata': {
                        'user_id': user_id,
                        'plan_type': plan_type,
                        'telegram_user_id': telegram_user_id
                    }
                }
            )
            
            logger.info(f"Создана Checkout Session для пользователя {user_id}: {checkout_session.id}")
            return checkout_session.url
            
        except stripe.error.StripeError as e:
            logger.error(f"Ошибка Stripe при создании Checkout Session: {e}")
            return None
        except Exception as e:
            logger.error(f"Общая ошибка при создании Checkout Session: {e}")
            return None
    
    async def handle_successful_payment(self, session_id: str) -> bool:
        """Обработать успешную оплату"""
        try:
            # Получаем информацию о сессии
            session = stripe.checkout.Session.retrieve(session_id)
            
            if session.payment_status != 'paid':
                logger.warning(f"Сессия {session_id} не оплачена")
                return False
            
            # Получаем подписку Stripe
            subscription_id = session.subscription
            subscription = stripe.Subscription.retrieve(subscription_id)
            
            user_id = int(session.metadata.get('user_id'))
            plan_type = session.metadata.get('plan_type')
            telegram_user_id = int(session.metadata.get('telegram_user_id'))
            
            # Активируем подписку в нашей БД
            success = await self._activate_subscription(
                user_id=user_id,
                plan_type=plan_type,
                stripe_subscription_id=subscription_id,
                stripe_customer_id=session.customer,
                current_period_start=datetime.fromtimestamp(subscription.current_period_start),
                current_period_end=datetime.fromtimestamp(subscription.current_period_end)
            )
            
            if success:
                logger.info(f"Подписка успешно активирована для пользователя {user_id}")
                return True
            else:
                logger.error(f"Ошибка активации подписки для пользователя {user_id}")
                return False
                
        except stripe.error.StripeError as e:
            logger.error(f"Ошибка Stripe при обработке успешной оплаты: {e}")
            return False
        except Exception as e:
            logger.error(f"Общая ошибка при обработке успешной оплаты: {e}")
            return False
    
    async def _activate_subscription(self, user_id: int, plan_type: str, 
                                   stripe_subscription_id: str, stripe_customer_id: str,
                                   current_period_start: datetime, current_period_end: datetime) -> bool:
        """Активировать подписку в нашей БД"""
        try:
            # Обновляем статус пользователя
            result = self.supabase_service.supabase.table("users").update({
                "subscription_status": "active",
                "subscription_plan": plan_type,
                "stripe_subscription_id": stripe_subscription_id,
                "stripe_customer_id": stripe_customer_id,
                "subscription_start": current_period_start.isoformat(),
                "subscription_end": current_period_end.isoformat(),
                "photos_analyzed": 0  # Сбрасываем счетчик
            }).eq("id", user_id).execute()
            
            # Создаем запись о платеже
            payment_data = {
                "user_id": user_id,
                "amount": self.subscription_plans[plan_type]["price"],
                "currency": "USD",
                "status": "completed",
                "payment_method": "stripe",
                "stripe_subscription_id": stripe_subscription_id,
                "plan_type": plan_type,
                "created_at": datetime.now().isoformat()
            }
            
            self.supabase_service.supabase.table("payments").insert(payment_data).execute()
            
            return True
            
        except Exception as e:
            logger.error(f"Ошибка активации подписки в БД: {e}")
            return False
    
    async def handle_subscription_updated(self, subscription_data: Dict) -> bool:
        """Обработать обновление подписки (продление, отмена и т.д.)"""
        try:
            subscription_id = subscription_data['id']
            status = subscription_data['status']
            
            # Находим пользователя по subscription_id
            user_result = self.supabase_service.supabase.table("users").select("*").eq(
                "stripe_subscription_id", subscription_id
            ).execute()
            
            if not user_result.data:
                logger.warning(f"Пользователь не найден для подписки {subscription_id}")
                return False
            
            user = user_result.data[0]
            user_id = user['id']
            
            # Обновляем статус подписки
            if status == 'active':
                # Продление подписки
                current_period_start = datetime.fromtimestamp(subscription_data['current_period_start'])
                current_period_end = datetime.fromtimestamp(subscription_data['current_period_end'])
                
                update_data = {
                    "subscription_status": "active",
                    "subscription_start": current_period_start.isoformat(),
                    "subscription_end": current_period_end.isoformat()
                }
            elif status in ['canceled', 'unpaid', 'past_due']:
                # Отмена или просрочка подписки
                update_data = {
                    "subscription_status": "expired"
                }
            else:
                logger.info(f"Неизвестный статус подписки: {status}")
                return True
            
            self.supabase_service.supabase.table("users").update(update_data).eq("id", user_id).execute()
            
            logger.info(f"Обновлен статус подписки для пользователя {user_id}: {status}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка обработки обновления подписки: {e}")
            return False
    
    async def cancel_subscription(self, user_id: int) -> bool:
        """Отменить подписку пользователя"""
        try:
            # Получаем данные пользователя
            user = await self.supabase_service.get_user_by_telegram_id(user_id)
            if not user or not user.stripe_subscription_id:
                logger.error(f"Подписка не найдена для пользователя {user_id}")
                return False
            
            # Отменяем подписку в Stripe
            stripe.Subscription.delete(user.stripe_subscription_id)
            
            # Обновляем статус в БД
            self.supabase_service.supabase.table("users").update({
                "subscription_status": "canceled"
            }).eq("id", user.id).execute()
            
            logger.info(f"Подписка отменена для пользователя {user_id}")
            return True
            
        except stripe.error.StripeError as e:
            logger.error(f"Ошибка Stripe при отмене подписки: {e}")
            return False
        except Exception as e:
            logger.error(f"Общая ошибка при отмене подписки: {e}")
            return False
    
    async def get_subscription_info(self, user_id: int) -> Optional[Dict]:
        """Получить информацию о подписке пользователя"""
        try:
            user = await self.supabase_service.get_user_by_telegram_id(user_id)
            if not user:
                return None
            
            if user.subscription_status != "active" or not user.stripe_subscription_id:
                return {
                    "status": user.subscription_status,
                    "plan": None,
                    "current_period_end": None
                }
            
            # Получаем актуальную информацию из Stripe
            subscription = stripe.Subscription.retrieve(user.stripe_subscription_id)
            
            return {
                "status": subscription.status,
                "plan": user.subscription_plan,
                "current_period_end": datetime.fromtimestamp(subscription.current_period_end),
                "cancel_at_period_end": subscription.cancel_at_period_end
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Ошибка Stripe при получении информации о подписке: {e}")
            return None
        except Exception as e:
            logger.error(f"Общая ошибка при получении информации о подписке: {e}")
            return None
    
    def get_subscription_plans(self) -> Dict[str, Any]:
        """Получить доступные планы подписок"""
        return self.subscription_plans