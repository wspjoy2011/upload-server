"""Service layer interfaces.

This module defines the contracts for service layer components that orchestrate
business logic between handlers and repositories.
"""

from abc import ABC, abstractmethod
from typing import List, Optional

from db.dto import ImageDTO
from dto.file import UploadedFileDTO
from dto.pagination import PaginationDTO


class ImageUploadServiceInterface(ABC):
    """Abstract base class for image upload service operations.

    This service orchestrates image upload business logic including:
    - File validation and processing
    - Image metadata creation
    - Repository coordination
    - Business rule enforcement
    """

    @abstractmethod
    def upload_image(self, file) -> UploadedFileDTO:
        """Processes and saves an uploaded image file.

        Args:
            file: The uploaded file object from multipart form parser.

        Returns:
            UploadedFileDTO: Information about the successfully uploaded file.

        Raises:
            APIError: If upload fails due to validation or processing errors.
            RepositoryError: If database operation fails.
        """
        pass

    @abstractmethod
    def get_images_list(self, pagination: PaginationDTO, order: str = "desc") -> tuple[List[ImageDTO], int]:
        """Retrieves a paginated list of images with total count.

        Args:
            pagination (PaginationDTO): Pagination parameters.
            order (str): Sort order for upload_time ("desc" or "asc").

        Returns:
            tuple[List[ImageDTO], int]: List of images and total count.

        Raises:
            ServiceError: If retrieval fails.
        """
        pass

    @abstractmethod
    def get_image_details(self, filename: str) -> Optional[ImageDTO]:
        """Retrieves detailed information about a specific image.

        Args:
            filename (str): Name of the image file.

        Returns:
            Optional[ImageDTO]: Image details if found, None otherwise.

        Raises:
            ServiceError: If retrieval fails.
        """
        pass

    @abstractmethod
    def delete_image(self, filename: str) -> bool:
        """Deletes an image file and its metadata.

        Args:
            filename (str): Name of the image file to delete.

        Returns:
            bool: True if deletion was successful, False if image not found.

        Raises:
            ServiceError: If deletion fails.
        """
        pass
