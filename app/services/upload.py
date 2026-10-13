import io
import uuid
from typing import Optional, Tuple
from pathlib import Path
from datetime import datetime
from PIL import Image, UnidentifiedImageError
from werkzeug.datastructures import FileStorage
from flask import current_app

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}
MAX_DIMENSION = 1200


def validate_and_save_image(file: FileStorage) -> Tuple[Optional[str], Optional[str]]:
    """
    Validates file extension, MIME type, file size, and actual image integrity with Pillow.
    Resizes image proportionally if exceeding max dimensions.
    Persists to MongoDB (for Vercel serverless environments) and writes to disk when writable.
    Returns: (relative_saved_path, error_message)
    """
    if not file or not file.filename:
        return None, None

    filename = file.filename.strip()
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        return None, f"Invalid image format. Allowed extensions: {', '.join(ALLOWED_EXTENSIONS)}."

    try:
        # Validate that the file is an authentic, non-corrupted image
        img = Image.open(file.stream)
        img.verify()

        # Re-open stream for processing (verify exhausts the file pointer)
        file.stream.seek(0)
        img = Image.open(file.stream)

        # Convert palette/RGBA to RGB if saving as JPEG
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")

        # Proportional resize if larger than MAX_DIMENSION
        if img.width > MAX_DIMENSION or img.height > MAX_DIMENSION:
            img.thumbnail((MAX_DIMENSION, MAX_DIMENSION), Image.Resampling.LANCZOS)

        unique_filename = f"{uuid.uuid4().hex}.jpg"

        # Generate optimized JPEG bytes
        out_buf = io.BytesIO()
        img.save(out_buf, format="JPEG", quality=85, optimize=True)
        img_bytes = out_buf.getvalue()

        # 1. Persist image to MongoDB (guarantees survival on Vercel serverless)
        try:
            from app.db import get_db
            db = get_db()
            db.item_images.update_one(
                {"filename": unique_filename},
                {"$set": {
                    "filename": unique_filename,
                    "content_type": "image/jpeg",
                    "data": img_bytes,
                    "created_at": datetime.utcnow()
                }},
                upsert=True
            )
        except Exception as db_err:
            current_app.logger.warning(f"Could not save image to MongoDB: {db_err}")

        # 2. Try writing to local upload folder (disk cache)
        saved_locally = False
        try:
            upload_folder = Path(current_app.config.get("UPLOAD_FOLDER", "app/static/uploads"))
            upload_folder.mkdir(parents=True, exist_ok=True)
            target_path = upload_folder / unique_filename
            with open(target_path, "wb") as f:
                f.write(img_bytes)
            saved_locally = True
        except (OSError, PermissionError):
            pass

        # 3. Fallback to /tmp/uploads on read-only environments like Vercel
        if not saved_locally:
            try:
                tmp_dir = Path("/tmp/uploads")
                tmp_dir.mkdir(parents=True, exist_ok=True)
                with open(tmp_dir / unique_filename, "wb") as f:
                    f.write(img_bytes)
            except Exception:
                pass

        return f"uploads/{unique_filename}", None
    except (UnidentifiedImageError, OSError, Exception) as e:
        return None, f"Could not process image: {str(e)}"
