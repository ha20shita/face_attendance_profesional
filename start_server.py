#!/usr/bin/env python3
"""
Production server startup script with checks
"""

import os
import sys
import subprocess
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def check_env():
    """Check required environment variables"""
    print("🔍 Checking environment variables...")
    
    db_url = os.getenv("DATABASE_URL")
    secret_key = os.getenv("SECRET_KEY")
    
    if not db_url:
        print("❌ DATABASE_URL not set!")
        print("   Add to .env: DATABASE_URL=mysql+pymysql://user:pass@host:3306/db")
        return False
    
    if not secret_key or secret_key == "change-this-secret-key-in-production":
        print("⚠️  WARNING: Using default SECRET_KEY!")
        print("   Run: python generate_secret.py")
        print("   Then update .env file\n")
    else:
        print("✅ SECRET_KEY is set")
    
    # Check if SQLite or MySQL
    if "sqlite" in db_url.lower():
        print("⚠️  Using SQLite (for development only)")
    else:
        print(f"✅ Database URL configured")
    
    return True

def test_database_connection():
    """Test database connection"""
    print("\n🔍 Testing database connection...")
    
    try:
        from sqlalchemy import create_engine
        from sqlalchemy.exc import OperationalError
        
        db_url = os.getenv("DATABASE_URL")
        engine = create_engine(db_url, pool_pre_ping=True)
        
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        
        print("✅ Database connection successful!")
        return True
        
    except OperationalError as e:
        print(f"❌ Database connection failed!")
        print(f"   Error: {e}")
        print("\n💡 Troubleshooting:")
        print("   1. Check if MySQL is running")
        print("   2. Verify DATABASE_URL in .env")
        print("   3. Check MySQL username/password")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def create_tables():
    """Create database tables"""
    print("\n🔍 Creating database tables...")
    
    try:
        from app.db import engine, Base
        Base.metadata.create_all(bind=engine)
        print("✅ Tables created/verified successfully!")
        return True
    except Exception as e:
        print(f"❌ Failed to create tables: {e}")
        return False

def start_server():
    """Start the uvicorn server"""
    print("\n🚀 Starting server...")
    print("=" * 50)
    
    host = os.getenv("HOST", "0.0.0.0")
    port = os.getenv("PORT", "8000")
    
    print(f"📡 Server will run on: http://{host}:{port}")
    print(f"🔗 Frontend URL: http://{host}:{port}/static/login.html")
    print("=" * 50 + "\n")
    
    # Start server
    subprocess.run([
        sys.executable, "-m", "uvicorn",
        "main:app",
        "--host", host,
        "--port", port,
        "--reload", "false"
    ])

def main():
    """Main function"""
    print("=" * 50)
    print("🎓 Face Attendance - Production Startup")
    print("=" * 50 + "\n")
    
    # Check environment
    if not check_env():
        sys.exit(1)
    
    # Test database
    if not test_database_connection():
        response = input("\n⚠️  Database not connected. Start anyway? (y/N): ")
        if response.lower() != 'y':
            sys.exit(1)
    
    # Create tables
    if not create_tables():
        print("⚠️  Continuing despite table creation issues...")
    
    # Start server
    start_server()

if __name__ == "__main__":
    main()
