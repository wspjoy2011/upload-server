"""Upload handler for processing and saving uploaded image files.

This module validates uploaded files for size, format, and image integrity,
and saves them to the configured directory with a unique filename.

Side effects:
    - Reads and writes files to disk.
    - Creates image directory if it does not exist.
    - Raises custom API exceptions on validation failure.
"""

import os
import uuid
import shutil
from typing import cast

from PIL import Image, UnidentifiedImageError

from settings.config import config
from exceptions.api_errors import NotSupportedFormatError, MaxSizeExceedError
from interfaces.protocols import SupportsWrite


def handle_uploaded_file(file) -> dict[str, str]:
    """Validates and saves a single uploaded image file to disk.

    Args:
        file: A multipart-compatible file-like object containing:
            - file_name (bytes | None): The name of the uploaded file.
            - file_object (IO[bytes]): The binary file stream.

    Returns:
        dict[str, str]: A dictionary containing:
            - 'filename': The unique stored filename.
            - 'url': The relative URL to access the image.

    Raises:
        NotSupportedFormatError: If the file extension or content is invalid.
        MaxSizeExceedError: If the file exceeds the configured size limit.

    Side effects:
        - Verifies image content using Pillow.
        - Writes the uploaded file to disk under `config.IMAGES_DIR`.
        - Creates the image directory if it does not exist.
    """
    filename = file.file_name.decode("utf-8") if file.file_name else "uploaded_file"
    ext = os.path.splitext(filename)[1].lower()

    if ext not in config.SUPPORTED_FORMATS:
        raise NotSupportedFormatError(config.SUPPORTED_FORMATS)

    file.file_object.seek(0, os.SEEK_END)
    size = file.file_object.tell()
    file.file_object.seek(0)

    if size > config.MAX_FILE_SIZE:
        raise MaxSizeExceedError(config.MAX_FILE_SIZE)

    try:
        image = Image.open(file.file_object)
        image.verify()
        file.file_object.seek(0)
    except (UnidentifiedImageError, OSError):
        raise NotSupportedFormatError(config.SUPPORTED_FORMATS)

    original_name = os.path.splitext(filename)[0].lower()
    unique_name = f"{original_name}_{uuid.uuid4()}{ext}"
    os.makedirs(config.IMAGES_DIR, exist_ok=True)
    file_path = os.path.join(config.IMAGES_DIR, unique_name)

    with open(file_path, "wb") as f:
        file.file_object.seek(0)
        shutil.copyfileobj(file.file_object, cast(SupportsWrite, f))

    return {
        "filename": unique_name,
        "url": f"/images/{unique_name}"
    }
