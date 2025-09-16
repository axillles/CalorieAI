import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

from config.settings import settings
from services.supabase_service import SupabaseService

logger = logging.getLogger(__name__)


class CryptoService:
    """Провайдер оплаты переводом на криптокошелёк с подтверждением монитором.

    Логика:
    - Показываем адрес(а) кошельков (TON и/или USDT TRC20).
    - Пользователь переводит сумму и нажимает "Я оплатил" → создаётся платеж `pending`.
    - Монитор TRC20 подтверждает поступление и вызывает активацию подписки.
    - Платёжную запись создаёт/обновляет внешний код (монитор), здесь дубликаты не создаём.
    """

    def __init__(self) -> None:
        self.supabase_service = SupabaseService()

        # Базовые планы в USD
        self.subscription_plans: Dict[str, Dict[str, Any]] = {
            "monthly": {
                "name": "Monthly subscription",
                "price": 4.99,
                "currency": "USD",
                "duration_days": 30,
                "photos_limit": -1,
            },
            "yearly": {
                "name": "Yearly subscription",
                "price": 49.99,
                "currency": "USD",
                "duration_days": 365,
                "photos_limit": -1,
            },
        }

    def get_subscription_plans(self) -> Dict[str, Any]:
        return self.subscription_plans

    def get_provider_display_name(self) -> str:
        return "🪙 Crypto wallet (transfer)"

    def get_payment_instructions(self, plan_type: str) -> Optional[str]:
        plan = self.subscription_plans.get(plan_type)
        if not plan:
            return None

        ton_addr = getattr(settings, "CRYPTO_TON_ADDRESS", None)
        trc20_addr = getattr(settings, "CRYPTO_TRC20_USDT_ADDRESS", None)

        if not ton_addr and not trc20_addr:
            return None

        lines = [
            f"🪙 Subscription payment: {plan['name']}",
            f"💰 Amount: ${plan['price']} {plan['currency']}",
            "\nSend the equivalent in crypto to one of the addresses:",
        ]

        if ton_addr:
            lines.append(f"• TON (TON): `{ton_addr}`")
        if trc20_addr:
            lines.append(f"• USDT (TRC20): `{trc20_addr}`")

        lines.extend([
            "\nAfter transfer, press \"✅ I have paid\" below.",
            "If needed, send the transaction hash in this chat.",
        ])

        return "\n".join(lines)

    async def activate_after_user_confirm(self, user_id: int, plan_type: str, tx_hash: Optional[str] = None) -> bool:
        try:
            plan = self.subscription_plans.get(plan_type)
            if not plan:
                logger.error("Unknown plan in crypto activation")
                return False

            start_date = datetime.now()
            end_date = start_date + timedelta(days=plan["duration_days"]) 

            self.supabase_service.supabase.table("users").update({
                "subscription_status": "active",
                "subscription_plan": plan_type,
                "subscription_start": start_date.isoformat(),
                "subscription_end": end_date.isoformat(),
                "photos_analyzed": 0,
                "payment_provider": "crypto",
            }).eq("id", user_id).execute()

            return True
        except Exception as e:
            logger.error(f"Crypto activate error: {e}")
            return False


