-- AI Satış Stratejisi Projesi
-- PostgreSQL Initialization Script

-- Create database if it doesn't exist
SELECT 'CREATE DATABASE ai_satis_db'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'ai_satis_db')\gexec

-- Connect to the database
\c ai_satis_db;

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Set timezone
SET timezone = 'Europe/Istanbul';

-- Create initial admin user (will be handled by application)
-- Tables will be created by Alembic migrations