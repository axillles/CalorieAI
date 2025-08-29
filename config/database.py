from supabase import create_client, Client
from config.settings import settings
import logging

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self):
        self.supabase: Client = None
        self._connect()
    
    def _connect(self):
        """Подключение к Supabase"""
        try:
            self.supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
            logger.info("Успешное подключение к Supabase")
        except Exception as e:
            logger.error(f"Ошибка подключения к Supabase: {e}")
            # Не вызываем raise, чтобы приложение могло запуститься без БД для тестирования
            logger.warning("Приложение запускается без подключения к базе данных")
    
    def get_client(self) -> Client:
        """Получить клиент Supabase"""
        return self.supabase

# Глобальный экземпляр менеджера БД
db_manager = DatabaseManager()
