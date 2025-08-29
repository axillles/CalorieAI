import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from telegram import LabeledPrice, Update
from telegram.ext import ContextTypes
from config.settings import settings

logger = logging.getLogger(__name__)

class TelegramStarsService:
    """Сервис для работы с Telegram Stars платежами"""
    
    def __init__(self):
        # Планы подписок в Telegram Stars (1 USD ≈ 100 Stars примерно)
        self.subscription_plans = {
            "monthly": {
                "name": "Monthly KBGU Analysis",
                "price_stars": 500,  # ~$5
                "price_usd": 4.99,
                "duration_days": 30,
                "photos_limit": -1  # -1 = безлимит
            },
            "yearly": {
                "name": "Yearly KBGU Analysis", 
                "price_stars": 5000,  # ~$50
                "price_usd": 49.99,
                "duration_days": 365,
                "photos_limit": -1
            }
        }
    
    async def create_stars_invoice(self, update: Update, context: ContextTypes.DEFAULT_TYPE, 
                                 user_id: int, plan_type: str) -> bool:
        """Создать инвойс для оплаты Telegram Stars"""
        try:
            plan = self.subscription_plans.get(plan_type)
            if not plan:
                logger.error(f"Неизвестный план подписки: {plan_type}")
                return False
            
            # Создаем LabeledPrice для Telegram Stars
            prices = [LabeledPrice(
                label=plan["name"],
                amount=plan["price_stars"]  # В Stars, не в центах
            )]
            
            # Payload содержит информацию для обработки после оплаты
            payload = f"stars_subscription_{user_id}_{plan_type}_{int(datetime.now().timestamp())}"
            
            # Отправляем инвойс
            await context.bot.send_invoice(
                chat_id=update.effective_chat.id,
                title=f"⭐ {plan['name']}",
                description=f"Безлимитный анализ фото еды на {plan['duration_days']} дней\n"
                           f"💰 Цена: {plan['price_stars']} Telegram Stars\n"
                           f"📸 Неограниченное количество фото\n"
                           f"🤖 ИИ анализ калорий, белков, жиров, углеводов",
                payload=payload,
                provider_token="",  # Пустой для Telegram Stars
                currency="XTR",     # XTR = Telegram Stars
                prices=prices,
                start_parameter=f"stars_subscription_{plan_type}",
                photo_url="https://telegram.org/img/t_logo.png",  # Опционально
                photo_size=512,
                photo_width=512,
                photo_height=512,
                need_name=False,
                need_phone_number=False,
                need_email=False,
                need_shipping_address=False,
                send_phone_number_to_provider=False,
                send_email_to_provider=False,
                is_flexible=False
            )
            
            logger.info(f"Создан Telegram Stars инвойс для пользователя {user_id}: {plan_type}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка создания Telegram Stars инвойса: {e}")
            return False
    
    async def handle_pre_checkout_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
        """Обработать pre-checkout запрос"""
        try:
            query = update.pre_checkout_query
            
            # Проверяем payload
            if not query.invoice_payload.startswith("stars_subscription_"):
                await query.answer(ok=False, error_message="Неверный тип платежа")
                return False
            
            # Парсим payload
            payload_parts = query.invoice_payload.split("_")
            if len(payload_parts) < 4:
                await query.answer(ok=False, error_message="Неверный формат платежа")
                return False
            
            user_id = int(payload_parts[2])
            plan_type = payload_parts[3]
            
            # Проверяем план
            if plan_type not in self.subscription_plans:
                await query.answer(ok=False, error_message="Неизвестный план подписки")
                return False
            
            plan = self.subscription_plans[plan_type]
            
            # Проверяем сумму
            if query.total_amount != plan["price_stars"]:
                await query.answer(ok=False, error_message="Неверная сумма платежа")
                return False
            
            # Одобряем платеж
            await query.answer(ok=True)
            logger.info(f"Pre-checkout одобрен для пользователя {user_id}: {plan_type}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка pre-checkout запроса: {e}")
            await query.answer(ok=False, error_message="Ошибка обработки платежа")
            return False
    
    async def handle_successful_payment(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> Optional[Dict[str, Any]]:
        """Обработать успешную оплату Telegram Stars"""
        try:
            payment = update.message.successful_payment
            
            # Парсим payload
            payload_parts = payment.invoice_payload.split("_")
            if len(payload_parts) < 4:
                logger.error("Неверный формат payload в successful_payment")
                return None
            
            user_id = int(payload_parts[2])
            plan_type = payload_parts[3]
            
            # Проверяем план
            plan = self.subscription_plans.get(plan_type)
            if not plan:
                logger.error(f"Неизвестный план в successful_payment: {plan_type}")
                return None
            
            # Возвращаем данные для активации подписки
            return {
                "success": True,
                "payment_id": payment.telegram_payment_charge_id,
                "amount_stars": payment.total_amount,
                "amount_usd": plan["price_usd"],
                "currency": "XTR",
                "user_id": user_id,
                "plan_type": plan_type,
                "telegram_user_id": update.effective_user.id,
                "provider_payment_charge_id": payment.provider_payment_charge_id
            }
            
        except Exception as e:
            logger.error(f"Ошибка обработки successful_payment: {e}")
            return None
    
    def get_subscription_plans(self) -> Dict[str, Any]:
        """Получить доступные планы подписок"""
        return self.subscription_plans
    
    def get_plan_info_message(self, plan_type: str) -> str:
        """Получить информационное сообщение о плане"""
        plan = self.subscription_plans.get(plan_type)
        if not plan:
            return "Неизвестный план подписки"
        
        return (
            f"⭐ **{plan['name']}**\n\n"
            f"💰 Стоимость: {plan['price_stars']} Telegram Stars\n"
            f"📅 Длительность: {plan['duration_days']} дней\n"
            f"📸 Фото: Безлимит\n\n"
            f"ℹ️ **Что включено:**\n"
            f"• Неограниченный анализ фотографий еды\n"
            f"• ИИ определение калорий, белков, жиров, углеводов\n"
            f"• Дневная и недельная статистика\n"
            f"• Персональные цели питания\n\n"
            f"💫 **Telegram Stars** - это внутренняя валюта Telegram\n"
            f"Вы можете купить Stars в настройках Telegram"
        )