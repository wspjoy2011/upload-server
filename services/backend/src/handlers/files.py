import os
from datetime import datetime, UTC

from settings.config import config


def list_uploaded_images() -> list[dict[str, str | int]]:
    """Returns a list of image metadata (name, size, created_at) from the upload directory."""
    files = []

    try:
        filenames = os.listdir(config.IMAGES_DIR)
    except FileNotFoundError:
        raise FileNotFoundError("Images directory not found.")
    except PermissionError:
        raise PermissionError("Permission denied to access images directory.")

    for filename in filenames:
        filepath = os.path.join(config.IMAGES_DIR, filename)
        ext = os.path.splitext(filename)[1].lower()

        if ext in config.SUPPORTED_FORMATS and os.path.isfile(filepath):
            created_at = datetime.fromtimestamp(os.path.getctime(filepath), tz=UTC).isoformat()
            size = os.path.getsize(filepath)
            files.append({
                "filename": filename,
                "created_at": created_at,
                "size": size
            })

    return files
