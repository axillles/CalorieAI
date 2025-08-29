-- Minimal database update for multi-provider payment support
-- Run this in your Supabase SQL Editor

-- Add new columns to users table for payment providers (only if they don't exist)
DO $$ 
BEGIN 
    -- Add payment_provider column
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='users' AND column_name='payment_provider') THEN
        ALTER TABLE users ADD COLUMN payment_provider TEXT DEFAULT NULL;
    END IF;
    
    -- Add provider_payment_id column
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='users' AND column_name='provider_payment_id') THEN
        ALTER TABLE users ADD COLUMN provider_payment_id TEXT DEFAULT NULL;
    END IF;
    
    -- Add subscription_plan column
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='users' AND column_name='subscription_plan') THEN
        ALTER TABLE users ADD COLUMN subscription_plan TEXT DEFAULT NULL;
    END IF;
    
    -- Add subscription_start column
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='users' AND column_name='subscription_start') THEN
        ALTER TABLE users ADD COLUMN subscription_start TIMESTAMP DEFAULT NULL;
    END IF;
    
    -- Add subscription_end column
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='users' AND column_name='subscription_end') THEN
        ALTER TABLE users ADD COLUMN subscription_end TIMESTAMP DEFAULT NULL;
    END IF;
END $$;