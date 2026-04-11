#!/usr/bin/env python3
"""
Test MySQL connection and table creation
"""

import os
from dotenv import load_dotenv

load_dotenv()

from app.db import engine, Base
from app.models import Student, Attendance

def test_mysql_connection():
    try:
        print("🔍 Testing MySQL connection...")
        
        # Test connection
        with engine.connect() as conn:
            print("✅ MySQL connection successful!")
            
        # Create tables
        print("🔨 Creating tables...")
        Base.metadata.create_all(bind=engine)
        print("✅ Tables created successfully!")
        
        # Check tables
        inspector = engine.inspect(engine)
        tables = inspector.get_table_names()
        print(f"📋 Tables in database: {tables}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    test_mysql_connection()
