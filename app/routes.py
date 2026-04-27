"""
API Routes for Face Attendance Service
GCS version - images GCS mein save hoti hain
"""

from __future__ import annotations

from datetime import datetime
import io
import os
from typing import List, Optional, Dict, Any

import numpy as np
import face_recognition
from PIL import Image

from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session

from app.attendance_excel import (
    export_today_attendance_excel,
    export_attendance_excel,
    generate_summary_excel,
)

from app.config import (
    UPLOADS_DIR,
    ENCODINGS_FILE,
    MIN_ENROLL_PHOTOS,
    ALLOWED_EXTENSIONS,
    MATCH_THRESHOLD,
)

from app.storage import ensure_dirs, load_cache, save_cache

from app.storage_helper import (
    list_student_images_new,
    save_image_to_gcs,
    delete_student_from_gcs,
    count_gcs_images,
)

from app.encoder import encode_images_from_paths
from app.db import get_db
from app.models import Attendance, Student, User
from app.auth import get_current_user

router = APIRouter()


# =========================================================
# Helper: Identify from numpy image array
# =========================================================
def identify_from_image_array(
    img: np.ndarray,
    students: Dict[str, Dict[str, Any]]
):
    face_locations = face_recognition.face_locations(
        img,
        model="hog",
        number_of_times_to_upsample=1
    )

    if len(face_locations) != 1:
        return None, None, None

    face_encoding = face_recognition.face_encodings(
        img,
        face_locations
    )[0]

    best_sid = None
    best_name = None
    best_distance = 999.0

    for sid, data in students.items():
        encodings = data.get("encodings", [])

        if not encodings:
            continue

        distances = face_recognition.face_distance(
            encodings,
            face_encoding
        )

        if len(distances) == 0:
            continue

        d = float(np.min(distances))

        if d < best_distance:
            best_distance = d
            best_sid = sid
            best_name = data.get("name", "")

    return best_sid, best_name, best_distance


# =========================================================
# Health
# =========================================================
@router.get("/health")
def health():
    ensure_dirs()

    return {
        "ok": True,
        "service": "face-attendance",
        "message": "Server running perfectly 🚀",
        "uploads_dir": UPLOADS_DIR,
        "encodings_file": ENCODINGS_FILE,
    }


# =========================================================
# Enroll Student
# =========================================================
@router.post("/enroll")
async def enroll(
    student_id: str = Form(...),
    name: str = Form(""),
    school_name: str = Form(""),
    class_name: str = Form(""),
    section: str = Form(""),
    roll: str = Form(""),
    replace_photos: str = Form("false"),
    files: List[UploadFile] = File([]),
    db: Session = Depends(get_db),
):
    ensure_dirs()

    sid = str(student_id).strip()

    if not sid:
        return {
            "ok": False,
            "message": "Student ID is required."
        }

    name = (name or "").strip()
    school_name = (school_name or "").strip()
    class_name = (class_name or "").strip()
    section = (section or "").strip()
    roll = (roll or "").strip()

    student: Optional[Student] = (
        db.query(Student)
        .filter(Student.id == sid)
        .first()
    )

    if student:
        effective_school = (
            school_name
            or student.school_name
            or "MainSchool"
        )
    else:
        effective_school = school_name or "MainSchool"

    has_files = bool(files)

    replace_flag = (
        (replace_photos or "false")
        .strip()
        .lower()
        in ("1", "true", "yes", "y")
    )

    # --------------------------------
    # Update only details
    # --------------------------------
    if student and not has_files:
        if name:
            student.name = name
        if class_name:
            student.class_name = class_name
        if section:
            student.section = section
        if roll:
            student.roll = roll

        db.commit()

        return {
            "ok": True,
            "message": "Student updated successfully"
        }

    # --------------------------------
    # New student without photos
    # --------------------------------
    if not student and not has_files:
        db.add(
            Student(
                id=sid,
                name=name,
                school_name=effective_school,
                class_name=class_name,
                section=section,
                roll=roll,
            )
        )
        db.commit()

        return {
            "ok": True,
            "message": "Student enrolled successfully"
        }

    # --------------------------------
    # Replace old photos
    # --------------------------------
    if has_files and replace_flag:
        delete_student_from_gcs(
            effective_school,
            class_name,
            section,
            sid
        )

    next_idx = 1

    if has_files and not replace_flag:
        existing_count = count_gcs_images(
            effective_school,
            class_name,
            section,
            sid
        )
        next_idx = existing_count + 1

    # --------------------------------
    # Save images to GCS
    # --------------------------------
    for f in files:
        if not f.filename:
            continue

        ext = os.path.splitext(f.filename)[1].lower()

        if ext not in ALLOWED_EXTENSIONS:
            continue

        image_bytes = await f.read()

        filename = f"img_{next_idx:03d}{ext}"

        save_image_to_gcs(
            effective_school,
            class_name,
            section,
            sid,
            image_bytes,
            filename
        )

        next_idx += 1

    # --------------------------------
    # Encode images
    # --------------------------------
    image_paths = list_student_images_new(
        effective_school,
        class_name,
        section,
        sid
    )

    encodings = encode_images_from_paths(image_paths)

    if len(encodings) < MIN_ENROLL_PHOTOS:
        return {
            "ok": False,
            "message": f"Need minimum {MIN_ENROLL_PHOTOS} valid photos."
        }

    # --------------------------------
    # Save in cache
    # --------------------------------
    cache = load_cache()
    cache.setdefault("students", {})

    cache["students"][sid] = {
        "name": name,
        "encodings": encodings
    }

    save_cache(cache)

    # --------------------------------
    # Save in DB
    # --------------------------------
    if student:
        student.name = name
        student.school_name = effective_school
        student.class_name = class_name
        student.section = section
        student.roll = roll
    else:
        db.add(
            Student(
                id=sid,
                name=name,
                school_name=effective_school,
                class_name=class_name,
                section=section,
                roll=roll,
            )
        )

    db.commit()

    return {
        "ok": True,
        "message": "Enrollment successful"
    }


# =========================================================
# Attendance Export Today
# =========================================================
# IMPORTANT FIX:
# current_user हटाया गया है
# यही तुम्हारा Excel issue था
# =========================================================
@router.get("/attendance/export/today")
def export_today_attendance_excel_route(
    db: Session = Depends(get_db),
):
    return export_today_attendance_excel(db)


# =========================================================
# Attendance Export Custom Range
# =========================================================
@router.get("/attendance/export/excel")
def export_attendance_excel_route(
    start_date: str = None,
    end_date: str = None,
    school_name: str = None,
    class_name: str = None,
    section: str = None,
    db: Session = Depends(get_db),
):
    start_dt = None
    end_dt = None

    if start_date:
        try:
            start_dt = datetime.strptime(
                start_date,
                "%Y-%m-%d"
            ).date()
        except:
            pass

    if end_date:
        try:
            end_dt = datetime.strptime(
                end_date,
                "%Y-%m-%d"
            ).date()
        except:
            pass

    return export_attendance_excel(
        db,
        start_date=start_dt,
        end_date=end_dt,
        school_name=school_name,
        class_name=class_name,
        section=section,
    )


# =========================================================
# Attendance Summary Export
# =========================================================
@router.get("/attendance/export/summary")
def export_summary_excel_route(
    start_date: str = None,
    end_date: str = None,
    school_name: str = None,
    class_name: str = None,
    section: str = None,
    db: Session = Depends(get_db),
):
    start_dt = None
    end_dt = None

    if start_date:
        try:
            start_dt = datetime.strptime(
                start_date,
                "%Y-%m-%d"
            ).date()
        except:
            pass

    if end_date:
        try:
            end_dt = datetime.strptime(
                end_date,
                "%Y-%m-%d"
            ).date()
        except:
            pass

    return generate_summary_excel(
        db,
        start_date=start_dt,
        end_date=end_dt,
        school_name=school_name,
        class_name=class_name,
        section=section,
    )
