"""
API Routes for Face Attendance Service
GCS version - images GCS mein save hoti hain
"""

from __future__ import annotations

from datetime import datetime
import io
import os
import re
import shutil
from typing import List, Optional, Dict, Any

import numpy as np
import face_recognition
from PIL import Image

from fastapi import APIRouter, Depends, File, Form, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.attendance_excel import export_today_attendance_excel, export_attendance_excel, generate_summary_excel

from app.config import (
    UPLOADS_DIR,
    ENCODINGS_FILE,
    MIN_ENROLL_PHOTOS,
    ALLOWED_EXTENSIONS,
    MATCH_THRESHOLD,
)
from app.storage import ensure_dirs, load_cache, save_cache
from app.storage_helper import (
    get_student_folder_path,
    ensure_student_folder,
    list_student_images_new,
    save_image_to_gcs,
    delete_student_from_gcs,
    count_gcs_images,
    get_student_gcs_prefix,
)
from app.encoder import encode_images_from_paths
from app.db import get_db
from app.models import Attendance, Student, User
from app.auth import get_current_user

router = APIRouter()


# =========================================================
# Helper: Identify from numpy image array
# =========================================================
def identify_from_image_array(img: np.ndarray, students: Dict[str, Dict[str, Any]]):
    face_locations = face_recognition.face_locations(
        img, model="hog", number_of_times_to_upsample=1
    )

    if len(face_locations) != 1:
        return None, None, None

    face_encoding = face_recognition.face_encodings(img, face_locations)[0]

    best_sid = None
    best_name = None
    best_distance = 999.0

    for sid, data in students.items():
        encodings = data.get("encodings", [])
        if not encodings:
            continue

        distances = face_recognition.face_distance(encodings, face_encoding)
        if len(distances) == 0:
            continue

        d = float(np.min(distances))
        if d < best_distance:
            best_distance = d
            best_sid = sid
            best_name = data.get("name", "")

    return best_sid, best_name, best_distance


# ==============================
# Health
# ==============================
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


# ==============================
# Enroll / Update / Photo Update
# ==============================
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
        return {"ok": False, "message": "Student ID is required."}

    name = (name or "").strip()
    school_name = (school_name or "").strip()
    class_name = (class_name or "").strip()
    section = (section or "").strip()
    roll = (roll or "").strip()

    if class_name and "-" in class_name and not section:
        parts = class_name.split("-", 1)
        class_name = parts[0].strip()
        section = parts[1].strip()

    student: Optional[Student] = db.query(Student).filter(Student.id == sid).first()

    if student:
        effective_school = school_name or student.school_name or "MainSchool"
    else:
        effective_school = school_name or "MainSchool"

    has_files = bool(files)
    replace_flag = (replace_photos or "false").strip().lower() in ("1", "true", "yes", "y")

    # ------------------------------
    # CASE 1: Detail update only (no photos)
    # ------------------------------
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

        if name:
            cache = load_cache()
            cache.setdefault("students", {})
            if sid in cache["students"]:
                cache["students"][sid]["name"] = student.name
                save_cache(cache)

        return {"ok": True, "message": "Student updated successfully"}

    # CASE: New student no photos
    if not student and not has_files:
        db.add(
            Student(
                id=sid,
                name=name or "",
                school_name=effective_school,
                class_name=class_name or "",
                section=section or "",
                roll=roll or "",
            )
        )
        db.commit()
        return {"ok": True, "message": "Student enrolled. Please add photos for face recognition."}

    # ------------------------------
    # CASE 2: Photos provided
    # ------------------------------

    # If replace -> GCS se purani images delete karo
    if has_files and replace_flag:
        delete_student_from_gcs(effective_school, class_name, section, sid)

    # GCS mein kitni images hain count karo next index ke liye
    next_idx = 1
    if has_files and not replace_flag:
        existing_count = count_gcs_images(effective_school, class_name, section, sid)
        next_idx = existing_count + 1

    # Images GCS mein save karo
    saved_files = []
    if len(files) > 0:
        for f in files:
            if not f.filename or not f.filename.strip():
                continue

            ext = os.path.splitext(f.filename)[1].lower()
            if ext not in ALLOWED_EXTENSIONS:
                continue

            image_bytes = await f.read()
            filename = f"img_{next_idx:03d}{ext}"

            # GCS mein save karo
            gcs_path = save_image_to_gcs(
                effective_school, class_name, section, sid, image_bytes, filename
            )
            if gcs_path:
                saved_files.append(filename)
            next_idx += 1

    # GCS se images download karo encoding ke liye
    image_paths = list_student_images_new(effective_school, class_name, section, sid)
    encodings = encode_images_from_paths(image_paths)

    if len(encodings) < MIN_ENROLL_PHOTOS:
        return {
            "ok": False,
            "message": f"Not enough valid photos. Need at least {MIN_ENROLL_PHOTOS}. Got {len(encodings)}.",
        }

    # Prevent accidental wipe
    if student:
        if not name:
            name = student.name or ""
        if not class_name:
            class_name = student.class_name or ""
        if not section:
            section = student.section or ""
        if not roll:
            roll = student.roll or ""

    # Cache mein save karo
    cache = load_cache()
    cache.setdefault("students", {})
    cache["students"][sid] = {"name": name, "encodings": encodings}
    save_cache(cache)

    # DB mein save/update karo
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

    msg = "Student photos updated successfully." if student else "Enrollment successful."
    return {"ok": True, "message": msg}


# ==============================
# Delete Student
# ==============================
@router.delete("/student/delete/{student_id}")
def delete_student(
    student_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ensure_dirs()
    sid = str(student_id).strip()

    if not sid:
        return {"ok": False, "message": "Student ID is required."}

    student_info = db.query(Student).filter(Student.id == sid).first()

    db.query(Attendance).filter(Attendance.student_id == sid).delete()
    db.query(Student).filter(Student.id == sid).delete()
    db.commit()

    # Cache se delete karo
    cache = load_cache()
    students = cache.get("students", {})
    if sid in students:
        students.pop(sid, None)
        cache["students"] = students
        save_cache(cache)

    # GCS se images delete karo
    if student_info:
        delete_student_from_gcs(
            student_info.school_name or "MainSchool",
            student_info.class_name,
            student_info.section,
            sid
        )

    return {"ok": True, "message": f"Student {sid} deleted successfully."}


# ==============================
# Students List
# ==============================
@router.get("/students")
def list_students(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    students = db.query(Student).all()
    result = []
    for s in students:
        result.append({
            "id": s.id,
            "name": s.name,
            "class_name": s.class_name,
            "section": s.section,
            "roll": s.roll,
            "school_name": s.school_name
        })
    return {"ok": True, "students": result}


# ==============================
# Attendance Mark
# ==============================
@router.post("/attendance/mark")
async def mark_attendance(
    file: UploadFile = File(...),
    mode: str = Form("in"),
    db: Session = Depends(get_db),
    
):
    ensure_dirs()

    cache = load_cache()
    students = cache.get("students", {})

    if not students:
        return {"ok": False, "message": "No students enrolled yet."}

    contents = await file.read()
    try:
        image = Image.open(io.BytesIO(contents)).convert("RGB")
        img = np.array(image, dtype=np.uint8)
    except Exception:
        return {"ok": False, "message": "Invalid image file."}

    best_sid, _, best_distance = identify_from_image_array(img, students)

    if best_sid is None or best_distance > MATCH_THRESHOLD:
        return {"ok": False, "message": "No match found"}

    sid = str(best_sid).strip()

    student = db.query(Student).filter(Student.id == sid).first()
    if not student:
        return {"ok": False, "message": "This person is not in classroom"}

    now = datetime.now()
    today = now.date()

    record = (
        db.query(Attendance)
        .filter(Attendance.student_id == sid)
        .filter(Attendance.date == today)
        .order_by(Attendance.id.desc())
        .first()
    )

    mode = (mode or "in").strip().lower()
    if mode not in ("in", "out"):
        return {"ok": False, "message": "Invalid mode. Use 'in' or 'out'."}

    if mode == "in":
        if record and record.in_time is not None:
            return {
                "ok": True,
                "message": "IN already marked",
                "student_id": sid,
                "name": student.name,
                "in_time": record.in_time.strftime("%Y-%m-%d %H:%M:%S"),
            }

        new_record = Attendance(
            student_id=sid,
            date=today,
            status="P",
            biometric_method="face",
            in_time=now,
        )
        db.add(new_record)
        db.commit()
        db.refresh(new_record)

        return {
            "ok": True,
            "message": "In time marked",
            "student_id": sid,
            "name": student.name,
            "in_time": new_record.in_time.strftime("%Y-%m-%d %H:%M:%S"),
        }

    if not record or record.in_time is None:
        return {"ok": False, "message": "IN not marked yet. Please mark IN first."}

    if record.out_time is not None:
        return {
            "ok": True,
            "message": "Out already marked",
            "student_id": sid,
            "name": student.name,
            "out_time": record.out_time.strftime("%Y-%m-%d %H:%M:%S"),
        }

    record.out_time = now
    record.updated_at = now
    db.commit()

    return {
        "ok": True,
        "message": "Out time marked",
        "student_id": sid,
        "name": student.name,
        "out_time": record.out_time.strftime("%Y-%m-%d %H:%M:%S"),
    }


# ==============================
# Export Excel (Today)
# ==============================
@router.get("/attendance/export/today")
def export_today_attendance_excel_route(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return export_today_attendance_excel(db)


# ==============================
# Export Excel (Custom Range)
# ==============================
@router.get("/attendance/export/excel")
def export_attendance_excel_route(
    start_date: str = None,
    end_date: str = None,
    school_name: str = None,
    class_name: str = None,
    section: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    start_dt = None
    end_dt = None

    if start_date:
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d").date()
        except ValueError:
            pass

    if end_date:
        try:
            end_dt = datetime.strptime(end_date, "%Y-%m-%d").date()
        except ValueError:
            pass

    return export_attendance_excel(
        db,
        start_date=start_dt,
        end_date=end_dt,
        school_name=school_name,
        class_name=class_name,
        section=section
    )


# ==============================
# Export Summary Excel
# ==============================
@router.get("/attendance/export/summary")
def export_summary_excel_route(
    start_date: str = None,
    end_date: str = None,
    school_name: str = None,
    class_name: str = None,
    section: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    start_dt = None
    end_dt = None

    if start_date:
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d").date()
        except ValueError:
            pass

    if end_date:
        try:
            end_dt = datetime.strptime(end_date, "%Y-%m-%d").date()
        except ValueError:
            pass

    return generate_summary_excel(
        db,
        start_date=start_dt,
        end_date=end_dt,
        school_name=school_name,
        class_name=class_name,
        section=section
    )
