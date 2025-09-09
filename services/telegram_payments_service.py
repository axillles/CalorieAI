import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

from telegram import LabeledPrice
from config.settings import settings
from services.supabase_service import SupabaseService

logger = logging.getLogger(__name__)


class TelegramPaymentsService:
    """Generic Telegram Payments (provider_token) service, compatible with Redsys via BotFather."""

    def __init__(self) -> None:
        self.supabase_service = SupabaseService()

        # EUR plans for Redsys testing; you can adjust prices/durations via env later
        self.subscription_plans: Dict[str, Dict[str, Any]] = {
            "monthly": {
                "name": "Monthly Subscription",
                "price": 4.99,
                "currency": getattr(settings, "TELEGRAM_PAYMENTS_CURRENCY", "EUR") or "EUR",
                "duration_days": 30,
                "photos_limit": -1,
            },
            "yearly": {
                "name": "Yearly Subscription",
                "price": 49.99,
                "currency": getattr(settings, "TELEGRAM_PAYMENTS_CURRENCY", "EUR") or "EUR",
                "duration_days": 365,
                "photos_limit": -1,
            },
        }

    def get_subscription_plans(self) -> Dict[str, Any]:
        return self.subscription_plans

    async def create_invoice_payload(self, user_id: int, plan_type: str) -> Optional[Dict[str, Any]]:
        try:
            plan = self.subscription_plans.get(plan_type)
            if not plan:
                logger.error(f"Unknown plan: {plan_type}")
                return None

            if not settings.PAYMENT_PROVIDER_TOKEN:
                logger.error("PAYMENT_PROVIDER_TOKEN is not configured")
                return None

            # Convert price to minor units (cents)
            amount_cents = int(round(plan["price"] * 100))
            prices = [LabeledPrice(plan["name"], amount_cents)]

            payload = {
                "title": plan["name"],
                "description": f"Подписка на {plan['duration_days']} дней",
                "payload": f"tgpay_subscription_{user_id}_{plan_type}_{int(datetime.now().timestamp())}",
                "provider_token": settings.PAYMENT_PROVIDER_TOKEN,
                "currency": plan["currency"],
                "prices": prices,
                "start_parameter": f"subscription_{plan_type}",
            }
            return payload
        except Exception as e:
            logger.error(f"Error creating invoice payload: {e}")
            return None

    async def handle_pre_checkout(self, invoice_payload: str, total_amount: int, currency: str) -> Optional[Dict[str, Any]]:
        try:
            # payload format: tgpay_subscription_{user_id}_{plan_type}_{ts}
            parts = invoice_payload.split("_")
            if len(parts) < 5 or parts[0] != "tgpay" or parts[1] != "subscription":
                logger.error("Invalid payload format for Telegram Payments")
                return None

            user_id = int(parts[2])
            plan_type = parts[3]

            plan = self.subscription_plans.get(plan_type)
            if not plan:
                logger.error("Plan not found in pre-checkout")
                return None

            expected_amount = int(round(plan["price"] * 100))
            expected_currency = plan["currency"]
            if total_amount != expected_amount or currency != expected_currency:
                logger.error("Amount or currency mismatch in pre-checkout")
                return None

            return {"user_id": user_id, "plan_type": plan_type}
        except Exception as e:
            logger.error(f"Error in pre-checkout: {e}")
            return None

    async def activate_after_success(self, payload: str, telegram_payment_charge_id: str, provider_payment_charge_id: str) -> bool:
        try:
            parts = payload.split("_")
            if len(parts) < 5:
                logger.error("Invalid payload in success handler")
                return False

            user_id = int(parts[2])
            plan_type = parts[3]
            plan = self.subscription_plans.get(plan_type)
            if not plan:
                logger.error("Plan not found in success handler")
                return False

            start_date = datetime.now()
            end_date = start_date + timedelta(days=plan["duration_days"]) 

            # Update user in DB (align with Stripe flow; avoid non-existing columns)
            self.supabase_service.supabase.table("users").update({
                "subscription_status": "active",
                "subscription_plan": plan_type,
                "subscription_start": start_date.isoformat(),
                "subscription_end": end_date.isoformat(),
                "photos_analyzed": 0,
            }).eq("id", user_id).execute()

            # Record payment (best-effort). If table doesn't exist, don't fail activation.
            try:
                self.supabase_service.supabase.table("payments").insert({
                    "user_id": user_id,
                    "amount": plan["price"],
                    "currency": plan["currency"],
                    "status": "completed",
                    "payment_method": settings.PAYMENT_PROVIDER_NAME or "telegram_payments",
                    "plan_type": plan_type,
                    "created_at": datetime.now().isoformat(),
                }).execute()
            except Exception as pay_err:
                logger.warning(f"Payment record insert skipped: {pay_err}")

            return True
        except Exception as e:
            logger.error(f"Error activating subscription after success: {e}")
            return False


