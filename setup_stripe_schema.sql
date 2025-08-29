-- ================================================
-- ОБНОВЛЕННАЯ СХЕМА БД ДЛЯ ПОДДЕРЖКИ STRIPE
-- ================================================

-- Обновление таблицы пользователей для поддержки Stripe
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS subscription_plan VARCHAR(50),
ADD COLUMN IF NOT EXISTS stripe_customer_id VARCHAR(255),
ADD COLUMN IF NOT EXISTS stripe_subscription_id VARCHAR(255),
ADD COLUMN IF NOT EXISTS subscription_start TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS subscription_end TIMESTAMP WITH TIME ZONE;

-- Обновление таблицы платежей для поддержки Stripe
ALTER TABLE payments 
ADD COLUMN IF NOT EXISTS stripe_subscription_id VARCHAR(255),
ADD COLUMN IF NOT EXISTS stripe_session_id VARCHAR(255),
ADD COLUMN IF NOT EXISTS plan_type VARCHAR(50);

-- Обновление значений по умолчанию для payment_method
ALTER TABLE payments 
ALTER COLUMN payment_method SET DEFAULT 'stripe';

-- Создание индексов для оптимизации запросов
CREATE INDEX IF NOT EXISTS idx_users_stripe_customer_id ON users(stripe_customer_id);
CREATE INDEX IF NOT EXISTS idx_users_stripe_subscription_id ON users(stripe_subscription_id);
CREATE INDEX IF NOT EXISTS idx_users_subscription_status ON users(subscription_status);
CREATE INDEX IF NOT EXISTS idx_payments_stripe_subscription_id ON payments(stripe_subscription_id);
CREATE INDEX IF NOT EXISTS idx_payments_stripe_session_id ON payments(stripe_session_id);

-- ================================================
-- ПОЛНАЯ СХЕМА БД (для новых установок)
-- ================================================

-- Таблица пользователей
CREATE TABLE IF NOT EXISTS users (
    id BIGSERIAL PRIMARY KEY,
    telegram_id BIGINT UNIQUE NOT NULL,
    username VARCHAR(255),
    daily_calories_goal INTEGER DEFAULT 2000,
    daily_protein_goal INTEGER DEFAULT 150,
    daily_fats_goal INTEGER DEFAULT 65,
    daily_carbs_goal INTEGER DEFAULT 250,
    daily_water_goal_ml INTEGER DEFAULT 2000,
    subscription_status VARCHAR(50) DEFAULT 'free', -- free, active, expired, canceled
    subscription_plan VARCHAR(50), -- monthly, yearly
    photos_analyzed INTEGER DEFAULT 0,
    stripe_customer_id VARCHAR(255),
    stripe_subscription_id VARCHAR(255),
    subscription_start TIMESTAMP WITH TIME ZONE,
    subscription_end TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Таблица изображений еды
CREATE TABLE IF NOT EXISTS food_images (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
    image_url TEXT NOT NULL,
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    status VARCHAR(50) DEFAULT 'pending' -- pending, processed, error
);

-- Таблица анализа питания
CREATE TABLE IF NOT EXISTS nutrition_data (
    id BIGSERIAL PRIMARY KEY,
    food_image_id BIGINT REFERENCES food_images(id) ON DELETE CASCADE,
    calories DECIMAL(10,2) NOT NULL,
    protein DECIMAL(10,2) NOT NULL,
    fats DECIMAL(10,2) NOT NULL,
    carbs DECIMAL(10,2) NOT NULL,
    food_name VARCHAR(255) NOT NULL,
    confidence DECIMAL(5,2) DEFAULT 0.8,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Таблица дневных отчетов
CREATE TABLE IF NOT EXISTS daily_reports (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    total_calories DECIMAL(10,2) DEFAULT 0,
    total_protein DECIMAL(10,2) DEFAULT 0,
    total_fats DECIMAL(10,2) DEFAULT 0,
    total_carbs DECIMAL(10,2) DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, date)
);

-- Таблица потребления воды
CREATE TABLE IF NOT EXISTS water_intake (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
    amount_ml INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Таблица платежей (обновленная для Stripe)
CREATE TABLE IF NOT EXISTS payments (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
    amount DECIMAL(10,2) NOT NULL,
    currency VARCHAR(10) DEFAULT 'USD',
    status VARCHAR(50) DEFAULT 'pending', -- pending, completed, failed, refunded
    payment_method VARCHAR(50) DEFAULT 'stripe', -- stripe, telegram
    stripe_subscription_id VARCHAR(255),
    stripe_session_id VARCHAR(255),
    plan_type VARCHAR(50), -- monthly, yearly
    telegram_payment_charge_id VARCHAR(255), -- для совместимости с legacy
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Создание индексов для оптимизации
CREATE INDEX IF NOT EXISTS idx_users_telegram_id ON users(telegram_id);
CREATE INDEX IF NOT EXISTS idx_users_stripe_customer_id ON users(stripe_customer_id);
CREATE INDEX IF NOT EXISTS idx_users_stripe_subscription_id ON users(stripe_subscription_id);
CREATE INDEX IF NOT EXISTS idx_users_subscription_status ON users(subscription_status);
CREATE INDEX IF NOT EXISTS idx_food_images_user_id ON food_images(user_id);
CREATE INDEX IF NOT EXISTS idx_nutrition_data_food_image_id ON nutrition_data(food_image_id);
CREATE INDEX IF NOT EXISTS idx_daily_reports_user_date ON daily_reports(user_id, date);
CREATE INDEX IF NOT EXISTS idx_water_intake_user_date ON water_intake(user_id, DATE(created_at));
CREATE INDEX IF NOT EXISTS idx_payments_user_id ON payments(user_id);
CREATE INDEX IF NOT EXISTS idx_payments_stripe_subscription_id ON payments(stripe_subscription_id);
CREATE INDEX IF NOT EXISTS idx_payments_stripe_session_id ON payments(stripe_session_id);

-- ================================================
-- ФУНКЦИИ ДЛЯ УПРАВЛЕНИЯ ПОДПИСКАМИ
-- ================================================

-- Функция для проверки активной подписки
CREATE OR REPLACE FUNCTION check_active_subscription(user_telegram_id BIGINT)
RETURNS BOOLEAN AS $$
DECLARE
    user_data RECORD;
BEGIN
    SELECT subscription_status, subscription_end INTO user_data
    FROM users 
    WHERE telegram_id = user_telegram_id;
    
    IF NOT FOUND THEN
        RETURN FALSE;
    END IF;
    
    -- Проверяем статус и срок действия
    IF user_data.subscription_status = 'active' AND 
       (user_data.subscription_end IS NULL OR user_data.subscription_end > NOW()) THEN
        RETURN TRUE;
    END IF;
    
    RETURN FALSE;
END;
$$ LANGUAGE plpgsql;

-- Функция для обновления истекших подписок
CREATE OR REPLACE FUNCTION update_expired_subscriptions()
RETURNS INTEGER AS $$
DECLARE
    updated_count INTEGER;
BEGIN
    UPDATE users 
    SET subscription_status = 'expired'
    WHERE subscription_status = 'active' 
    AND subscription_end IS NOT NULL 
    AND subscription_end < NOW();
    
    GET DIAGNOSTICS updated_count = ROW_COUNT;
    RETURN updated_count;
END;
$$ LANGUAGE plpgsql;

-- ================================================
-- RLS ПОЛИТИКИ (Row Level Security)
-- ================================================

-- Включаем RLS для таблицы пользователей
ALTER TABLE users ENABLE ROW LEVEL SECURITY;

-- Политика для пользователей: пользователи могут видеть только свои данные
CREATE POLICY users_policy ON users
    FOR ALL USING (auth.uid() = id::text OR auth.role() = 'service_role');

-- Включаем RLS для остальных таблиц
ALTER TABLE food_images ENABLE ROW LEVEL SECURITY;
ALTER TABLE nutrition_data ENABLE ROW LEVEL SECURITY;
ALTER TABLE daily_reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE water_intake ENABLE ROW LEVEL SECURITY;
ALTER TABLE payments ENABLE ROW LEVEL SECURITY;

-- Политики для таблиц с внешними ключами на users
CREATE POLICY food_images_policy ON food_images
    FOR ALL USING (auth.uid() IN (SELECT id::text FROM users WHERE users.id = food_images.user_id) OR auth.role() = 'service_role');

CREATE POLICY nutrition_data_policy ON nutrition_data
    FOR ALL USING (auth.uid() IN (SELECT users.id::text FROM users JOIN food_images ON users.id = food_images.user_id WHERE food_images.id = nutrition_data.food_image_id) OR auth.role() = 'service_role');

CREATE POLICY daily_reports_policy ON daily_reports
    FOR ALL USING (auth.uid() IN (SELECT id::text FROM users WHERE users.id = daily_reports.user_id) OR auth.role() = 'service_role');

CREATE POLICY water_intake_policy ON water_intake
    FOR ALL USING (auth.uid() IN (SELECT id::text FROM users WHERE users.id = water_intake.user_id) OR auth.role() = 'service_role');

CREATE POLICY payments_policy ON payments
    FOR ALL USING (auth.uid() IN (SELECT id::text FROM users WHERE users.id = payments.user_id) OR auth.role() = 'service_role');

-- ================================================
-- КОММЕНТАРИИ К ТАБЛИЦАМ
-- ================================================

COMMENT ON TABLE users IS 'Таблица пользователей Telegram бота';
COMMENT ON TABLE food_images IS 'Таблица загруженных изображений еды';
COMMENT ON TABLE nutrition_data IS 'Таблица результатов анализа питания';
COMMENT ON TABLE daily_reports IS 'Таблица дневных отчетов по питанию';
COMMENT ON TABLE water_intake IS 'Таблица учета потребления воды';
COMMENT ON TABLE payments IS 'Таблица платежей и подписок';

COMMENT ON COLUMN users.subscription_status IS 'Статус подписки: free, active, expired, canceled';
COMMENT ON COLUMN users.subscription_plan IS 'Тип подписки: monthly, yearly';
COMMENT ON COLUMN users.photos_analyzed IS 'Количество проанализированных фото (для лимитов)';
COMMENT ON COLUMN users.stripe_customer_id IS 'ID клиента в Stripe';
COMMENT ON COLUMN users.stripe_subscription_id IS 'ID подписки в Stripe';
COMMENT ON COLUMN payments.payment_method IS 'Способ оплаты: stripe, telegram (legacy)';
COMMENT ON COLUMN payments.status IS 'Статус платежа: pending, completed, failed, refunded';