-- SQL скрипт для настройки базы данных Supabase (исправленная версия)
-- Выполните этот скрипт в SQL Editor вашего проекта Supabase

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
    subscription_status VARCHAR(20) DEFAULT 'free',
    photos_analyzed INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Таблица фотографий еды
CREATE TABLE IF NOT EXISTS food_images (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
    image_url TEXT NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Таблица данных о питании
CREATE TABLE IF NOT EXISTS nutrition_data (
    id BIGSERIAL PRIMARY KEY,
    food_image_id BIGINT REFERENCES food_images(id) ON DELETE CASCADE,
    calories DECIMAL(10,2) NOT NULL,
    protein DECIMAL(10,2) NOT NULL,
    fats DECIMAL(10,2) NOT NULL,
    carbs DECIMAL(10,2) NOT NULL,
    food_name VARCHAR(255) NOT NULL,
    confidence DECIMAL(3,2) NOT NULL,
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

-- Индексы для оптимизации запросов
CREATE INDEX IF NOT EXISTS idx_users_telegram_id ON users(telegram_id);
CREATE INDEX IF NOT EXISTS idx_food_images_user_id ON food_images(user_id);
CREATE INDEX IF NOT EXISTS idx_food_images_status ON food_images(status);
CREATE INDEX IF NOT EXISTS idx_nutrition_data_food_image_id ON nutrition_data(food_image_id);
CREATE INDEX IF NOT EXISTS idx_nutrition_data_created_at ON nutrition_data(created_at);
CREATE INDEX IF NOT EXISTS idx_daily_reports_user_date ON daily_reports(user_id, date);
CREATE INDEX IF NOT EXISTS idx_water_intake_user_id ON water_intake(user_id);
CREATE INDEX IF NOT EXISTS idx_water_intake_created_at ON water_intake(created_at);

-- ВАЖНО: Отключаем RLS для упрощения (или используем простые политики)
-- Если нужна безопасность, используйте второй вариант ниже

-- Вариант 1: Отключить RLS (для тестирования)
ALTER TABLE users DISABLE ROW LEVEL SECURITY;
ALTER TABLE food_images DISABLE ROW LEVEL SECURITY;
ALTER TABLE nutrition_data DISABLE ROW LEVEL SECURITY;
ALTER TABLE daily_reports DISABLE ROW LEVEL SECURITY;
ALTER TABLE water_intake DISABLE ROW LEVEL SECURITY;

-- Вариант 2: Простые RLS политики (раскомментируйте если нужна безопасность)
/*
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE food_images ENABLE ROW LEVEL SECURITY;
ALTER TABLE nutrition_data ENABLE ROW LEVEL SECURITY;
ALTER TABLE daily_reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE water_intake ENABLE ROW LEVEL SECURITY;

-- Простые политики - разрешить все операции
CREATE POLICY "Allow all operations on users" ON users FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all operations on food_images" ON food_images FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all operations on nutrition_data" ON nutrition_data FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all operations on daily_reports" ON daily_reports FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all operations on water_intake" ON water_intake FOR ALL USING (true) WITH CHECK (true);
*/

-- Комментарии к таблицам
COMMENT ON TABLE users IS 'Пользователи бота';
COMMENT ON TABLE food_images IS 'Фотографии еды пользователей';
COMMENT ON TABLE nutrition_data IS 'Данные о питательной ценности еды';
COMMENT ON TABLE daily_reports IS 'Дневные отчеты о питании';
COMMENT ON TABLE water_intake IS 'Потребление воды пользователями';

-- Функция для автоматического обновления updated_at (опционально)
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Миграция для существующих пользователей (добавить поле daily_water_goal_ml)
-- Выполните если у вас уже есть таблица users
-- ALTER TABLE users ADD COLUMN IF NOT EXISTS daily_water_goal_ml INTEGER DEFAULT 2000;
