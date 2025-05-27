"""Repository-related exception classes.

This module defines exception types specific to repository operations,
such as database errors, connection issues, or data consistency problems.

These exceptions provide structured error handling for repository operations
and can be mapped to appropriate HTTP responses.
"""

from exceptions.api_errors import APIError


class RepositoryError(APIError):
    """Base class for repository-related errors.

    Attributes:
        status_code (int): HTTP status code to be returned. Default is 500.
        message (str): Human-readable error message.
    """

    status_code = 500
    message = "Database operation failed"


class EntityNotFoundError(RepositoryError):
    """Raised when an entity cannot be found in the repository.

    Args:
        entity_type (str): Type of entity that was not found.
        identifier (str | int): Identifier used for the search.
    """

    status_code = 404

    def __init__(self, entity_type: str, identifier):
        message = f"{entity_type} with identifier '{identifier}' not found"
        super().__init__(message)


class EntityCreationError(RepositoryError):
    """Raised when an entity cannot be created in the repository.

    Args:
        entity_type (str): Type of entity that failed to create.
        reason (str, optional): Specific reason for the failure.
    """

    def __init__(self, entity_type: str, reason: str = None):
        if reason:
            message = f"Failed to create {entity_type}: {reason}"
        else:
            message = f"Failed to create {entity_type}"
        super().__init__(message)


class EntityDeletionError(RepositoryError):
    """Raised when an entity cannot be deleted from the repository.

    Args:
        entity_type (str): Type of entity that failed to delete.
        identifier: Identifier of the entity that couldn't be deleted.
        reason (str, optional): Specific reason for the failure.
    """

    def __init__(self, entity_type: str, identifier, reason: str = None):
        if reason:
            message = f"Failed to delete {entity_type} '{identifier}': {reason}"
        else:
            message = f"Failed to delete {entity_type} '{identifier}'"
        super().__init__(message)


class DatabaseConnectionError(RepositoryError):
    """Raised when the repository cannot connect to the database.

    Attributes:
        status_code (int): HTTP status code to be returned. Default is 503.
    """

    status_code = 503
    message = "Database connection failed"


class QueryExecutionError(RepositoryError):
    """Raised when a database query fails to execute.

    Args:
        query_type (str): Description of the query that failed.
        reason (str, optional): Specific reason for the failure.
    """

    def __init__(self, query_type: str, reason: str = None):
        if reason:
            message = f"Failed to execute {query_type} query: {reason}"
        else:
            message = f"Failed to execute {query_type} query"
        super().__init__(message)
