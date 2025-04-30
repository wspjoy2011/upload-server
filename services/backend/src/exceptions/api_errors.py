"""Custom API exception classes for upload server.

Defines structured error types for specific failure scenarios such as
unsupported file formats, file size limits, and multiple uploads.

Each error inherits from the base APIError and includes a message and HTTP status code.
"""


class APIError(Exception):
    """Base class for API-related errors.

    Attributes:
        status_code (int): HTTP status code to be returned. Default is 400.
        message (str): Human-readable error message.
    """

    status_code = 400
    message = "API Error"

    def __init__(self, message: str = None):
        """Initializes an APIError with a custom message.

        Args:
            message (str, optional): Optional custom message to override default.
        """
        if message:
            self.message = message
        super().__init__(self.message)


class NotSupportedFormatError(APIError):
    """Raised when the uploaded file format is not supported.

    Args:
        supported_formats (set[str]): Set of allowed file extensions.
    """

    def __init__(self, supported_formats: set[str]):
        formats_list = ", ".join(sorted(supported_formats))
        message = f"Unsupported file format. Supported formats: {formats_list}."
        super().__init__(message)


class MaxSizeExceedError(APIError):
    """Raised when the uploaded file exceeds the allowed size limit.

    Args:
        max_size_bytes (int): Maximum allowed file size in bytes.
    """

    def __init__(self, max_size_bytes: int):
        max_size_mb = max_size_bytes / (1024 * 1024)
        message = f"File size exceeds the maximum allowed size of {max_size_mb:.1f} MB."
        super().__init__(message)


class MultipleFilesUploadError(APIError):
    """Raised when multiple files are uploaded in a single request.

    Used to enforce single-file upload policy.
    """

    def __init__(self):
        message = "Only one file can be uploaded per request."
        super().__init__(message)
