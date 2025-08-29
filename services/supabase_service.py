from config.database import db_manager
from models.data_models import User, FoodImage, NutritionData, DailyReport, WaterIntake
from datetime import datetime, date
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)

class SupabaseService:
    def __init__(self):
        self.supabase = db_manager.get_client()
    
    # User operations
    async def create_user(self, user: User) -> User:
        """Создать нового пользователя"""
        try:
            if not self.supabase:
                raise Exception("Supabase client not initialized")
                
            data = {
                "telegram_id": user.telegram_id,
                "username": user.username,
                "daily_calories_goal": user.daily_calories_goal,
                "daily_protein_goal": user.daily_protein_goal,
                "daily_fats_goal": user.daily_fats_goal,
                "daily_carbs_goal": user.daily_carbs_goal
            }
            
            result = self.supabase.table("users").insert(data).execute()
            user_data = result.data[0]
            return User(**user_data)
        except Exception as e:
            logger.error(f"Ошибка создания пользователя: {e}")
            raise
    
    async def get_user_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        """Получить пользователя по telegram_id"""
        try:
            if not self.supabase:
                return None
                
            result = self.supabase.table("users").select("*").eq("telegram_id", telegram_id).execute()
            if result.data:
                return User(**result.data[0])
            return None
        except Exception as e:
            logger.error(f"Ошибка получения пользователя: {e}")
            return None
    
    # FoodImage operations
    async def create_food_image(self, food_image: FoodImage) -> FoodImage:
        """Создать запись о фотографии еды"""
        try:
            if not self.supabase:
                raise Exception("Supabase client not initialized")
                
            data = {
                "user_id": food_image.user_id,
                "image_url": food_image.image_url,
                "status": food_image.status
            }
            
            result = self.supabase.table("food_images").insert(data).execute()
            image_data = result.data[0]
            return FoodImage(**image_data)
        except Exception as e:
            logger.error(f"Ошибка создания записи о фотографии: {e}")
            raise
    
    async def update_food_image_status(self, image_id: int, status: str):
        """Обновить статус фотографии"""
        try:
            if not self.supabase:
                raise Exception("Supabase client not initialized")
                
            self.supabase.table("food_images").update({"status": status}).eq("id", image_id).execute()
        except Exception as e:
            logger.error(f"Ошибка обновления статуса фотографии: {e}")
            raise
    
    # NutritionData operations
    async def create_nutrition_data(self, nutrition_data: NutritionData) -> NutritionData:
        """Создать запись о питательных веществах"""
        try:
            if not self.supabase:
                raise Exception("Supabase client not initialized")
                
            data = {
                "food_image_id": nutrition_data.food_image_id,
                "calories": nutrition_data.calories,
                "protein": nutrition_data.protein,
                "fats": nutrition_data.fats,
                "carbs": nutrition_data.carbs,
                "food_name": nutrition_data.food_name,
                "confidence": nutrition_data.confidence
            }
            
            result = self.supabase.table("nutrition_data").insert(data).execute()
            nutrition_data_dict = result.data[0]
            return NutritionData(**nutrition_data_dict)
        except Exception as e:
            logger.error(f"Ошибка создания данных о питании: {e}")
            raise
    
    # DailyReport operations
    async def get_daily_report(self, user_id: int, report_date: date) -> Optional[DailyReport]:
        """Получить дневной отчет"""
        try:
            if not self.supabase:
                return None
                
            result = self.supabase.table("daily_reports").select("*").eq("user_id", user_id).eq("date", report_date.isoformat()).execute()
            if result.data:
                return DailyReport(**result.data[0])
            return None
        except Exception as e:
            logger.error(f"Ошибка получения дневного отчета: {e}")
            return None
    
    async def create_or_update_daily_report(self, daily_report: DailyReport) -> DailyReport:
        """Создать или обновить дневной отчет"""
        try:
            if not self.supabase:
                raise Exception("Supabase client not initialized")
                
            existing_report = await self.get_daily_report(daily_report.user_id, daily_report.date)
            
            data = {
                "user_id": daily_report.user_id,
                "date": daily_report.date.isoformat(),
                "total_calories": daily_report.total_calories,
                "total_protein": daily_report.total_protein,
                "total_fats": daily_report.total_fats,
                "total_carbs": daily_report.total_carbs
            }
            
            if existing_report:
                result = self.supabase.table("daily_reports").update(data).eq("id", existing_report.id).execute()
            else:
                result = self.supabase.table("daily_reports").insert(data).execute()
            
            report_data = result.data[0]
            return DailyReport(**report_data)
        except Exception as e:
            logger.error(f"Ошибка создания/обновления дневного отчета: {e}")
            raise
    
    # Analytics operations
    async def get_user_nutrition_today(self, user_id: int) -> dict:
        """Получить питание пользователя за сегодня"""
        try:
            if not self.supabase:
                return {"calories": 0, "protein": 0, "fats": 0, "carbs": 0}
                
            today = date.today().isoformat()
            
            # Получаем все записи о питании за сегодня
            # Сначала получаем ID изображений пользователя
            food_images_result = self.supabase.table("food_images").select("id").eq("user_id", user_id).execute()
            food_image_ids = [img["id"] for img in food_images_result.data]
            
            if not food_image_ids:
                return {"calories": 0, "protein": 0, "fats": 0, "carbs": 0}
            
            # Получаем данные о питании
            result = self.supabase.table("nutrition_data").select(
                "calories, protein, fats, carbs"
            ).in_("food_image_id", food_image_ids).gte("created_at", f"{today}T00:00:00").lte("created_at", f"{today}T23:59:59").execute()
            
            total_calories = sum(item["calories"] for item in result.data)
            total_protein = sum(item["protein"] for item in result.data)
            total_fats = sum(item["fats"] for item in result.data)
            total_carbs = sum(item["carbs"] for item in result.data)
            
            return {
                "calories": total_calories,
                "protein": total_protein,
                "fats": total_fats,
                "carbs": total_carbs
            }
        except Exception as e:
            logger.error(f"Ошибка получения питания за сегодня: {e}")
            return {"calories": 0, "protein": 0, "fats": 0, "carbs": 0}
    
    async def get_user_nutrition_week(self, user_id: int) -> dict:
        """Получить питание пользователя за неделю"""
        try:
            if not self.supabase:
                return {
                    "total_calories": 0, "total_protein": 0, "total_fats": 0, "total_carbs": 0,
                    "average_calories": 0, "average_protein": 0, "average_fats": 0, "average_carbs": 0
                }
                
            from datetime import timedelta
            end_date = date.today()
            start_date = end_date - timedelta(days=7)
            
            # Получаем все записи о питании за неделю
            # Сначала получаем ID изображений пользователя
            food_images_result = self.supabase.table("food_images").select("id").eq("user_id", user_id).execute()
            food_image_ids = [img["id"] for img in food_images_result.data]
            
            if not food_image_ids:
                return {
                    "total_calories": 0, "total_protein": 0, "total_fats": 0, "total_carbs": 0,
                    "average_calories": 0, "average_protein": 0, "average_fats": 0, "average_carbs": 0
                }
            
            # Получаем данные о питании
            result = self.supabase.table("nutrition_data").select(
                "calories, protein, fats, carbs, created_at"
            ).in_("food_image_id", food_image_ids).gte("created_at", f"{start_date}T00:00:00").lte("created_at", f"{end_date}T23:59:59").execute()
            
            total_calories = sum(item["calories"] for item in result.data)
            total_protein = sum(item["protein"] for item in result.data)
            total_fats = sum(item["fats"] for item in result.data)
            total_carbs = sum(item["carbs"] for item in result.data)
            
            days_count = 7
            return {
                "total_calories": total_calories,
                "total_protein": total_protein,
                "total_fats": total_fats,
                "total_carbs": total_carbs,
                "average_calories": total_calories / days_count,
                "average_protein": total_protein / days_count,
                "average_fats": total_fats / days_count,
                "average_carbs": total_carbs / days_count
            }
        except Exception as e:
            logger.error(f"Ошибка получения питания за неделю: {e}")
            return {
                "total_calories": 0, "total_protein": 0, "total_fats": 0, "total_carbs": 0,
                "average_calories": 0, "average_protein": 0, "average_fats": 0, "average_carbs": 0
            }

    async def get_water_week(self, user_id: int) -> dict:
        """Получить суммарную воду по дням за последнюю неделю (включая сегодня)"""
        try:
            if not self.supabase:
                return {}
            from datetime import date, timedelta
            end_date = date.today()
            start_date = end_date - timedelta(days=6)
            result = self.supabase.table("water_intake").select(
                "amount_ml, created_at"
            ).eq("user_id", user_id).gte("created_at", f"{start_date}T00:00:00").lte("created_at", f"{end_date}T23:59:59").execute()

            # Агрегируем по дням (YYYY-MM-DD)
            per_day = {}
            for item in result.data:
                day = item["created_at"][0:10]
                per_day[day] = per_day.get(day, 0) + item["amount_ml"]
            return per_day
        except Exception as e:
            logger.error(f"Ошибка получения воды за неделю: {e}")
            return {}

    # Water operations
    async def add_water_intake(self, user_id: int, amount_ml: int) -> WaterIntake:
        try:
            if not self.supabase:
                raise Exception("Supabase client not initialized")
            data = {"user_id": user_id, "amount_ml": amount_ml}
            result = self.supabase.table("water_intake").insert(data).execute()
            return WaterIntake(**result.data[0])
        except Exception as e:
            logger.error(f"Ошибка добавления воды: {e}")
            raise

    async def get_water_today(self, user_id: int) -> int:
        try:
            if not self.supabase:
                return 0
            from datetime import date
            today = date.today().isoformat()
            result = self.supabase.table("water_intake").select("amount_ml,created_at").eq("user_id", user_id).gte("created_at", f"{today}T00:00:00").lte("created_at", f"{today}T23:59:59").execute()
            return sum(item["amount_ml"] for item in result.data)
        except Exception as e:
            logger.error(f"Ошибка получения воды за сегодня: {e}")
            return 0

    async def set_user_water_goal(self, user_id: int, goal_ml: int) -> User:
        try:
            if not self.supabase:
                raise Exception("Supabase client not initialized")
            result = self.supabase.table("users").update({"daily_water_goal_ml": goal_ml}).eq("id", user_id).execute()
            return User(**result.data[0])
        except Exception as e:
            logger.error(f"Ошибка установки нормы воды: {e}")
            raise
