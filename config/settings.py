import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # Telegram Bot
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    
    # OpenAI
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENAI_ORG_ID = os.getenv("OPENAI_ORG_ID")
    
    # Supabase
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")
    
    # App settings
    MAX_IMAGE_SIZE = 20 * 1024 * 1024  # 20MB
    SUPPORTED_FORMATS = ['.jpg', '.jpeg', '.png', '.webp']
    
    # OpenAI Vision settings
    OPENAI_MODEL = "gpt-4o-mini"
    MAX_TOKENS = 1000

    # G4F fallback
    ENABLE_G4F_FALLBACK = os.getenv("ENABLE_G4F_FALLBACK", "false").lower() in ("1", "true", "yes")
    
    # Daily nutrition goals (default values)
    DEFAULT_DAILY_CALORIES = 2000
    DEFAULT_DAILY_PROTEIN = 150  # grams
    DEFAULT_DAILY_FATS = 65      # grams
    DEFAULT_DAILY_CARBS = 250    # grams
    
    # Stripe Configuration
    STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
    STRIPE_PUBLISHABLE_KEY = os.getenv("STRIPE_PUBLISHABLE_KEY")
    STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")
    STRIPE_PRICE_ID_MONTHLY = os.getenv("STRIPE_PRICE_ID_MONTHLY")
    STRIPE_PRICE_ID_YEARLY = os.getenv("STRIPE_PRICE_ID_YEARLY")
    
    # App URL for Stripe redirects
    APP_URL = os.getenv("APP_URL", "https://your-domain.com")
    
    # Subscription settings
    FREE_PHOTO_LIMIT = 1  # First photo is free

settings = Settings()
