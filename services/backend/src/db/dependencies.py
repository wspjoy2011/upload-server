"""Repository dependency injection module.

This module provides singleton instances of repositories using the dependency injection pattern.
It ensures that only a single instance of each repository is created and reused across the application.
"""

from typing import Optional

from db.session import get_connection_pool
from db.repositories import PostgresImageRepository
from interfaces.repositories import ImageRepository


_image_repository: Optional[ImageRepository] = None


def get_image_repository() -> ImageRepository:
    """Get or create a singleton instance of the image repository.

    Uses the database connection pool to create a PostgresImageRepository
    instance if one doesn't already exist, ensuring resource efficiency.

    Returns:
        ImageRepository: A singleton instance of the image repository.

    Side effects:
        - On first call, creates a repository instance using the connection pool.
    """
    global _image_repository
    if _image_repository is None:
        pool = get_connection_pool()
        _image_repository = PostgresImageRepository(pool)
    return _image_repository
