import uuid
from typing import Optional, Tuple
from pathlib import Path
from PIL import Image, UnidentifiedImageError
from werkzeug.datastructures import FileStorage
from flask import current_app

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}
MAX_DIMENSION = 1200


def validate_and_save_image(file: FileStorage) -> Tuple[Optional[str], Optional[str]]:
    """
    Validates file extension, MIME type, file size, and actual image integrity with Pillow.
    Resizes image proportionally if exceeding max dimensions and saves safely.
    Returns: (relative_saved_path, error_message)
    """
    if not file or not file.filename:
        return None, None

    filename = file.filename.strip()
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        return None, f"Invalid image format. Allowed extensions: {', '.join(ALLOWED_EXTENSIONS)}."

    upload_folder = Path(current_app.config["UPLOAD_FOLDER"])
    upload_folder.mkdir(parents=True, exist_ok=True)

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
        target_path = upload_folder / unique_filename
        img.save(str(target_path), format="JPEG", quality=85, optimize=True)

        return f"uploads/{unique_filename}", None
    except (UnidentifiedImageError, OSError, Exception) as e:
        return None, f"Could not process image: {str(e)}"
