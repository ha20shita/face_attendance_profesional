"""
Storage helper - Google Cloud Storage version
School/Class/Section structure
"""
import os
import io
from app.config import UPLOADS_DIR, ALLOWED_EXTENSIONS

BUCKET_NAME = os.getenv("GCS_BUCKET", "face-attendance-bucket-492205")


def get_bucket():
    from google.cloud import storage
    client = storage.Client()
    return client.bucket(BUCKET_NAME)


def sanitize_folder_name(name: str) -> str:
    invalid_chars = ['<', '>', ':', '"', '|', '?', '*', '/', '\\']
    for char in invalid_chars:
        name = name.replace(char, '_')
    name = name.strip(' .')
    if not name:
        name = "Unknown"
    return name


def get_student_gcs_prefix(school_name: str, class_name: str, section: str, student_id: str) -> str:
    school_clean = sanitize_folder_name(school_name or "Unknown_School")
    class_clean = sanitize_folder_name(class_name or "Unknown_Class")
    section_clean = sanitize_folder_name(section or "Unknown_Section")
    return f"uploads/students/{school_clean}/{class_clean}/{section_clean}/{student_id}"


def get_student_folder_path(school_name: str, class_name: str, section: str, student_id: str) -> str:
    school_clean = sanitize_folder_name(school_name or "Unknown_School")
    class_clean = sanitize_folder_name(class_name or "Unknown_Class")
    section_clean = sanitize_folder_name(section or "Unknown_Section")
    return os.path.join(UPLOADS_DIR, school_clean, class_clean, section_clean, str(student_id))


def ensure_student_folder(school_name: str, class_name: str, section: str, student_id: str) -> str:
    """Local folder banana (temporary - encoding ke liye)"""
    folder_path = get_student_folder_path(school_name, class_name, section, student_id)
    os.makedirs(folder_path, exist_ok=True)
    return folder_path


def save_image_to_gcs(school_name: str, class_name: str, section: str, student_id: str, image_bytes: bytes, filename: str) -> str:
    """Image GCS mein save karo"""
    try:
        bucket = get_bucket()
        prefix = get_student_gcs_prefix(school_name, class_name, section, student_id)
        blob = bucket.blob(f"{prefix}/{filename}")
        blob.upload_from_string(image_bytes, content_type="image/jpeg")
        return f"{prefix}/{filename}"
    except Exception as e:
        print(f"Image GCS save error: {e}")
        return ""


def download_images_from_gcs(school_name: str, class_name: str, section: str, student_id: str) -> list:
    """GCS se images download karo local temp folder mein encoding ke liye"""
    try:
        bucket = get_bucket()
        prefix = get_student_gcs_prefix(school_name, class_name, section, student_id)
        blobs = list(bucket.list_blobs(prefix=prefix))

        local_folder = ensure_student_folder(school_name, class_name, section, student_id)
        local_paths = []

        for blob in blobs:
            filename = blob.name.split("/")[-1]
            if not filename.lower().endswith(ALLOWED_EXTENSIONS):
                continue
            local_path = os.path.join(local_folder, filename)
            blob.download_to_filename(local_path)
            local_paths.append(local_path)

        local_paths.sort()
        return local_paths

    except Exception as e:
        print(f"GCS download error: {e}")
        return []


def delete_student_from_gcs(school_name: str, class_name: str, section: str, student_id: str):
    """GCS se student ki sari images delete karo"""
    try:
        bucket = get_bucket()
        prefix = get_student_gcs_prefix(school_name, class_name, section, student_id)
        blobs = list(bucket.list_blobs(prefix=prefix))
        for blob in blobs:
            blob.delete()
        print(f"Deleted {len(blobs)} files from GCS for student {student_id}")
    except Exception as e:
        print(f"GCS delete error: {e}")


def list_student_images_new(school_name: str, class_name: str, section: str, student_id: str) -> list:
    """GCS se images download karke local paths return karo"""
    return download_images_from_gcs(school_name, class_name, section, student_id)


def count_gcs_images(school_name: str, class_name: str, section: str, student_id: str) -> int:
    """GCS mein kitni images hain count karo"""
    try:
        bucket = get_bucket()
        prefix = get_student_gcs_prefix(school_name, class_name, section, student_id)
        blobs = list(bucket.list_blobs(prefix=prefix))
        return len([b for b in blobs if b.name.lower().endswith(ALLOWED_EXTENSIONS)])
    except Exception as e:
        print(f"GCS count error: {e}")
        return 0
