import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

from config.settings import settings
from services.supabase_service import SupabaseService

logger = logging.getLogger(__name__)


class CryptoService:
    """Простой провайдер оплаты переводом на криптокошелек (без авто-подтверждения).

    Логика:
    - Показываем адрес(а) кошельков (TON и/или USDT TRC20).
    - Пользователь переводит сумму и нажимает "Я оплатил".
    - Сразу активируем подписку (доверительный режим) и записываем платеж с пометкой user_confirmed.
    """

    def __init__(self) -> None:
        self.supabase_service = SupabaseService()

        # Базовые планы в USD
        self.subscription_plans: Dict[str, Dict[str, Any]] = {
            "monthly": {
                "name": "Месячная подписка",
                "price": 4.99,
                "currency": "USD",
                "duration_days": 30,
                "photos_limit": -1,
            },
            "yearly": {
                "name": "Годовая подписка",
                "price": 49.99,
                "currency": "USD",
                "duration_days": 365,
                "photos_limit": -1,
            },
        }

    def get_subscription_plans(self) -> Dict[str, Any]:
        return self.subscription_plans

    def get_provider_display_name(self) -> str:
        return "🪙 Криптокошелёк (перевод)"

    def get_payment_instructions(self, plan_type: str) -> Optional[str]:
        plan = self.subscription_plans.get(plan_type)
        if not plan:
            return None

        ton_addr = getattr(settings, "CRYPTO_TON_ADDRESS", None)
        trc20_addr = getattr(settings, "CRYPTO_TRC20_USDT_ADDRESS", None)

        if not ton_addr and not trc20_addr:
            return None

        lines = [
            f"🪙 Оплата подписки: {plan['name']}",
            f"💰 Сумма: ${plan['price']} {plan['currency']}",
            "\nПереведите эквивалент в криптовалюте на один из адресов:
",
        ]

        if ton_addr:
            lines.append(f"• TON (TON): `{ton_addr}`")
        if trc20_addr:
            lines.append(f"• USDT (TRC20): `{trc20_addr}`")

        lines.extend([
            "\nПосле перевода нажмите кнопку \"✅ Я оплатил\" ниже.",
            "Если нужно, пришлите хеш транзакции этим же сообщением.",
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

            # Запишем платеж (best-effort)
            try:
                self.supabase_service.supabase.table("payments").insert({
                    "user_id": user_id,
                    "amount": plan["price"],
                    "currency": plan["currency"],
                    "status": "user_confirmed",
                    "payment_method": "crypto",
                    "plan_type": plan_type,
                    "tx_hash": tx_hash or "",
                    "created_at": datetime.now().isoformat(),
                }).execute()
            except Exception as pay_err:
                logger.warning(f"Payment record insert skipped (crypto): {pay_err}")

            return True
        except Exception as e:
            logger.error(f"Crypto activate error: {e}")
            return False


