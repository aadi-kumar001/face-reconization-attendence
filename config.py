"""
Central configuration for the Face Recognition Attendance System.
All tunables live here so nothing is hard-coded deep inside the app.
"""
import os
from datetime import timedelta


class Config:
    # --- Core ---
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    SECRET_KEY = os.environ.get("FRAS_SECRET_KEY", "dev-key-change-me")
    DEBUG = os.environ.get("FRAS_DEBUG", "false").lower() == "true"

    # --- Database ---
    DB_PATH = os.path.join(BASE_DIR, "instance", "attendance.db")
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{DB_PATH}"

    # --- Face recognition engine ---
    # "insightface" (ArcFace embeddings, most accurate) or "face_recognition"
    # (dlib ResNet embeddings, easier to install) — engine.py auto-falls back.
    FACE_ENGINE_BACKEND = os.environ.get("FRAS_BACKEND", "auto")
    FACE_MATCH_THRESHOLD = float(os.environ.get("FRAS_MATCH_THRESHOLD", 0.42))
    EMBEDDING_DIM = 512  # ArcFace default; face_recognition uses 128 (handled in engine)
    FAISS_INDEX_TYPE = "IVF_FLAT"  # scales to 10k+ enrolled faces with sub-ms lookups
    MIN_FACE_SIZE = 60  # px, ignore faces smaller than this (reduces false positives)

    # --- Liveness / anti-spoofing ---
    LIVENESS_ENABLED = True
    EAR_BLINK_THRESHOLD = 0.21          # eye-aspect-ratio below this = eye closed
    EAR_CONSEC_FRAMES = 2               # frames closed to count a blink
    BLINK_TIMEOUT_SECONDS = 8           # must blink within this window to pass
    TEXTURE_LAPLACIAN_MIN_VAR = 60.0    # below this variance => likely a printed photo
    MOIRE_FFT_ENERGY_THRESHOLD = 0.15   # high-frequency energy typical of screen replay

    # --- Attendance rules ---
    DEDUPE_WINDOW_MINUTES = 5           # ignore repeat marks for same person within window
    LATE_AFTER = "09:15"                # HH:MM, used to flag "late" status
    WORKDAY_START = "09:00"
    WORKDAY_END = "18:00"

    # --- Camera / streaming ---
    CAMERA_SOURCE = int(os.environ.get("FRAS_CAMERA", 0))
    FRAME_WIDTH = 640
    FRAME_HEIGHT = 480
    PROCESS_EVERY_N_FRAMES = 2          # skip frames for real-time performance
    JPEG_QUALITY = 80

    # --- Auth ---
    JWT_SECRET = os.environ.get("FRAS_JWT_SECRET", SECRET_KEY)
    JWT_EXPIRY = timedelta(hours=8)
    ADMIN_USERNAME = os.environ.get("FRAS_ADMIN_USER", "admin")
    ADMIN_PASSWORD_HASH = os.environ.get("FRAS_ADMIN_HASH")  # set via scripts/create_admin.py

    # --- Notifications ---
    NOTIFY_ON_MARK = os.environ.get("FRAS_NOTIFY", "false").lower() == "true"
    SMTP_HOST = os.environ.get("FRAS_SMTP_HOST")
    SMTP_PORT = int(os.environ.get("FRAS_SMTP_PORT", 587))
    SMTP_USER = os.environ.get("FRAS_SMTP_USER")
    SMTP_PASSWORD = os.environ.get("FRAS_SMTP_PASSWORD")
    TELEGRAM_BOT_TOKEN = os.environ.get("FRAS_TG_TOKEN")
    TELEGRAM_CHAT_ID = os.environ.get("FRAS_TG_CHAT")

    # --- Storage ---
    ENROLL_IMAGES_DIR = os.path.join(BASE_DIR, "instance", "enrolled_faces")
    EXPORTS_DIR = os.path.join(BASE_DIR, "instance", "exports")
    LOG_DIR = os.path.join(BASE_DIR, "instance", "logs")

    @classmethod
    def ensure_dirs(cls):
        for d in (
            os.path.dirname(cls.DB_PATH),
            cls.ENROLL_IMAGES_DIR,
            cls.EXPORTS_DIR,
            cls.LOG_DIR,
        ):
            os.makedirs(d, exist_ok=True)
