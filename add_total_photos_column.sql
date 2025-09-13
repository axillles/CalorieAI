-- Добавление колонки total_photos_sent в таблицу users
-- Выполнить этот скрипт в Supabase SQL Editor

ALTER TABLE users 
ADD COLUMN IF NOT EXISTS total_photos_sent INTEGER DEFAULT 0;

-- Обновляем существующих пользователей, устанавливая счетчик на основе количества записей в food_images
UPDATE users 
SET total_photos_sent = (
    SELECT COUNT(*) 
    FROM food_images 
    WHERE food_images.user_id = users.id
);

-- Добавляем комментарий к колонке
COMMENT ON COLUMN users.total_photos_sent IS 'Общее количество отправленных фото за все время';

