from pydantic import BaseModel
from datetime import datetime, date
from typing import Optional, List
from decimal import Decimal

class User(BaseModel):
    id: Optional[int] = None
    telegram_id: int
    username: Optional[str] = None
    created_at: Optional[datetime] = None
    daily_calories_goal: int = 2000
    daily_protein_goal: int = 150
    daily_fats_goal: int = 65
    daily_carbs_goal: int = 250
    daily_water_goal_ml: int = 2000
    subscription_status: str = "free"  # free, active, expired, canceled
    subscription_plan: Optional[str] = None  # monthly, yearly
    photos_analyzed: int = 0
    total_photos_sent: int = 0  # Общее количество отправленных фото за все время
    stripe_customer_id: Optional[str] = None
    stripe_subscription_id: Optional[str] = None
    subscription_start: Optional[datetime] = None
    subscription_end: Optional[datetime] = None

class FoodImage(BaseModel):
    id: Optional[int] = None
    user_id: int
    image_url: str
    uploaded_at: Optional[datetime] = None
    status: str = "pending"  # pending, processed, error

class NutritionData(BaseModel):
    id: Optional[int] = None
    food_image_id: int
    calories: float
    protein: float
    fats: float
    carbs: float
    food_name: str
    confidence: float
    weight_grams: float | None = None
    created_at: Optional[datetime] = None

class DailyReport(BaseModel):
    id: Optional[int] = None
    user_id: int
    date: date
    total_calories: float = 0
    total_protein: float = 0
    total_fats: float = 0
    total_carbs: float = 0
    created_at: Optional[datetime] = None

class WaterIntake(BaseModel):
    id: Optional[int] = None
    user_id: int
    amount_ml: int
    created_at: Optional[datetime] = None

class NutritionAnalysis(BaseModel):
    """Модель для ответа от OpenAI Vision API"""
    calories: float
    protein: float
    fats: float
    carbs: float
    food_name: str
    confidence: float
    weight_grams: float | None = None

class WeeklyReport(BaseModel):
    """Модель для недельного отчета"""
    user_id: int
    week_start: date
    week_end: date
    total_calories: float
    total_protein: float
    total_fats: float
    total_carbs: float
    average_calories_per_day: float
    average_protein_per_day: float
    average_fats_per_day: float
    average_carbs_per_day: float

class Subscription(BaseModel):
    """Модель подписки пользователя"""
    id: Optional[int] = None
    user_id: int
    status: str = "free"  # free, active, expired
    plan_type: str = "monthly"  # monthly, yearly
    photos_analyzed: int = 0
    photos_limit: int = 1  # 1 для бесплатного, -1 для безлимита
    subscription_start: Optional[datetime] = None
    subscription_end: Optional[datetime] = None
    created_at: Optional[datetime] = None

class Payment(BaseModel):
    """Модель платежа"""
    id: Optional[int] = None
    user_id: int
    amount: float
    currency: str = "USD"
    status: str = "pending"  # pending, completed, failed, refunded
    payment_method: str = "stripe"  # stripe, telegram (legacy)
    stripe_subscription_id: Optional[str] = None
    stripe_session_id: Optional[str] = None
    plan_type: Optional[str] = None  # monthly, yearly
    telegram_payment_charge_id: Optional[str] = None  # для совместимости
    created_at: Optional[datetime] = None
