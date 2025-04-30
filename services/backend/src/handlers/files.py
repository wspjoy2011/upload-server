"""Image file listing utility.

This module provides functionality to scan the image upload directory
and return metadata for each valid image file.

Side effects:
    - Reads the file system to access metadata (size, creation time) of files.
    - Raises exceptions if the directory is missing or inaccessible.
"""

import os
from datetime import datetime, UTC

from settings.config import config


def list_uploaded_images() -> list[dict[str, str | int]]:
    """Scans the upload directory and returns metadata for valid image files.

    Returns:
        list[dict[str, str | int]]: A list of dictionaries, each containing:
            - 'filename' (str): The name of the image file.
            - 'created_at' (str): ISO-formatted creation timestamp (UTC).
            - 'size' (int): Size of the file in bytes.

    Raises:
        FileNotFoundError: If the upload directory does not exist.
        PermissionError: If the upload directory cannot be accessed.

    Side effects:
        - Reads the file system (os.listdir, os.path.getctime, os.path.getsize).
    """
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
