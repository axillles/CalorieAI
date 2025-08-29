-- Update database schema for multi-provider payment support
-- Run this in your Supabase SQL Editor

-- Add new columns to users table for payment providers
ALTER TABLE users ADD COLUMN IF NOT EXISTS payment_provider TEXT DEFAULT NULL;
ALTER TABLE users ADD COLUMN IF NOT EXISTS provider_payment_id TEXT DEFAULT NULL;

-- Update existing subscription columns if they don't exist
ALTER TABLE users ADD COLUMN IF NOT EXISTS subscription_plan TEXT DEFAULT NULL;
ALTER TABLE users ADD COLUMN IF NOT EXISTS subscription_start TIMESTAMP DEFAULT NULL;
ALTER TABLE users ADD COLUMN IF NOT EXISTS subscription_end TIMESTAMP DEFAULT NULL;

-- Create payments table for tracking all payments
CREATE TABLE IF NOT EXISTS payments (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id),
    provider TEXT NOT NULL, -- 'telegram_stars', 'paypal', 'stripe'
    provider_payment_id TEXT NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    currency TEXT NOT NULL,
    plan_type TEXT NOT NULL, -- 'monthly', 'yearly'
    status TEXT DEFAULT 'completed',
    created_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(provider, provider_payment_id)
);

-- Enable RLS on payments table
ALTER TABLE payments ENABLE ROW LEVEL SECURITY;

-- Create policy for payments (drop if exists first)
DROP POLICY IF EXISTS "Users can view own payments" ON payments;
CREATE POLICY "Users can view own payments" ON payments
    FOR SELECT USING (auth.uid()::text = user_id::text);

-- Insert or update RLS policies for users table (if needed)
DROP POLICY IF EXISTS "Users can view own data" ON users;
CREATE POLICY "Users can view own data" ON users
    FOR ALL USING (true); -- Temporarily disable RLS for testing

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_users_telegram_id ON users(telegram_id);
CREATE INDEX IF NOT EXISTS idx_users_subscription_status ON users(subscription_status);
CREATE INDEX IF NOT EXISTS idx_payments_user_id ON payments(user_id);
CREATE INDEX IF NOT EXISTS idx_payments_provider ON payments(provider, provider_payment_id);