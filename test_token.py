#!/usr/bin/env python3
"""
Простой тест для проверки токена бота
"""

import asyncio
import logging
from telegram import Bot
from config.settings import settings

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def test_bot_token():
    """Тестируем токен бота"""
    try:
        print("🔍 Тестирование токена бота...")
        
        if not settings.TELEGRAM_BOT_TOKEN:
            print("❌ Токен не установлен")
            return False
        
        if settings.TELEGRAM_BOT_TOKEN == "your_telegram_bot_token_here":
            print("❌ Установлен примерный токен")
            return False
        
        # Создаем бота
        bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
        
        # Получаем информацию о боте
        bot_info = await bot.get_me()
        
        print(f"✅ Токен работает!")
        print(f"🤖 Имя бота: {bot_info.first_name}")
        print(f"📝 Username: @{bot_info.username}")
        print(f"🆔 ID бота: {bot_info.id}")
        
        await bot.close()
        return True
        
    except Exception as e:
        print(f"❌ Ошибка тестирования токена: {e}")
        return False

async def main():
    """Главная функция"""
    success = await test_bot_token()
    
    if success:
        print("\n🎉 Токен бота работает корректно!")
        print("💡 Теперь можно запускать основного бота: python main.py")
    else:
        print("\n❌ Проблема с токеном бота")
        print("💡 Проверьте токен в файле .env")

if __name__ == "__main__":
    asyncio.run(main())

