"""Repository interfaces for data access objects.

This module defines abstract base classes that specify interfaces for repository objects,
which handle data access operations for specific entity types.
"""

from abc import ABC, abstractmethod
from typing import List, Optional

from db.dto import ImageDTO, ImageDetailsDTO


class ImageRepository(ABC):
    """Repository interface for image-related data operations.

    Defines the contract for image repository implementations.
    """

    @abstractmethod
    def create(self, image: ImageDTO) -> ImageDetailsDTO:
        """Create a new image record in the data store.

        Args:
            image (ImageDTO): Image data to create.

        Returns:
            ImageDetailsDTO: Created image data with ID and timestamp.

        Raises:
            EntityCreationError: If the entity creation fails.
        """
        pass

    @abstractmethod
    def get_by_id(self, image_id: int) -> Optional[ImageDetailsDTO]:
        """Retrieve an image by its ID.

        Args:
            image_id (int): The unique identifier of the image.

        Returns:
            Optional[ImageDetailsDTO]: The found image data, or None if not found.
        """
        pass

    @abstractmethod
    def get_by_filename(self, filename: str) -> Optional[ImageDetailsDTO]:
        """Retrieve an image by its filename.

        Args:
            filename (str): The filename to search for.

        Returns:
            Optional[ImageDetailsDTO]: The found image data, or None if not found.
        """
        pass

    @abstractmethod
    def delete(self, image_id: int) -> bool:
        """Delete an image from the data store by ID.

        Args:
            image_id (int): The unique identifier of the image to delete.

        Returns:
            bool: True if the image was deleted, False if it didn't exist.

        Raises:
            EntityDeletionError: If the entity deletion fails.
        """
        pass

    @abstractmethod
    def delete_by_filename(self, filename: str) -> bool:
        """Delete an image from the data store by filename.

        Args:
            filename (str): The filename of the image to delete.

        Returns:
            bool: True if the image was deleted, False if it didn't exist.

        Raises:
            EntityDeletionError: If the entity deletion fails.
        """
        pass

    @abstractmethod
    def list_all(self, limit: int = 10, offset: int = 0) -> List[ImageDetailsDTO]:
        """List images with pagination.

        Args:
            limit (int): Maximum number of images to return.
            offset (int): Number of images to skip.

        Returns:
            List[ImageDetailsDTO]: A list of image data.

        Raises:
            QueryExecutionError: If the listing operation fails.
        """
        pass

    @abstractmethod
    def count(self) -> int:
        """Count the total number of images.

        Returns:
            int: The total count of images in the store.

        Raises:
            QueryExecutionError: If the counting operation fails.
        """
        pass
