"""
Encoder Layer – Face Recognition Core (Production Ready)

Responsibilities:
✔ Read images from disk
✔ Auto convert ANY format → RGB (via OpenCV best for dlib)
✔ Force uint8 + contiguous memory (dlib safe)
✔ Detect exactly ONE face
✔ Generate encodings
✔ Skip invalid/corrupt images safely

This module contains ONLY face logic.
NO API / NO DB / NO storage code.
"""

import os
from typing import List, Optional

import numpy as np
import cv2
import face_recognition

from app.config import UPLOADS_DIR, ALLOWED_EXTENSIONS


# ==========================
# Tuning
# ==========================
# Big images slow down face detection on Windows laptops.
# This keeps quality decent and improves speed.
MAX_WIDTH = 800  # set None to disable


def _resize_if_needed(img_rgb: np.ndarray) -> np.ndarray:
    if MAX_WIDTH is None:
        return img_rgb
    h, w = img_rgb.shape[:2]
    if w <= MAX_WIDTH:
        return img_rgb
    scale = MAX_WIDTH / float(w)
    new_w = int(w * scale)
    new_h = int(h * scale)
    return cv2.resize(img_rgb, (new_w, new_h), interpolation=cv2.INTER_AREA)


# =========================================================
# Safe Image Loader (dlib-safe)
# =========================================================
def load_image_safe(path: str) -> np.ndarray:
    """
    Safely load image and guarantee:
    - RGB
    - uint8
    - contiguous memory
    """
    img_bgr = cv2.imread(path, cv2.IMREAD_COLOR)

    if img_bgr is None:
        raise ValueError(f"Could not read image file: {path}")

    img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)

    # Resize for speed (optional)
    img_rgb = _resize_if_needed(img_rgb)

    # enforce expected dtype + contiguous memory for dlib
    img_rgb = img_rgb.astype(np.uint8, copy=False)
    img_rgb = np.ascontiguousarray(img_rgb)

    return img_rgb


# =========================================================
# File Listing
# =========================================================
def list_student_images(student_id: str) -> List[str]:
    """
    Returns sorted image paths for a student.

    Path:
        uploads/students/{student_id}/
    """
    folder = os.path.join(UPLOADS_DIR, str(student_id))
    if not os.path.isdir(folder):
        return []

    files = [
        os.path.join(folder, f)
        for f in os.listdir(folder)
        if f.lower().endswith(ALLOWED_EXTENSIONS)
    ]
    files.sort()
    return files


# =========================================================
# Single Image Encoding
# =========================================================
def encode_single_image(image_rgb: np.ndarray) -> Optional[np.ndarray]:
    """
    Build encoding ONLY if exactly ONE face is found.

    Returns:
        encoding OR None
    """
    face_locations = face_recognition.face_locations(
        image_rgb,
        model="hog",
        number_of_times_to_upsample=1,
    )

    # exactly ONE face required
    if len(face_locations) != 1:
        return None

    encodings = face_recognition.face_encodings(image_rgb, face_locations)
    if not encodings:
        return None

    return encodings[0]


# =========================================================
# Batch Encoding
# =========================================================
def encode_images_from_paths(paths: List[str]) -> List[np.ndarray]:
    """
    Generate encodings from multiple images.

    Automatically:
    ✔ skips bad files
    ✔ skips 0-face images
    ✔ skips multi-face images

    Returns:
        list of valid encodings
    """
    final_encodings: List[np.ndarray] = []

    for path in paths:
        try:
            image = load_image_safe(path)
            enc = encode_single_image(image)
            if enc is not None:
                final_encodings.append(enc)
        except Exception:
            continue

    return final_encodings