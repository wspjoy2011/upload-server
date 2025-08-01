"""Service-related exception classes.

This module defines exception types specific to service layer operations,
providing structured error handling for business logic operations.

These exceptions can be mapped to appropriate HTTP responses by extracting
their status_code and message attributes.
"""


class ServiceError(Exception):
    """Base class for service-related errors.

    Attributes:
        status_code (int): HTTP status code to be returned. Default is 500.
        message (str): Human-readable error message.
    """

    status_code = 500
    message = "Service operation failed"

    def __init__(self, message: str = None, status_code: int = None):
        """Initializes a ServiceError with optional custom message and status code.

        Args:
            message (str, optional): Optional custom message to override default.
            status_code (int, optional): Optional custom status code to override default.
        """
        if message:
            self.message = message
        if status_code:
            self.status_code = status_code
        super().__init__(self.message)


class UploadServiceError(ServiceError):
    """Raised when image upload service operations fail.

    This error wraps underlying file handler and repository errors,
    preserving their status codes and messages for HTTP response mapping.
    """

    message = "Image upload service operation failed"


class ImageListServiceError(ServiceError):
    """Raised when image listing service operations fail.

    This error wraps underlying repository errors and validation errors,
    preserving their status codes and messages for HTTP response mapping.
    """

    message = "Image list service operation failed"


class InvalidSortOrderError(ServiceError):
    """Raised when an invalid sort order parameter is provided.

    This error indicates that the order parameter is not one of the allowed values.
    """

    status_code = 400
    message = "Order parameter must be 'desc' or 'asc'"


class ImageNotFoundError(ServiceError):
    """Raised when an image cannot be found in filesystem or database.

    This error indicates that the requested image does not exist or cannot be accessed.
    """

    status_code = 404

    def __init__(self, filename: str):
        message = f"Image '{filename}' not found"
        super().__init__(message, 404)


class ImageDeletionServiceError(ServiceError):
    """Raised when image deletion service operations fail.

    This error wraps underlying file handler and repository errors,
    preserving their status codes and messages for HTTP response mapping.
    """

    message = "Image deletion service operation failed"


class ImageDetailsServiceError(ServiceError):
    """Raised when image details retrieval service operations fail.

    This error wraps underlying repository errors,
    preserving their status codes and messages for HTTP response mapping.
    """

    message = "Image details retrieval service operation failed"
