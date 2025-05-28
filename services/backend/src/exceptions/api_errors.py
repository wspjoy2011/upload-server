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


class FileNotFoundError(APIError):
    """Raised when the requested file is not found on the server.

    Args:
        filename (str, optional): The name of the file that couldn't be found.
    """
    status_code = 404

    def __init__(self, filename: str = None):
        message = "File not found."
        if filename:
            message = f"File '{filename}' not found."
        super().__init__(message)


class PermissionDeniedError(APIError):
    """Raised when there are permission issues with file operations.

    Args:
        operation (str, optional): The operation that couldn't be performed.
    """
    status_code = 500

    def __init__(self, operation: str = None):
        message = "Permission denied."
        if operation:
            message = f"Permission denied to {operation}."
        super().__init__(message)


class UnsupportedFileFormatError(APIError):
    """Raised when a file has an unsupported format.

    Args:
        extension (str, optional): The unsupported file extension.
        supported_formats (set[str], optional): Set of supported formats to include in message.
    """

    def __init__(self, extension: str = None, supported_formats: set[str] = None):
        if extension and supported_formats:
            formats_list = ", ".join(sorted(supported_formats))
            message = f"Unsupported file format '{extension}'. Supported formats: {formats_list}."
        elif supported_formats:
            formats_list = ", ".join(sorted(supported_formats))
            message = f"Unsupported file format. Supported formats: {formats_list}."
        else:
            message = "Unsupported file format."
        super().__init__(message)
