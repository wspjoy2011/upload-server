"""Image service implementation.

This module provides the concrete implementation of image service operations,
orchestrating business logic between file handlers and repositories.
"""

from typing import List
from logging import Logger

from db.dto import ImageDTO, ImageDetailsDTO
from dto.file import UploadedFileDTO
from dto.pagination import PaginationDTO
from exceptions.api_errors import APIError
from exceptions.repository_errors import RepositoryError
from exceptions.service_errors import (
    UploadServiceError,
    ImageListServiceError,
    InvalidSortOrderError,
    ImageNotFoundError,
    ImageDeletionServiceError,
    ImageDetailsServiceError
)
from interfaces.services import ImageUploadServiceInterface
from interfaces.handlers import FileHandlerInterface
from interfaces.repositories import ImageRepository


class ImageUploadService(ImageUploadServiceInterface):
    """Concrete implementation of image upload service.

    Orchestrates image operations between file handlers and repositories,
    providing business logic for upload, retrieval, and deletion operations.
    """

    def __init__(
            self,
            file_handler: FileHandlerInterface,
            image_repository: ImageRepository,
            logger: Logger
    ):
        """Initialize the image service.

        Args:
            file_handler: Handler for file system operations.
            image_repository: Repository for image metadata operations.
            logger: Optional logger instance.
        """
        self._file_handler = file_handler
        self._image_repository = image_repository
        self._logger = logger

    def upload_image(self, file) -> UploadedFileDTO:
        """Processes and saves an uploaded image file.

        Args:
            file: The uploaded file object from multipart form parser.

        Returns:
            UploadedFileDTO: Information about the successfully uploaded file.

        Raises:
            UploadServiceError: If upload fails due to validation or processing errors.
        """
        try:
            uploaded_file_dto = self._file_handler.handle_upload(file)
            self._logger.info(f"File processed successfully: {uploaded_file_dto.filename}")
        except APIError as e:
            raise UploadServiceError(e.message, e.status_code)
        else:
            image_dto = ImageDTO(
                filename=uploaded_file_dto.filename,
                original_name=uploaded_file_dto.original_name,
                size=uploaded_file_dto.size,
                file_type=uploaded_file_dto.extension
            )

        try:
            self._image_repository.create(image_dto)
            self._logger.info(f"Image metadata saved for: {uploaded_file_dto.filename}")
        except RepositoryError as e:
            raise UploadServiceError(e.message, e.status_code)
        else:
            self._logger.info(f"Image upload completed successfully: {uploaded_file_dto.filename}")
            return uploaded_file_dto

    def get_images_list(self, pagination: PaginationDTO, order: str = "desc") -> tuple[List[ImageDetailsDTO], int]:
        """Retrieves a paginated list of images with total count.

        Args:
            pagination: Pagination parameters.
            order: Sort order for upload_time ("desc" or "asc").

        Returns:
            tuple[List[ImageDetailsDTO], int]: List of images and total count.

        Raises:
            InvalidSortOrderError: If order parameter is invalid.
            ImageListServiceError: If retrieval fails.
        """
        self._logger.info(
            f"Retrieving images list with pagination: page={pagination.page},"
            f" per_page={pagination.per_page}, order={order}")

        if order.lower() not in ("desc", "asc"):
            raise InvalidSortOrderError()

        limit, offset = pagination.to_sql_params()

        try:
            total_count = self._image_repository.count()
        except RepositoryError as e:
            raise ImageListServiceError(e.message, e.status_code)

        if not total_count:
            self._logger.info("No images found in repository")
            return [], 0

        try:
            images_dto = self._image_repository.list_all(limit, offset, order)
        except RepositoryError as e:
            raise ImageListServiceError(e.message, e.status_code)
        except ValueError as e:
            raise InvalidSortOrderError(str(e))
        else:
            self._logger.info(f"Retrieved {len(images_dto)} images from repository")
            return images_dto, total_count

    def get_image_details(self, filename: str) -> ImageDetailsDTO:
        """Retrieves detailed information about a specific image.

        Args:
            filename: Name of the image file.

        Returns:
            ImageDetailsDTO: Image details if found.

        Raises:
            ImageNotFoundError: If image not found.
            ImageDetailsServiceError: If retrieval fails due to other errors.
        """
        self._logger.info(f"Retrieving image details for: {filename}")

        try:
            image_details = self._image_repository.get_by_filename(filename)
        except RepositoryError as e:
            raise ImageDetailsServiceError(e.message, e.status_code)

        if not image_details:
            self._logger.info(f"Image not found: {filename}")
            raise ImageNotFoundError(filename)

        self._logger.info(f"Image details retrieved for: {filename}")
        return image_details

    def delete_image(self, filename: str) -> bool:
        """Deletes an image file and its metadata.

        Args:
            filename: Name of the image file to delete.

        Returns:
            bool: True if deletion was successful.

        Raises:
            ImageNotFoundError: If image not found in filesystem or database.
            ImageDeletionServiceError: If deletion fails due to other errors.
        """
        self._logger.info(f"Starting image deletion process for: {filename}")

        try:
            image_details = self._image_repository.get_by_filename(filename)
            if not image_details:
                raise ImageNotFoundError(filename)
        except RepositoryError as e:
            raise ImageDeletionServiceError(e.message, e.status_code)

        try:
            self._file_handler.delete_file(filename)
            self._logger.info(f"File deleted from filesystem: {filename}")
        except APIError as e:
            if e.status_code == 404:
                raise ImageNotFoundError(filename)
            raise ImageDeletionServiceError(e.message, e.status_code)

        try:
            db_deleted = self._image_repository.delete_by_filename(filename)
            if not db_deleted:
                self._logger.warning(f"Image '{filename}' was not found in database during deletion")
                raise ImageNotFoundError(filename)
        except RepositoryError as e:
            raise ImageDeletionServiceError(e.message, e.status_code)

        self._logger.info(f"Image '{filename}' deleted successfully from both filesystem and database")
        return True
