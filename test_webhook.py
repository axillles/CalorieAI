"""
Тест веб-хук сервера
"""
import requests
import time
import subprocess
import sys
import os

def test_webhook_server():
    """Тестирует веб-хук сервер"""
    print("🧪 Тестирование веб-хук сервера...")
    
    # Запускаем сервер в фоне
    print("🚀 Запуск веб-хук сервера...")
    process = subprocess.Popen([sys.executable, "main_webhook.py"], 
                              stdout=subprocess.PIPE, 
                              stderr=subprocess.PIPE)
    
    # Ждем запуска
    print("⏳ Ожидание запуска сервера...")
    time.sleep(10)
    
    try:
        # Тестируем health check
        print("🔍 Тестирование /health endpoint...")
        response = requests.get("http://localhost:8001/health", timeout=5)
        print(f"✅ Health check ответ: {response.status_code}")
        print(f"📄 Содержимое: {response.text}")
        
        if response.status_code == 200:
            print("🎉 Веб-хук сервер работает корректно!")
        else:
            print("❌ Веб-хук сервер не отвечает корректно")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка подключения: {e}")
        
    finally:
        # Останавливаем сервер
        print("🛑 Остановка сервера...")
        process.terminate()
        process.wait()

if __name__ == "__main__":
    test_webhook_server()
