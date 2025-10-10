-- Create custom enum type for user roles
CREATE TYPE role AS ENUM ('user', 'admin');

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    avatar_s3_key VARCHAR(255),
    email VARCHAR(100) UNIQUE,
    lichess_username VARCHAR(50) UNIQUE,
    chess_dot_com_username VARCHAR(50) UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    role role NOT NULL DEFAULT 'user'
);
