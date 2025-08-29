#!/usr/bin/env python3
"""
Скрипт для проверки конфигурации бота
"""

def check_config():
    """Проверяем конфигурацию бота"""
    print("🔍 Проверка конфигурации КБЖУ Анализатора...\n")
    
    try:
        from config.settings import settings
        
        # Проверяем Telegram Bot Token
        print("📱 Telegram Bot Token:")
        if not settings.TELEGRAM_BOT_TOKEN:
            print("   ❌ Не установлен")
            print("   💡 Получите токен у @BotFather в Telegram")
        elif settings.TELEGRAM_BOT_TOKEN == "your_telegram_bot_token_here":
            print("   ⚠️  Установлен примерный токен")
            print("   💡 Замените на реальный токен")
        else:
            print("   ✅ Установлен")
        
        # Проверяем OpenAI API Key
        print("\n🤖 OpenAI API Key:")
        if not settings.OPENAI_API_KEY:
            print("   ❌ Не установлен")
            print("   💡 Получите ключ на https://platform.openai.com/api-keys")
        elif settings.OPENAI_API_KEY == "your_openai_api_key_here":
            print("   ⚠️  Установлен примерный ключ")
            print("   💡 Замените на реальный ключ")
        else:
            print("   ✅ Установлен")
        
        # Проверяем Supabase URL
        print("\n🗄️  Supabase URL:")
        if not settings.SUPABASE_URL:
            print("   ❌ Не установлен")
            print("   💡 Создайте проект на supabase.com")
        elif settings.SUPABASE_URL == "https://your-project-id.supabase.co":
            print("   ⚠️  Установлен примерный URL")
            print("   💡 Замените на реальный URL")
        else:
            print("   ✅ Установлен")
        
        # Проверяем Supabase Key
        print("\n🔑 Supabase Key:")
        if not settings.SUPABASE_KEY:
            print("   ❌ Не установлен")
            print("   💡 Получите ключ в настройках проекта Supabase")
        elif settings.SUPABASE_KEY == "your_supabase_anon_key_here":
            print("   ⚠️  Установлен примерный ключ")
            print("   💡 Замените на реальный ключ")
        else:
            print("   ✅ Установлен")
        
        # Проверяем другие настройки
        print("\n⚙️  Другие настройки:")
        print(f"   OpenAI Model: {settings.OPENAI_MODEL}")
        print(f"   Max Tokens: {settings.MAX_TOKENS}")
        print(f"   Max Image Size: {settings.MAX_IMAGE_SIZE / (1024*1024):.1f} MB")
        
        # Рекомендации
        print("\n📋 Рекомендации:")
        
        if (not settings.TELEGRAM_BOT_TOKEN or 
            settings.TELEGRAM_BOT_TOKEN == "your_telegram_bot_token_here"):
            print("   1. Получите Telegram Bot Token у @BotFather")
            print("   2. Добавьте его в файл .env")
        
        if (not settings.OPENAI_API_KEY or 
            settings.OPENAI_API_KEY == "your_openai_api_key_here"):
            print("   3. Получите OpenAI API Key на platform.openai.com")
            print("   4. Добавьте его в файл .env")
        
        if (not settings.SUPABASE_URL or 
            settings.SUPABASE_URL == "https://your-project-id.supabase.co" or
            not settings.SUPABASE_KEY or 
            settings.SUPABASE_KEY == "your_supabase_anon_key_here"):
            print("   5. Настройте Supabase для сохранения данных (опционально)")
            print("   6. Выполните SQL из setup_supabase.sql")
        
        print("\n   7. Запустите бота: python main.py")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка проверки конфигурации: {e}")
        return False

def main():
    """Главная функция"""
    if check_config():
        print("\n✅ Проверка завершена!")
    else:
        print("\n❌ Проверка не удалась!")

if __name__ == "__main__":
    main()

