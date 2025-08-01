"""Service dependency injection module.

This module provides singleton instances of services using the dependency injection pattern.
It ensures that only a single instance of each service is created and reused across
the application, improving resource usage and maintaining consistent behavior.
"""

from typing import Optional

from db.dependencies import get_image_repository
from handlers.dependencies import get_file_handler
from interfaces.services import ImageUploadServiceInterface
from services.upload_image import ImageUploadService
from settings.logging_config import get_logger

_image_upload_service: Optional[ImageUploadServiceInterface] = None


def get_image_upload_service() -> ImageUploadServiceInterface:
    """Get or create a singleton instance of the image upload service.

    Creates an ImageUploadService instance if one doesn't already exist,
    ensuring consistent handling of image operations throughout
    the application.

    Returns:
        ImageUploadServiceInterface: A singleton instance of the image upload service.

    Side effects:
        - On first call, creates a service instance with injected dependencies.
    """
    global _image_upload_service
    if _image_upload_service is None:
        file_handler = get_file_handler()
        image_repository = get_image_repository()
        logger = get_logger(__name__)

        _image_upload_service = ImageUploadService(
            file_handler=file_handler,
            image_repository=image_repository,
            logger=logger
        )
    return _image_upload_service
