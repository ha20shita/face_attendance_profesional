#!/usr/bin/env python3
"""
Create MySQL database and tables using Python
"""

import pymysql
from pymysql import Error

def create_mysql_database():
    """Create face_attendance database and tables"""
    
    # Connection parameters for MySQL server (without database)
    try:
        # Connect to MySQL server
        connection = pymysql.connect(
            host='localhost',
            user='root',
            password='',  # Try empty password
            charset='utf8mb4'
        )
        
        print("✅ Connected to MySQL server")
        
        with connection.cursor() as cursor:
            # Create database
            cursor.execute("CREATE DATABASE IF NOT EXISTS face_attendance CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            print("✅ Database 'face_attendance' created")
            
            # Use the database
            cursor.execute("USE face_attendance")
            
            # Create students table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS students (
                    id VARCHAR(50) PRIMARY KEY,
                    name VARCHAR(255) NOT NULL DEFAULT '',
                    class_name VARCHAR(100) NOT NULL DEFAULT '',
                    section VARCHAR(50) NOT NULL DEFAULT '',
                    roll VARCHAR(50) NOT NULL DEFAULT '',
                    INDEX idx_student_id (id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)
            print("✅ Table 'students' created")
            
            # Create attendance table
            cursor.execute("""
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
                    INDEX idx_attendance_status (status)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)
            print("✅ Table 'attendance' created")
            
        connection.commit()
        print("🎉 MySQL database setup complete!")
        
    except Error as e:
        print(f"❌ MySQL Error: {e}")
        print("💡 Please check:")
        print("   - MySQL is running")
        print("   - Username/password are correct")
        print("   - MySQL server is accessible")
        
    finally:
        if 'connection' in locals() and connection:
            connection.close()

if __name__ == "__main__":
    create_mysql_database()
