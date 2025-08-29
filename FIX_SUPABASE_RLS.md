# 🔧 Исправление проблемы с RLS в Supabase

## Проблема
Бот выдает ошибку: `new row violates row-level security policy for table "food_images"`

Это происходит из-за настроенных RLS (Row Level Security) политик в Supabase, которые блокируют вставку данных.

## Решение

### Вариант 1: Быстрое исправление (рекомендуется для тестирования)

1. Откройте **Supabase Dashboard**
2. Перейдите в **SQL Editor**
3. Выполните следующие команды:

```sql
-- Отключить RLS для всех таблиц
ALTER TABLE users DISABLE ROW LEVEL SECURITY;
ALTER TABLE food_images DISABLE ROW LEVEL SECURITY;
ALTER TABLE nutrition_data DISABLE ROW LEVEL SECURITY;
ALTER TABLE daily_reports DISABLE ROW LEVEL SECURITY;
```

### Вариант 2: Использовать исправленный SQL файл

1. Откройте файл `setup_supabase_fixed.sql`
2. Скопируйте содержимое
3. Вставьте в **SQL Editor** Supabase
4. Выполните скрипт

### Вариант 3: Простые RLS политики (для безопасности)

Если хотите сохранить безопасность, выполните:

```sql
-- Включить RLS
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE food_images ENABLE ROW LEVEL SECURITY;
ALTER TABLE nutrition_data ENABLE ROW LEVEL SECURITY;
ALTER TABLE daily_reports ENABLE ROW LEVEL SECURITY;

-- Удалить старые политики
DROP POLICY IF EXISTS "Users can view own data" ON users;
DROP POLICY IF EXISTS "Users can insert own data" ON users;
DROP POLICY IF EXISTS "Users can update own data" ON users;
DROP POLICY IF EXISTS "Users can view own food images" ON food_images;
DROP POLICY IF EXISTS "Users can insert own food images" ON food_images;
DROP POLICY IF EXISTS "Users can update own food images" ON food_images;
DROP POLICY IF EXISTS "Users can view own nutrition data" ON nutrition_data;
DROP POLICY IF EXISTS "Users can insert own nutrition data" ON nutrition_data;
DROP POLICY IF EXISTS "Users can view own daily reports" ON daily_reports;
DROP POLICY IF EXISTS "Users can insert own daily reports" ON daily_reports;
DROP POLICY IF EXISTS "Users can update own daily reports" ON daily_reports;

-- Создать простые политики
CREATE POLICY "Allow all operations on users" ON users FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all operations on food_images" ON food_images FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all operations on nutrition_data" ON nutrition_data FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all operations on daily_reports" ON daily_reports FOR ALL USING (true) WITH CHECK (true);
```

## После исправления

1. Перезапустите бота
2. Попробуйте отправить фотографию снова
3. Бот должен работать без ошибок RLS

## Примечание

- **Вариант 1** - самый простой, но отключает безопасность
- **Вариант 3** - сохраняет RLS, но разрешает все операции
- Для продакшена рекомендуется настроить правильные RLS политики с аутентификацией
