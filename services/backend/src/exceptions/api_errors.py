class APIError(Exception):
    """Base class for API-related errors."""
    status_code = 400
    message = "API Error"

    def __init__(self, message: str = None):
        if message:
            self.message = message
        super().__init__(self.message)


class NotSupportedFormatError(APIError):
    """Raised when file format is not supported."""

    def __init__(self, supported_formats: set[str]):
        formats_list = ", ".join(sorted(supported_formats))
        message = f"Unsupported file format. Supported formats: {formats_list}."
        super().__init__(message)


class MaxSizeExceedError(APIError):
    """Raised when file size exceeds allowed limit."""

    def __init__(self, max_size_bytes: int):
        max_size_mb = max_size_bytes / (1024 * 1024)
        message = f"File size exceeds the maximum allowed size of {max_size_mb:.1f} MB."
        super().__init__(message)


class MultipleFilesUploadError(APIError):
    """Raised when more than one file is uploaded."""

    def __init__(self):
        message = "Only one file can be uploaded per request."
        super().__init__(message)
