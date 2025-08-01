"""File utility functions.

This module provides utility functions for file handling operations
that can be used across different parts of the application.
"""

from typing import List, Callable, Any

from exceptions.api_errors import MultipleFilesUploadError


def get_file_collector(files_list: List) -> Callable[[Any], None]:
    """Returns a callback function that collects files into the provided list.

    Creates a closure that has access to the files_list and implements
    logic for handling file collection during multipart form parsing.
    This function is used with python_multipart library which requires
    a callback for file processing.

    Args:
        files_list: A list where uploaded files will be collected.

    Returns:
        A callback function to be used with multipart form parser.

    Raises:
        MultipleFilesUploadError: If more than one file is being uploaded.
    """

    def on_file(file):
        if len(files_list) >= 1:
            raise MultipleFilesUploadError()
        files_list.append(file)

    return on_file
