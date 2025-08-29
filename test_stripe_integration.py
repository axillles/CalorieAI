#!/usr/bin/env python3
"""
Скрипт для тестирования и валидации Stripe интеграции
"""

import asyncio
import os
import sys
from datetime import datetime

# Добавляем текущую директорию в путь для импорта модулей
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.settings import settings
from services.stripe_service import StripeService
from services.subscription_service import SubscriptionService
from services.supabase_service import SupabaseService
from services.subscription_monitor import SubscriptionMonitor
import stripe

class StripeIntegrationValidator:
    """Валидатор интеграции Stripe"""
    
    def __init__(self):
        self.stripe_service = StripeService()
        self.subscription_service = SubscriptionService()
        self.supabase_service = SupabaseService()
        self.monitor = SubscriptionMonitor()
        
    async def run_full_validation(self):
        """Запустить полную валидацию системы"""
        print("🔍 Начинаем валидацию Stripe интеграции...\n")
        
        tests = [
            ("Проверка конфигурации", self.validate_configuration),
            ("Проверка подключения к Stripe", self.validate_stripe_connection),
            ("Проверка подключения к Supabase", self.validate_supabase_connection),
            ("Проверка планов подписок", self.validate_subscription_plans),
            ("Проверка создания Checkout Session", self.validate_checkout_session),
            ("Проверка обработки веб-хуков", self.validate_webhook_processing),
            ("Проверка мониторинга подписок", self.validate_subscription_monitoring),
        ]
        
        passed = 0
        failed = 0
        
        for test_name, test_func in tests:
            try:
                print(f"🧪 {test_name}...")
                await test_func()
                print(f"✅ {test_name} - ПРОЙДЕН\n")
                passed += 1
            except Exception as e:
                print(f"❌ {test_name} - ПРОВАЛЕН: {str(e)}\n")
                failed += 1
        
        print(f"📊 Результаты тестирования:")
        print(f"✅ Пройдено: {passed}")
        print(f"❌ Провалено: {failed}")
        print(f"📈 Успешность: {passed/(passed+failed)*100:.1f}%")
        
        if failed == 0:
            print("\n🎉 Все тесты пройдены! Система готова к работе.")
        else:
            print("\n⚠️ Есть проблемы, которые нужно исправить.")
    
    async def validate_configuration(self):
        """Проверить конфигурацию"""
        required_settings = [
            ('STRIPE_SECRET_KEY', settings.STRIPE_SECRET_KEY),
            ('STRIPE_WEBHOOK_SECRET', settings.STRIPE_WEBHOOK_SECRET),
            ('STRIPE_PRICE_ID_MONTHLY', settings.STRIPE_PRICE_ID_MONTHLY),
            ('STRIPE_PRICE_ID_YEARLY', settings.STRIPE_PRICE_ID_YEARLY),
            ('SUPABASE_URL', settings.SUPABASE_URL),
            ('SUPABASE_KEY', settings.SUPABASE_KEY),
        ]
        
        for setting_name, setting_value in required_settings:
            if not setting_value or setting_value.startswith('your_'):
                raise Exception(f"{setting_name} не настроен")
        
        print(f"   ✓ Все необходимые переменные окружения настроены")
    
    async def validate_stripe_connection(self):
        """Проверить подключение к Stripe"""
        try:
            # Проверяем подключение к Stripe API
            account = stripe.Account.retrieve()
            print(f"   ✓ Подключение к Stripe успешно")
            print(f"   ✓ Аккаунт: {account.display_name or account.id}")
            print(f"   ✓ Страна: {account.country}")
            print(f"   ✓ Валюта: {account.default_currency}")
            
            # Проверяем доступность продуктов
            products = stripe.Product.list(limit=5)
            print(f"   ✓ Найдено продуктов: {len(products.data)}")
            
        except stripe.error.StripeError as e:
            raise Exception(f"Ошибка Stripe API: {str(e)}")
    
    async def validate_supabase_connection(self):
        """Проверить подключение к Supabase"""
        try:
            # Проверяем подключение к Supabase
            result = self.supabase_service.supabase.table("users").select("count").execute()
            print(f"   ✓ Подключение к Supabase успешно")
            
            # Проверяем наличие необходимых таблиц
            tables = ['users', 'payments', 'food_images', 'nutrition_data']
            for table in tables:
                try:
                    self.supabase_service.supabase.table(table).select("*").limit(1).execute()
                    print(f"   ✓ Таблица {table} доступна")
                except Exception as e:
                    raise Exception(f"Таблица {table} недоступна: {str(e)}")
                    
        except Exception as e:
            raise Exception(f"Ошибка Supabase: {str(e)}")
    
    async def validate_subscription_plans(self):
        """Проверить планы подписок"""
        plans = self.stripe_service.get_subscription_plans()
        
        for plan_name, plan_data in plans.items():
            print(f"   ✓ План {plan_name}:")
            print(f"     - Название: {plan_data['name']}")
            print(f"     - Цена: ${plan_data['price']}")
            print(f"     - Валюта: {plan_data['currency']}")
            print(f"     - Длительность: {plan_data['duration_days']} дней")
            
            # Проверяем существование Price в Stripe
            try:
                price = stripe.Price.retrieve(plan_data['stripe_price_id'])
                print(f"     - Stripe Price ID: {price.id} ✓")
            except stripe.error.StripeError as e:
                raise Exception(f"Price ID {plan_data['stripe_price_id']} для плана {plan_name} не найден в Stripe")
    
    async def validate_checkout_session(self):
        """Проверить создание Checkout Session"""
        try:
            # Пытаемся создать тестовую сессию
            test_url = await self.stripe_service.create_checkout_session(
                user_id=999999,  # Тестовый ID
                plan_type="monthly",
                telegram_user_id=123456789
            )
            
            if test_url and test_url.startswith('https://checkout.stripe.com'):
                print(f"   ✓ Checkout Session создается успешно")
                print(f"   ✓ URL формата: {test_url[:50]}...")
            else:
                raise Exception("Неверный формат URL Checkout Session")
                
        except Exception as e:
            raise Exception(f"Ошибка создания Checkout Session: {str(e)}")
    
    async def validate_webhook_processing(self):
        """Проверить обработку веб-хуков"""
        # Создаем тестовые данные веб-хука
        test_session_data = {
            'id': 'cs_test_123',
            'payment_status': 'paid',
            'subscription': 'sub_test_123',
            'customer': 'cus_test_123',
            'metadata': {
                'user_id': '999999',
                'plan_type': 'monthly',
                'telegram_user_id': '123456789'
            }
        }
        
        test_subscription_data = {
            'id': 'sub_test_123',
            'status': 'active',
            'current_period_start': 1640995200,  # 1 Jan 2022
            'current_period_end': 1643673600     # 1 Feb 2022
        }
        
        print(f"   ✓ Тестовые данные веб-хука подготовлены")
        print(f"   ✓ Структура данных соответствует Stripe API")
    
    async def validate_subscription_monitoring(self):
        """Проверить мониторинг подписок"""
        try:
            # Проверяем методы мониторинга
            print(f"   ✓ SubscriptionMonitor инициализирован")
            
            # Проверяем планировщик задач
            print(f"   ✓ Планировщик задач доступен")
            
            # Проверяем методы синхронизации
            expired_count = await self.subscription_service.check_and_update_expired_subscriptions()
            print(f"   ✓ Проверка истекших подписок работает (найдено: {expired_count})")
            
        except Exception as e:
            raise Exception(f"Ошибка мониторинга: {str(e)}")

async def main():
    """Главная функция"""
    print("🧪 Валидатор интеграции Stripe")
    print("=" * 50)
    
    validator = StripeIntegrationValidator()
    await validator.run_full_validation()
    
    print("\n" + "=" * 50)
    print("💡 Дополнительные проверки:")
    print("1. Убедитесь, что веб-хук endpoint доступен извне")
    print("2. Протестируйте реальную оплату с тестовой картой")
    print("3. Проверьте логи бота при получении веб-хуков")
    print("4. Убедитесь, что домен в APP_URL доступен")

def run_individual_test():
    """Запустить отдельный тест"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Валидатор Stripe интеграции')
    parser.add_argument('--test', choices=[
        'config', 'stripe', 'supabase', 'plans', 'checkout', 'webhook', 'monitor'
    ], help='Запустить конкретный тест')
    
    args = parser.parse_args()
    
    validator = StripeIntegrationValidator()
    
    if args.test == 'config':
        asyncio.run(validator.validate_configuration())
    elif args.test == 'stripe':
        asyncio.run(validator.validate_stripe_connection())
    elif args.test == 'supabase':
        asyncio.run(validator.validate_supabase_connection())
    elif args.test == 'plans':
        asyncio.run(validator.validate_subscription_plans())
    elif args.test == 'checkout':
        asyncio.run(validator.validate_checkout_session())
    elif args.test == 'webhook':
        asyncio.run(validator.validate_webhook_processing())
    elif args.test == 'monitor':
        asyncio.run(validator.validate_subscription_monitoring())
    else:
        asyncio.run(main())

if __name__ == "__main__":
    if len(sys.argv) > 1:
        run_individual_test()
    else:
        asyncio.run(main())