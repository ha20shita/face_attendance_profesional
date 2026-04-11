-- MySQL Database Setup for Face Attendance System
-- Run this script in MySQL to create database and tables

-- Create Database
CREATE DATABASE IF NOT EXISTS face_attendance CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Use the database
USE face_attendance;

-- Students Table
CREATE TABLE IF NOT EXISTS students (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(255) NOT NULL DEFAULT '',
    class_name VARCHAR(100) NOT NULL DEFAULT '',
    section VARCHAR(50) NOT NULL DEFAULT '',
    roll VARCHAR(50) NOT NULL DEFAULT '',
    INDEX idx_student_id (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Attendance Table
CREATE TABLE IF NOT EXISTS attendance (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id VARCHAR(50) NOT NULL,
    date DATE NOT NULL,
    status ENUM('P', 'A', 'H', 'HD', 'L') NOT NULL DEFAULT 'A',
    qr_code INT NOT NULL DEFAULT 0,
    biometric_method ENUM('thumb', 'iris', 'face') NULL,
    rfid_code VARCHAR(50) NULL,
    remark TEXT NULL,
    branch_id INT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NULL ON UPDATE CURRENT_TIMESTAMP,
    in_time TIMESTAMP NULL,
    out_time TIMESTAMP NULL,
    INDEX idx_attendance_student (student_id),
    INDEX idx_attendance_date (date),
    INDEX idx_attendance_status (status),
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Insert sample data (optional)
-- INSERT INTO students (id, name, class_name, section, roll) VALUES 
-- ('STU001', 'John Doe', '10', 'A', '01'),
-- ('STU002', 'Jane Smith', '10', 'A', '02');

SELECT 'MySQL Face Attendance Database Setup Complete!' as message;
