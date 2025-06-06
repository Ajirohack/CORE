-- Superior RAG System Database Initialization Script
-- Creates the necessary tables and indexes for the PostgreSQL database

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgvector";

-- Documents table
CREATE TABLE IF NOT EXISTS documents (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    source TEXT,
    content_type TEXT,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP WITH TIME ZONE
);

-- Create indexes on documents table
CREATE INDEX idx_documents_title ON documents USING GIN (to_tsvector('english', title));
CREATE INDEX idx_documents_metadata ON documents USING GIN (metadata);
CREATE INDEX idx_documents_created_at ON documents (created_at);

-- Document chunks table
CREATE TABLE IF NOT EXISTS document_chunks (
    id SERIAL PRIMARY KEY,
    document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    embedding VECTOR(1536),
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (document_id, chunk_index)
);

-- Create indexes on document_chunks table
CREATE INDEX idx_document_chunks_document_id ON document_chunks(document_id);
CREATE INDEX idx_document_chunks_content ON document_chunks USING GIN (to_tsvector('english', content));
CREATE INDEX idx_document_chunks_embedding ON document_chunks USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) NOT NULL UNIQUE,
    email VARCHAR(255) UNIQUE,
    password_hash TEXT,
    full_name TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    is_admin BOOLEAN DEFAULT FALSE,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_login_at TIMESTAMP WITH TIME ZONE
);

-- API keys table
CREATE TABLE IF NOT EXISTS api_keys (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    key TEXT NOT NULL UNIQUE,
    scopes TEXT[] DEFAULT '{}',
    is_active BOOLEAN DEFAULT TRUE,
    expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_used_at TIMESTAMP WITH TIME ZONE
);

-- Create index on API keys
CREATE INDEX idx_api_keys_key ON api_keys(key);
CREATE INDEX idx_api_keys_user_id ON api_keys(user_id);

-- Conversations table
CREATE TABLE IF NOT EXISTS conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    title TEXT,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create index on conversations
CREATE INDEX idx_conversations_user_id ON conversations(user_id);
CREATE INDEX idx_conversations_created_at ON conversations(created_at);

-- Messages table
CREATE TABLE IF NOT EXISTS messages (
    id SERIAL PRIMARY KEY,
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    role VARCHAR(50) NOT NULL, -- 'user', 'assistant', 'system'
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create index on messages
CREATE INDEX idx_messages_conversation_id ON messages(conversation_id);
CREATE INDEX idx_messages_created_at ON messages(created_at);

-- Feedback table
CREATE TABLE IF NOT EXISTS feedback (
    id SERIAL PRIMARY KEY,
    message_id INTEGER REFERENCES messages(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    rating INTEGER, -- e.g., 1-5 scale
    feedback_text TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create index on feedback
CREATE INDEX idx_feedback_message_id ON feedback(message_id);
CREATE INDEX idx_feedback_user_id ON feedback(user_id);

-- Query logs table
CREATE TABLE IF NOT EXISTS query_logs (
    id SERIAL PRIMARY KEY,
    conversation_id UUID REFERENCES conversations(id) ON DELETE SET NULL,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    query TEXT NOT NULL,
    transformed_query TEXT,
    response TEXT,
    documents_retrieved JSONB,
    duration_ms INTEGER,
    embedding_duration_ms INTEGER,
    retrieval_duration_ms INTEGER,
    llm_duration_ms INTEGER,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create index on query_logs
CREATE INDEX idx_query_logs_user_id ON query_logs(user_id);
CREATE INDEX idx_query_logs_conversation_id ON query_logs(conversation_id);
CREATE INDEX idx_query_logs_created_at ON query_logs(created_at);
CREATE INDEX idx_query_logs_query ON query_logs USING GIN (to_tsvector('english', query));

-- Memory items table
CREATE TABLE IF NOT EXISTS memory_items (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    embedding VECTOR(1536),
    memory_type VARCHAR(50) NOT NULL, -- 'working', 'short_term', 'long_term'
    importance FLOAT DEFAULT 0.5,
    access_count INTEGER DEFAULT 1,
    last_accessed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes on memory_items
CREATE INDEX idx_memory_items_user_id ON memory_items(user_id);
CREATE INDEX idx_memory_items_conversation_id ON memory_items(conversation_id);
CREATE INDEX idx_memory_items_memory_type ON memory_items(memory_type);
CREATE INDEX idx_memory_items_embedding ON memory_items USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);
CREATE INDEX idx_memory_items_expires_at ON memory_items(expires_at);

-- Create admin user (password: admin)
INSERT INTO users (username, email, password_hash, full_name, is_admin)
VALUES ('admin', 'admin@example.com', 
        '$2b$12$RA9UBsBIJ9RM9aG0bxS81.Kn1.7EymACgcPWcnKwTdMGI5.YFG3o6', 
        'System Administrator', TRUE)
ON CONFLICT (username) DO NOTHING;

-- Create default API key for admin user
INSERT INTO api_keys (user_id, name, key)
SELECT id, 'Default Admin Key', 'sk-admin-' || substr(md5(random()::text), 0, 30)
FROM users WHERE username = 'admin'
ON CONFLICT DO NOTHING;