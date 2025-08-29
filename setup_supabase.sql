-- SQL скрипт для настройки базы данных Supabase
-- Выполните этот скрипт в SQL Editor вашего проекта Supabase

-- Таблица пользователей
CREATE TABLE users (
    id BIGSERIAL PRIMARY KEY,
    telegram_id BIGINT UNIQUE NOT NULL,
    username VARCHAR(255),
    daily_calories_goal INTEGER DEFAULT 2000,
    daily_protein_goal INTEGER DEFAULT 150,
    daily_fats_goal INTEGER DEFAULT 65,
    daily_carbs_goal INTEGER DEFAULT 250,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Таблица фотографий еды
CREATE TABLE food_images (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
    image_url TEXT NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Таблица данных о питании
CREATE TABLE nutrition_data (
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
CREATE TABLE daily_reports (
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

-- Индексы для оптимизации запросов
CREATE INDEX idx_users_telegram_id ON users(telegram_id);
CREATE INDEX idx_food_images_user_id ON food_images(user_id);
CREATE INDEX idx_food_images_status ON food_images(status);
CREATE INDEX idx_nutrition_data_food_image_id ON nutrition_data(food_image_id);
CREATE INDEX idx_nutrition_data_created_at ON nutrition_data(created_at);
CREATE INDEX idx_daily_reports_user_date ON daily_reports(user_id, date);

-- RLS (Row Level Security) политики для безопасности
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE food_images ENABLE ROW LEVEL SECURITY;
ALTER TABLE nutrition_data ENABLE ROW LEVEL SECURITY;
ALTER TABLE daily_reports ENABLE ROW LEVEL SECURITY;

-- Политики для таблицы users (пользователи видят только свои данные)
CREATE POLICY "Users can view own data" ON users
    FOR SELECT USING (true);

CREATE POLICY "Users can insert own data" ON users
    FOR INSERT WITH CHECK (true);

CREATE POLICY "Users can update own data" ON users
    FOR UPDATE USING (true);

-- Политики для таблицы food_images
CREATE POLICY "Users can view own food images" ON food_images
    FOR SELECT USING (user_id IN (SELECT id FROM users WHERE telegram_id = current_setting('app.telegram_user_id', true)::bigint));

CREATE POLICY "Users can insert own food images" ON food_images
    FOR INSERT WITH CHECK (user_id IN (SELECT id FROM users WHERE telegram_id = current_setting('app.telegram_user_id', true)::bigint));

CREATE POLICY "Users can update own food images" ON food_images
    FOR UPDATE USING (user_id IN (SELECT id FROM users WHERE telegram_id = current_setting('app.telegram_user_id', true)::bigint));

-- Политики для таблицы nutrition_data
CREATE POLICY "Users can view own nutrition data" ON nutrition_data
    FOR SELECT USING (food_image_id IN (
        SELECT id FROM food_images WHERE user_id IN (
            SELECT id FROM users WHERE telegram_id = current_setting('app.telegram_user_id', true)::bigint
        )
    ));

CREATE POLICY "Users can insert own nutrition data" ON nutrition_data
    FOR INSERT WITH CHECK (food_image_id IN (
        SELECT id FROM food_images WHERE user_id IN (
            SELECT id FROM users WHERE telegram_id = current_setting('app.telegram_user_id', true)::bigint
        )
    ));

-- Политики для таблицы daily_reports
CREATE POLICY "Users can view own daily reports" ON daily_reports
    FOR SELECT USING (user_id IN (SELECT id FROM users WHERE telegram_id = current_setting('app.telegram_user_id', true)::bigint));

CREATE POLICY "Users can insert own daily reports" ON daily_reports
    FOR INSERT WITH CHECK (user_id IN (SELECT id FROM users WHERE telegram_id = current_setting('app.telegram_user_id', true)::bigint));

CREATE POLICY "Users can update own daily reports" ON daily_reports
    FOR UPDATE USING (user_id IN (SELECT id FROM users WHERE telegram_id = current_setting('app.telegram_user_id', true)::bigint));

-- Комментарии к таблицам
COMMENT ON TABLE users IS 'Пользователи бота';
COMMENT ON TABLE food_images IS 'Фотографии еды пользователей';
COMMENT ON TABLE nutrition_data IS 'Данные о питательной ценности еды';
COMMENT ON TABLE daily_reports IS 'Дневные отчеты о питании';

-- Функция для автоматического обновления updated_at (опционально)
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';
