"""
Global configuration for Face Attendance Service

✔ All paths
✔ Thresholds
✔ Server settings
✔ Database config
✔ Centralized constants

If anything changes, edit ONLY this file.
"""

import os


# ==============================
# Project Paths
# ==============================

# app/ folder
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Face attendance/ (project root)
PROJECT_ROOT = os.path.dirname(BASE_DIR)


# ==============================
# Storage
# ==============================

# uploads/students/{school_name}/{class_name}/{section}/{student_id}/images
UPLOADS_DIR = os.path.join(PROJECT_ROOT, "uploads", "students")

# data/ folder for cache/logs
DATA_DIR = os.path.join(PROJECT_ROOT, "data")

# face encodings cache file (pickle)
ENCODINGS_FILE = os.path.join(DATA_DIR, "encodings.pkl")


# ==============================
# 🟢 Database (MySQL)
# ==============================
# MySQL Database - configure via .env: mysql+pymysql://user:pass@host:3306/dbname
DB_URL = os.getenv(
    "DATABASE_URL",
    "mysql+pymysql://faceapp:faceapp123@34.76.226.12:3306/face_attendance"
)


# ==============================
# Face Recognition Settings
# ==============================

# Minimum good photos required to enroll
MIN_ENROLL_PHOTOS = 8

# Matching threshold (lower = strict, higher = loose)
# 0.45–0.55 is ideal
MATCH_THRESHOLD = 0.50

# Margin between best and second match
MATCH_MARGIN = 0.05


# ==============================
# ✅ Server (NETWORK ACCESS)
# ==============================

HOST = "0.0.0.0"   # ✅ changed from 127.0.0.1 (allows other systems to access)
PORT = int(os.getenv("PORT", 8080))


# ==============================
# Misc
# ==============================

ALLOWED_EXTENSIONS = (".jpg", ".jpeg", ".png")
