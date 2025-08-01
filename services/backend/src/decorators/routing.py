"""Routing decorators for automatic route registration.

This module provides decorators that automatically register methods
as route handlers in the class route dictionaries.
"""

from typing import Callable


def route(method: str, path: str) -> Callable:
    """Decorator to register a method as a route handler.

    Automatically adds the route to the appropriate routes dictionary
    (routes_get, routes_post, routes_delete, routes_put) on the class.

    Args:
        method: HTTP method ('GET', 'POST', 'DELETE', 'PUT')
        path: URL path pattern (e.g., '/upload/', '/upload/<filename>')

    Returns:
        Decorated method with route registration functionality.

    Example:
        @route('GET', '/upload/')
        def get_uploads(self):
            # Handler logic here
            pass
    """

    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        wrapper._route_method = method.upper()
        wrapper._route_path = path
        wrapper._original_func = func

        return wrapper

    return decorator


def register_routes(cls: type) -> type:
    """Class decorator to automatically register all @route decorated methods.

    Scans the class for methods decorated with @route and adds them
    to the appropriate routes dictionary (routes_get, routes_post, etc.).

    Args:
        cls: Class to scan for route decorators

    Returns:
        The same class with routes registered
    """
    route_attrs = {
        'GET': 'routes_get',
        'POST': 'routes_post',
        'DELETE': 'routes_delete',
        'PUT': 'routes_put'
    }

    for method, attr_name in route_attrs.items():
        if not hasattr(cls, attr_name):
            setattr(cls, attr_name, {})

    for method_name in dir(cls):
        method_obj = getattr(cls, method_name)

        if (hasattr(method_obj, '_route_method') and
                hasattr(method_obj, '_route_path')):

            http_method = method_obj._route_method
            path = method_obj._route_path

            routes_attr = route_attrs.get(http_method)
            if routes_attr:
                routes_dict = getattr(cls, routes_attr)
                routes_dict[path] = method_name

    return cls
