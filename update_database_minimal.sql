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

-- Ensure payments table exists with required columns
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_name = 'payments'
    ) THEN
        CREATE TABLE payments (
            id BIGSERIAL PRIMARY KEY,
            user_id BIGINT REFERENCES users(id) ON DELETE SET NULL,
            amount NUMERIC(18,2) NOT NULL,
            currency TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            payment_method TEXT NOT NULL, -- e.g. 'crypto'
            plan_type TEXT,               -- 'monthly' | 'yearly'
            tx_hash TEXT,                 -- blockchain tx id (optional)
            provider_payment_id TEXT,     -- for non-crypto providers (optional)
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );

        -- Indexes for faster lookups
        CREATE INDEX IF NOT EXISTS idx_payments_user_id ON payments(user_id);
        CREATE INDEX IF NOT EXISTS idx_payments_status ON payments(status);
        CREATE INDEX IF NOT EXISTS idx_payments_created_at ON payments(created_at);
    END IF;

    -- Add missing columns if table already exists
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'payments') THEN
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='payments' AND column_name='provider') THEN
            ALTER TABLE payments ADD COLUMN provider TEXT;
        END IF;
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='payments' AND column_name='user_id') THEN
            ALTER TABLE payments ADD COLUMN user_id BIGINT REFERENCES users(id) ON DELETE SET NULL;
        END IF;
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='payments' AND column_name='amount') THEN
            ALTER TABLE payments ADD COLUMN amount NUMERIC(18,2) NOT NULL DEFAULT 0;
        END IF;
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='payments' AND column_name='currency') THEN
            ALTER TABLE payments ADD COLUMN currency TEXT NOT NULL DEFAULT 'USDT';
        END IF;
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='payments' AND column_name='status') THEN
            ALTER TABLE payments ADD COLUMN status TEXT NOT NULL DEFAULT 'pending';
        END IF;
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='payments' AND column_name='payment_method') THEN
            ALTER TABLE payments ADD COLUMN payment_method TEXT NOT NULL DEFAULT 'crypto';
        END IF;
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='payments' AND column_name='plan_type') THEN
            ALTER TABLE payments ADD COLUMN plan_type TEXT;
        END IF;
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='payments' AND column_name='tx_hash') THEN
            ALTER TABLE payments ADD COLUMN tx_hash TEXT;
        END IF;
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='payments' AND column_name='provider_payment_id') THEN
            ALTER TABLE payments ADD COLUMN provider_payment_id TEXT DEFAULT '';
        END IF;
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='payments' AND column_name='created_at') THEN
            ALTER TABLE payments ADD COLUMN created_at TIMESTAMPTZ NOT NULL DEFAULT NOW();
        END IF;
    END IF;
END $$;

-- Optional: disable RLS for payments to avoid policy issues (enable if you manage policies)
ALTER TABLE IF EXISTS payments DISABLE ROW LEVEL SECURITY;

-- Add weight_grams to nutrition_data (nullable)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name='nutrition_data' AND column_name='weight_grams'
    ) THEN
        ALTER TABLE nutrition_data ADD COLUMN weight_grams NUMERIC(10,2) DEFAULT NULL;
    END IF;
END $$;