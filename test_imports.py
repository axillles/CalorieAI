#!/usr/bin/env python3
"""
Тестовый файл для проверки импортов и базовой функциональности
"""

def test_imports():
    """Тестируем все импорты"""
    try:
        print("Тестируем импорты...")
        
        # Тест 1: Основные библиотеки
        import asyncio
        import logging
        print("✓ asyncio и logging импортированы")
        
        # Тест 2: Telegram
        from telegram.ext import Application, CommandHandler, MessageHandler, filters
        from telegram import Update
        print("✓ telegram библиотеки импортированы")
        
        # Тест 3: Настройки
        from config.settings import settings
        print("✓ настройки импортированы")
        
        # Тест 4: Модели
        from models.data_models import User, FoodImage, NutritionData, DailyReport
        print("✓ модели данных импортированы")
        
        # Тест 5: Сервисы
        from services.supabase_service import SupabaseService
        from services.openai_service import OpenAIService
        print("✓ сервисы импортированы")
        
        # Тест 6: Обработчики
        from handlers.command_handler import CommandHandler as BotCommandHandler
        from handlers.message_handler import MessageHandler as BotMessageHandler
        print("✓ обработчики импортированы")
        
        # Тест 7: Утилиты
        from utils.report_generator import ReportGenerator
        print("✓ утилиты импортированы")
        
        # Тест 8: База данных
        from config.database import db_manager
        print("✓ база данных импортирована")
        
        print("\n🎉 Все импорты успешны!")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка импорта: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_settings():
    """Тестируем настройки"""
    try:
        print("\nТестируем настройки...")
        from config.settings import settings
        
        print(f"TELEGRAM_BOT_TOKEN: {'✓ установлен' if settings.TELEGRAM_BOT_TOKEN else '❌ не установлен'}")
        print(f"OPENAI_API_KEY: {'✓ установлен' if settings.OPENAI_API_KEY else '❌ не установлен'}")
        print(f"SUPABASE_URL: {'✓ установлен' if settings.SUPABASE_URL else '❌ не установлен'}")
        print(f"SUPABASE_KEY: {'✓ установлен' if settings.SUPABASE_KEY else '❌ не установлен'}")
        
        print(f"OPENAI_MODEL: {settings.OPENAI_MODEL}")
        print(f"MAX_TOKENS: {settings.MAX_TOKENS}")
        print(f"MAX_IMAGE_SIZE: {settings.MAX_IMAGE_SIZE}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка настроек: {e}")
        return False

def test_models():
    """Тестируем модели данных"""
    try:
        print("\nТестируем модели данных...")
        from models.data_models import User, FoodImage, NutritionData, DailyReport
        
        # Тест создания пользователя
        user = User(telegram_id=123456, username="test_user")
        print(f"✓ Пользователь создан: {user.telegram_id}")
        
        # Тест создания записи о еде
        food_image = FoodImage(user_id=1, image_url="test.jpg")
        print(f"✓ Запись о еде создана: {food_image.image_url}")
        
        # Тест создания данных о питании
        nutrition = NutritionData(
            food_image_id=1,
            calories=500,
            protein=25,
            fats=20,
            carbs=50,
            food_name="Тестовое блюдо",
            confidence=0.8
        )
        print(f"✓ Данные о питании созданы: {nutrition.food_name}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка моделей: {e}")
        return False

def test_report_generator():
    """Тестируем генератор отчетов"""
    try:
        print("\nТестируем генератор отчетов...")
        from utils.report_generator import ReportGenerator
        
        # Тест дневного отчета
        nutrition_data = {"calories": 1500, "protein": 100, "fats": 50, "carbs": 200}
        report = ReportGenerator.format_daily_report(nutrition_data)
        print("✓ Дневной отчет сгенерирован")
        
        # Тест приветственного сообщения
        welcome = ReportGenerator.get_welcome_message()
        print("✓ Приветственное сообщение сгенерировано")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка генератора отчетов: {e}")
        return False

def main():
    """Главная функция тестирования"""
    print("🧪 Запуск тестов КБЖУ Анализатора...\n")
    
    tests = [
        test_imports,
        test_settings,
        test_models,
        test_report_generator
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print(f"\n📊 Результаты тестов: {passed}/{total} пройдено")
    
    if passed == total:
        print("🎉 Все тесты пройдены! Бот готов к настройке.")
        print("\n📝 Следующие шаги:")
        print("1. Создайте файл .env с вашими API ключами")
        print("2. Настройте Supabase базу данных")
        print("3. Запустите бота командой: python main.py")
    else:
        print("❌ Некоторые тесты не пройдены. Проверьте установку зависимостей.")

if __name__ == "__main__":
    main()
