"""Interfaces for file handler implementations.

This module defines protocol classes that file handler implementations
must adhere to, ensuring consistent behavior across different
implementations.
"""

from abc import ABC, abstractmethod

from dto.file import UploadedFileDTO


class FileHandlerInterface(ABC):
    """Protocol defining the interface for file handler implementations.

    Any class implementing this protocol must provide methods for
    handling file uploads and other file operations.
    """

    @abstractmethod
    def handle_upload(self, file) -> UploadedFileDTO:
        """Validate and save an uploaded file.

        Args:
            file: The uploaded file object with file_name and file_object.

        Returns:
            UploadedFileDTO: DTO containing information about the saved file.

        Raises:
            Various exceptions for validation failures.
        """
        pass

    @abstractmethod
    def delete_file(self, filename: str) -> None:
        """Delete a file from the file system.

        Args:
            filename: The name of the file to delete.

        Raises:
            FileNotFoundError: If the file does not exist.
            UnsupportedFileFormatError: If the file has an unsupported extension.
            PermissionDeniedError: If there are permission issues deleting the file.
            APIError: For other errors that may occur during deletion.
        """
        pass
