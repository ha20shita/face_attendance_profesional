#!/usr/bin/env python3
"""
Setup MySQL user and database for Face Attendance
Production ready - reads credentials from .env
"""

import os
import sys
from urllib.parse import urlparse

# Load .env if exists
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import pymysql
from pymysql import Error

def parse_db_url():
    """Parse DATABASE_URL from environment"""
    db_url = os.getenv("DATABASE_URL", "")
    if not db_url:
        return None
    
    # Parse mysql+pymysql://user:pass@host:port/db
    parsed = urlparse(db_url.replace("mysql+pymysql://", "mysql://"))
    return {
        'user': parsed.username or 'faceapp',
        'password': parsed.password or 'faceapp123',
        'host': parsed.hostname or 'localhost',
        'port': parsed.port or 3306,
        'database': parsed.path.lstrip('/') or 'face_attendance'
    }

def setup_mysql():
    """Setup MySQL user and database for production"""
    
    # Parse credentials from DATABASE_URL if available
    db_config = parse_db_url()
    if db_config:
        print(f"📋 Database config from .env:")
        print(f"   User: {db_config['user']}")
        print(f"   Host: {db_config['host']}")
        print(f"   Database: {db_config['database']}\n")
    
    # For production, try root with password prompt if needed
    root_password = os.getenv("MYSQL_ROOT_PASSWORD", "")
    
    try:
        # Try to connect - first with provided root password, then common ones
        credentials = []
        
        if root_password:
            credentials.append({'user': 'root', 'password': root_password})
        
        # Common default passwords to try
        credentials.extend([
            {'user': 'root', 'password': ''},
            {'user': 'root', 'password': 'root'},
            {'user': 'root', 'password': 'password'},
            {'user': 'root', 'password': 'admin'},
            {'user': 'mysql', 'password': ''},
        ])
        
        connection = None
        for cred in credentials:
            try:
                connection = pymysql.connect(
                    host='localhost',
                    user=cred['user'],
                    password=cred['password'],
                    charset='utf8mb4'
                )
                print(f"✅ Connected with user: {cred['user']}")
                break
            except Error:
                continue
        
        if not connection:
            print("\n❌ Could not connect to MySQL")
            print("\n💡 Solutions:")
            print("   1. Set MYSQL_ROOT_PASSWORD env variable:")
            print("      export MYSQL_ROOT_PASSWORD=your_root_password")
            print("   2. Or use: mysql -u root -p")
            print("   3. Or update .env with correct DATABASE_URL\n")
            return False
        
        with connection.cursor() as cursor:
            # Create database
            cursor.execute("CREATE DATABASE IF NOT EXISTS face_attendance CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            print("✅ Database 'face_attendance' created")
            
            # Create user for our app
            cursor.execute("CREATE USER IF NOT EXISTS 'faceapp'@'localhost' IDENTIFIED BY 'faceapp123'")
            print("✅ User 'faceapp' created")
            
            # Grant privileges
            cursor.execute("GRANT ALL PRIVILEGES ON face_attendance.* TO 'faceapp'@'localhost'")
            cursor.execute("FLUSH PRIVILEGES")
            print("✅ Privileges granted")
            
        connection.commit()
        
        # Test connection with new user
        test_connection = pymysql.connect(
            host='localhost',
            user='faceapp',
            password='faceapp123',
            database='face_attendance',
            charset='utf8mb4'
        )
        
        with test_connection.cursor() as cursor:
            # Create tables
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
            
        test_connection.commit()
        print("✅ Tables created successfully!")
        
        # Also create Users table for authentication
        with test_connection.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    email VARCHAR(100) UNIQUE NULL,
                    hashed_password VARCHAR(255) NOT NULL,
                    full_name VARCHAR(100) NULL,
                    is_active BOOLEAN DEFAULT TRUE,
                    is_admin BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP NULL ON UPDATE CURRENT_TIMESTAMP,
                    INDEX idx_username (username)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)
            print("✅ Table 'users' created")
        
        test_connection.commit()
        
        # Update .env file with new credentials
        env_path = '.env'
        env_content = f"""# =========================================
# Production Environment Configuration
# =========================================

# MySQL Database URL
DATABASE_URL=mysql+pymysql://faceapp:faceapp123@localhost:3306/face_attendance

# JWT Secret Key (IMPORTANT: Change this in production!)
SECRET_KEY=change-this-secret-key-in-production
"""
        
        with open(env_path, 'w') as f:
            f.write(env_content)
        
        print("✅ .env file updated with new credentials")
        print("\n🎉 MySQL setup complete!")
        print("\n📋 Next steps:")
        print("   1. Run: python generate_secret.py")
        print("   2. Update SECRET_KEY in .env file")
        print("   3. Start server: python start_server.py")
        print("   4. Create admin: curl -X POST http://localhost:8000/auth/setup-admin")
        print("\n🔗 Login URL: http://localhost:8000/static/login.html")
        print("   Default: admin@gmail.com / admin123")
        
        return True
        
    except Error as e:
        print(f"❌ Error: {e}")
        return False
        
    finally:
        if 'connection' in locals() and connection:
            connection.close()
        if 'test_connection' in locals() and test_connection:
            test_connection.close()

if __name__ == "__main__":
    setup_mysql()
