import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # Telegram Bot
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    
    # OpenAI
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENAI_ORG_ID = os.getenv("OPENAI_ORG_ID") or None
    
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
    
    # PayPal Configuration
    PAYPAL_CLIENT_ID = os.getenv("PAYPAL_CLIENT_ID")
    PAYPAL_CLIENT_SECRET = os.getenv("PAYPAL_CLIENT_SECRET")
    PAYPAL_BASE_URL = os.getenv("PAYPAL_BASE_URL", "https://api-m.sandbox.paypal.com")  # sandbox по умолчанию
    
    # Payment Provider Settings
    ENABLED_PAYMENT_PROVIDERS = os.getenv("ENABLED_PAYMENT_PROVIDERS", "crypto,telegram_stars").split(",")
    PRIMARY_PAYMENT_PROVIDER = os.getenv("PRIMARY_PAYMENT_PROVIDER", "crypto")
    
    # App URL
    APP_URL = os.getenv("APP_URL", "https://your-domain.com")
    
    # Subscription settings
    FREE_PHOTO_LIMIT = 1  # First photo is free

    # Crypto payments (manual wallet transfer)
    CRYPTO_TON_ADDRESS = os.getenv("CRYPTO_TON_ADDRESS")
    CRYPTO_TRC20_USDT_ADDRESS = os.getenv("CRYPTO_TRC20_USDT_ADDRESS")
    PAYMENT_PROVIDER_NAME = "crypto"

    # TRC20 monitor settings
    ENABLE_TRC20_MONITOR = os.getenv("ENABLE_TRC20_MONITOR", "true").lower() in ("1", "true", "yes")
    TRONGRID_API_KEY = os.getenv("TRONGRID_API_KEY")
    TRC20_CONFIRMATIONS_REQUIRED = int(os.getenv("TRC20_CONFIRMATIONS_REQUIRED", "1"))
    TRC20_AMOUNT_TOLERANCE_USD = float(os.getenv("TRC20_AMOUNT_TOLERANCE_USD", "0.5"))

settings = Settings()
