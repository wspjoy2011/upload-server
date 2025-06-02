"""Database repository implementations.

This module provides concrete implementations of repository interfaces
for database operations on specific entity types.

Each repository handles data access operations for a specific entity type,
encapsulating SQL queries and database interaction details.
"""

from typing import List, Optional

from psycopg_pool import ConnectionPool
from psycopg.errors import Error as PsycopgError

from interfaces.repositories import (
    ImageRepository,
    ImageDTO,
    ImageDetailsDTO
)
from exceptions.repository_errors import (
    EntityCreationError,
    EntityDeletionError,
    QueryExecutionError,
)


class PostgresImageRepository(ImageRepository):
    """PostgreSQL implementation of the ImageRepository interface.

    Handles database operations for image entities using a connection pool.

    Attributes:
        _pool (ConnectionPool): Database connection pool.
    """

    def __init__(self, pool: ConnectionPool):
        """Initialize repository with a connection pool.

        Args:
            pool (ConnectionPool): Database connection pool to use for queries.
        """
        self._pool = pool

    def create(self, image: ImageDTO) -> ImageDetailsDTO:
        """Create a new image record in the database.

        Args:
            image (ImageDTO): Image data to create.

        Returns:
            ImageDetailsDTO: Created image data with ID and timestamp.

        Raises:
            EntityCreationError: If creation fails due to database errors.
        """
        query = """
            INSERT INTO images (filename, original_name, size, file_type)
            VALUES (%s, %s, %s, %s)
            RETURNING id, upload_time
        """
        try:
            with self._pool.connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        query,
                        (image.filename, image.original_name, image.size, image.file_type),
                    )
                    db_id, upload_time = cur.fetchone()
                    conn.commit()

                    return ImageDetailsDTO(
                        id=db_id,
                        filename=image.filename,
                        original_name=image.original_name,
                        size=image.size,
                        file_type=image.file_type,
                        upload_time=upload_time.isoformat() if upload_time else None,
                    )
        except PsycopgError as e:
            raise EntityCreationError("Image", str(e))
        except Exception as e:
            raise EntityCreationError("Image", str(e))

    def get_by_id(self, image_id: int) -> Optional[ImageDetailsDTO]:
        """Retrieve an image by its ID.

        Args:
            image_id (int): Unique identifier of the image.

        Returns:
            Optional[ImageDetailsDTO]: Found image data or None if not found.

        Raises:
            QueryExecutionError: If query execution fails.
        """
        query = """
            SELECT id, filename, original_name, size, upload_time, file_type::text
            FROM images
            WHERE id = %s
        """
        try:
            with self._pool.connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(query, (image_id,))
                    result = cur.fetchone()

                    if not result:
                        return None

                    db_id, filename, original_name, size, upload_time, file_type = result
                    return ImageDetailsDTO(
                        id=db_id,
                        filename=filename,
                        original_name=original_name,
                        size=size,
                        upload_time=upload_time.isoformat() if upload_time else None,
                        file_type=file_type,
                    )
        except PsycopgError as e:
            raise QueryExecutionError("get_by_id", str(e))

    def get_by_filename(self, filename: str) -> Optional[ImageDetailsDTO]:
        """Retrieve an image by its filename.

        Args:
            filename (str): Filename to search for.

        Returns:
            Optional[ImageDetailsDTO]: Found image data or None if not found.

        Raises:
            QueryExecutionError: If query execution fails.
        """
        query = """
            SELECT id, filename, original_name, size, upload_time, file_type::text
            FROM images
            WHERE filename = %s
        """
        try:
            with self._pool.connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(query, (filename,))
                    result = cur.fetchone()

                    if not result:
                        return None

                    db_id, filename, original_name, size, upload_time, file_type = result
                    return ImageDetailsDTO(
                        id=db_id,
                        filename=filename,
                        original_name=original_name,
                        size=size,
                        upload_time=upload_time.isoformat() if upload_time else None,
                        file_type=file_type,
                    )
        except PsycopgError as e:
            raise QueryExecutionError("get_by_filename", str(e))

    def delete(self, image_id: int) -> bool:
        """Delete an image from the database by ID.

        Args:
            image_id (int): Unique identifier of the image to delete.

        Returns:
            bool: True if deleted, False if not found.

        Raises:
            EntityDeletionError: If deletion fails due to database errors.
        """
        query = "DELETE FROM images WHERE id = %s RETURNING id"
        try:
            with self._pool.connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(query, (image_id,))
                    result = cur.fetchone()
                    conn.commit()
                    return result is not None
        except PsycopgError as e:
            raise EntityDeletionError("Image", image_id, str(e))

    def delete_by_filename(self, filename: str) -> bool:
        """Delete an image from the database by filename.

        Args:
            filename (str): Filename of the image to delete.

        Returns:
            bool: True if deleted, False if not found.

        Raises:
            EntityDeletionError: If deletion fails due to database errors.
        """
        query = "DELETE FROM images WHERE filename = %s RETURNING id"
        try:
            with self._pool.connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(query, (filename,))
                    result = cur.fetchone()
                    conn.commit()
                    return result is not None
        except PsycopgError as e:
            raise EntityDeletionError("Image", filename, str(e))

    def list_all(self, limit: int = 10, offset: int = 0, order: str = "desc") -> List[ImageDetailsDTO]:
        """List images with pagination and sorting.

        Args:
            limit (int, optional): Maximum number of images to return. Defaults to 10.
            offset (int, optional): Number of images to skip. Defaults to 0.
            order (str, optional): Sort order for upload_time ("desc" or "asc"). Defaults to "desc".

        Returns:
            List[ImageDetailsDTO]: List of image data.

        Raises:
            QueryExecutionError: If query execution fails.
            ValueError: If order parameter is not "desc" or "asc".
        """
        if order.lower() not in ("desc", "asc"):
            raise ValueError("Order parameter must be 'desc' or 'asc'")

        query = f"""
            SELECT id, filename, original_name, size, upload_time, file_type::text
            FROM images
            ORDER BY upload_time {order.upper()}
            LIMIT %s OFFSET %s
        """

        try:
            with self._pool.connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(query, (limit, offset))
                    results = cur.fetchall()

                    return [
                        ImageDetailsDTO(
                            id=int(row[0]),
                            filename=row[1],
                            original_name=row[2],
                            size=row[3],
                            upload_time=row[4].isoformat() if row[4] else None,
                            file_type=row[5],
                        )
                        for row in results
                    ]
        except PsycopgError as e:
            raise QueryExecutionError("list_all", str(e))

    def count(self) -> int:
        """Count the total number of images.

        Returns:
            int: Total count of images.

        Raises:
            QueryExecutionError: If query execution fails.
        """
        query = "SELECT COUNT(*) FROM images"
        try:
            with self._pool.connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(query)
                    result = cur.fetchone()
                    return result[0]
        except PsycopgError as e:
            raise QueryExecutionError("count", str(e))
