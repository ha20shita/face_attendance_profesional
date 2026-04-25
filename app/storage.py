"""
Storage layer - Google Cloud Storage version
"""
import os
import pickle
from app.config import UPLOADS_DIR, DATA_DIR

BUCKET_NAME = os.getenv("GCS_BUCKET", "face-attendance-bucket-492205")

def get_bucket():
    from google.cloud import storage
    client = storage.Client()
    return client.bucket(BUCKET_NAME)

def ensure_dirs():
    os.makedirs(UPLOADS_DIR, exist_ok=True)
    os.makedirs(DATA_DIR, exist_ok=True)

def load_cache() -> dict:
    try:
        bucket = get_bucket()
        blob = bucket.blob("data/encodings.pkl")
        if not blob.exists():
            return {"students": {}}
        data = blob.download_as_bytes()
        return pickle.loads(data)
    except Exception as e:
        print(f"Cache load error: {e}")
        return {"students": {}}

def save_cache(cache: dict):
    try:
        bucket = get_bucket()
        blob = bucket.blob("data/encodings.pkl")
        data = pickle.dumps(cache)
        blob.upload_from_string(data, content_type="application/octet-stream")
        print("Cache saved to GCS")
    except Exception as e:
        print(f"Cache save error: {e}")
