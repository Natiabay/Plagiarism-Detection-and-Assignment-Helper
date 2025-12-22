-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create students table
CREATE TABLE IF NOT EXISTS students (
    id SERIAL PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    full_name TEXT,
    student_id TEXT UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create assignments table
CREATE TABLE IF NOT EXISTS assignments (
    id SERIAL PRIMARY KEY,
    student_id INTEGER REFERENCES students(id) ON DELETE CASCADE,
    filename TEXT NOT NULL,
    original_text TEXT,
    topic TEXT,
    academic_level TEXT,
    word_count INTEGER,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create analysis_results table
CREATE TABLE IF NOT EXISTS analysis_results (
    id SERIAL PRIMARY KEY,
    assignment_id INTEGER REFERENCES assignments(id) ON DELETE CASCADE,
    original_summary TEXT,
    suggested_sources JSONB,
    plagiarism_score FLOAT,
    flagged_sections JSONB,
    research_suggestions TEXT,
    citation_recommendations TEXT,
    confidence_score FLOAT,
    analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create academic_sources table with vector embeddings
CREATE TABLE IF NOT EXISTS academic_sources (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    authors TEXT,
    publication_year INTEGER,
    abstract TEXT,
    full_text TEXT,
    source_type TEXT CHECK (source_type IN ('paper', 'textbook', 'course_material')),
    url TEXT,
    embedding VECTOR(1536),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create index for vector similarity search
CREATE INDEX IF NOT EXISTS academic_sources_embedding_idx ON academic_sources 
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Create index for text search
CREATE INDEX IF NOT EXISTS academic_sources_title_idx ON academic_sources USING gin(to_tsvector('english', title));
CREATE INDEX IF NOT EXISTS academic_sources_abstract_idx ON academic_sources USING gin(to_tsvector('english', abstract));

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS assignments_student_id_idx ON assignments(student_id);
CREATE INDEX IF NOT EXISTS analysis_results_assignment_id_idx ON analysis_results(assignment_id);
CREATE INDEX IF NOT EXISTS students_email_idx ON students(email);
CREATE INDEX IF NOT EXISTS students_student_id_idx ON students(student_id);

-- Insert sample student for testing (password: test123)
-- Password hash for 'test123' using bcrypt
INSERT INTO students (email, password_hash, full_name, student_id) 
VALUES ('test@student.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYqJY5Z5Z5O', 'Test Student', 'STU001')
ON CONFLICT (email) DO NOTHING;

-- Function to calculate cosine similarity
CREATE OR REPLACE FUNCTION cosine_similarity(vec1 vector, vec2 vector)
RETURNS float AS $$
BEGIN
    RETURN 1 - (vec1 <=> vec2);
END;
$$ LANGUAGE plpgsql IMMUTABLE;

