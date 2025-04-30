"""Type protocols for type safety and interface contracts.

This module defines structural typing protocols used for better type checking
when working with file-like objects and HTTP request handlers.

Protocols:
    - SupportsWrite: Describes any object with a `write()` method (e.g. file, socket).
    - RequestHandlerFactory: Describes a callable that creates HTTP request handlers.

These are especially useful when working with `cast()` to ensure compatibility
with `shutil.copyfileobj` and `HTTPServer` handler factories.
"""

from http.server import HTTPServer
from socketserver import BaseRequestHandler
from typing import Protocol, TypeVar, Any

_T_contra = TypeVar("_T_contra", contravariant=True)


class SupportsWrite(Protocol[_T_contra]):
    """Protocol for writable objects.

    Any object that implements a `write(s)` method and can accept data of type `_T_contra`.

    Example use:
        Used with `shutil.copyfileobj` where the destination must support `.write()`.

    Methods:
        write(s): Writes a value of type `_T_contra` to the underlying stream.

    Args:
        s (_T_contra): The data to write.

    Returns:
        object: Typically returns the number of bytes written or `None`.
    """

    def write(self, s: _T_contra, /) -> object: ...


class RequestHandlerFactory(Protocol):
    """Protocol for HTTP request handler factories.

    Describes any callable that instantiates a subclass of `BaseRequestHandler`.

    This is used with `HTTPServer` to specify a dynamic request handler creation strategy.

    Args:
        request (Any): The incoming socket object.
        client_address (Any): The (host, port) tuple of the client.
        server (HTTPServer): The associated HTTP server instance.

    Returns:
        BaseRequestHandler: An initialized handler that can process the request.
    """

    def __call__(self, request: Any, client_address: Any, server: HTTPServer) -> BaseRequestHandler: ...
