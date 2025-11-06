-- Run this SQL script to add the question_responses table to existing database
-- Execute this in MySQL Workbench after running the main schema.sql

USE exam_proctoring;

-- Question responses table (to track question timing and answers)
CREATE TABLE IF NOT EXISTS question_responses (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    session_id VARCHAR(255) NOT NULL,
    question_number INT NOT NULL,
    question_type VARCHAR(50) NOT NULL,
    answer TEXT,
    time_taken_seconds INT DEFAULT 0,
    first_viewed_at DATETIME NOT NULL,
    last_updated_at DATETIME NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_session (user_id, session_id),
    INDEX idx_question_number (question_number),
    INDEX idx_session_question (session_id, question_number)
);

