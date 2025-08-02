"""Main composite controller that aggregates routes from multiple controllers.

This module provides a composite controller that collects routes from
registered controller classes and dispatches requests using the existing
routing infrastructure.
"""

from typing import Dict, Type, List, Any, TypeVar
from logging import Logger
from http.server import BaseHTTPRequestHandler

from decorators.di import inject, get_container
from mixins.http import RouterMixin, JsonResponseMixin

T = TypeVar('T', bound=BaseHTTPRequestHandler)


@inject('logger')
class CompositeController(BaseHTTPRequestHandler, JsonResponseMixin, RouterMixin):
    """Composite controller that aggregates routes from multiple registered controllers.

    This controller:
    - Collects routes from all registered controller classes
    - Uses existing RouterMixin.handle_request() logic
    - Dynamically creates instances of target controllers when needed
    - Provides unified entry point for all application routes

    The key insight is that we reuse the existing @route + @register_routes
    infrastructure by aggregating routes from multiple classes into single
    routes_get/routes_post/routes_delete dictionaries.

    Dependencies are automatically injected via @inject decorator:
    - logger: Logger instance
    """

    logger: Logger

    _registered_controllers: List[Type[BaseHTTPRequestHandler]] = []

    routes_get: Dict[str, str] = {}
    routes_post: Dict[str, str] = {}
    routes_delete: Dict[str, str] = {}
    routes_put: Dict[str, str] = {}

    _handler_to_controller: Dict[str, Type[BaseHTTPRequestHandler]] = {}

    @classmethod
    def register_controller(cls, controller_class: Type[T]):
        """Register a controller class to aggregate its routes.

        Args:
            controller_class: Controller class with @register_routes decorator
        """
        if controller_class not in cls._registered_controllers:
            cls._registered_controllers.append(controller_class)
            cls._aggregate_routes()

    @classmethod
    def _aggregate_routes(cls):
        """Aggregate routes from all registered controllers."""
        cls.routes_get.clear()
        cls.routes_post.clear()
        cls.routes_delete.clear()
        cls.routes_put.clear()
        cls._handler_to_controller.clear()

        for controller_class in cls._registered_controllers:
            controller_routes_get = controller_class.__dict__.get('routes_get', {})
            controller_routes_post = controller_class.__dict__.get('routes_post', {})
            controller_routes_delete = controller_class.__dict__.get('routes_delete', {})
            controller_routes_put = controller_class.__dict__.get('routes_put', {})

            cls._merge_routes(cls.routes_get, controller_routes_get, controller_class, "GET")
            cls._merge_routes(cls.routes_post, controller_routes_post, controller_class, "POST")
            cls._merge_routes(cls.routes_delete, controller_routes_delete, controller_class, "DELETE")
            cls._merge_routes(cls.routes_put, controller_routes_put, controller_class, "PUT")

    @classmethod
    def _merge_routes(cls, target_routes: Dict[str, str], controller_routes: Dict[str, str],
                      controller_class: Type[BaseHTTPRequestHandler], method: str):
        """Helper method to merge routes from a controller into target routes dict."""
        for path, handler_name in controller_routes.items():
            if path in target_routes:
                continue

            composite_handler_name = f"{controller_class.__name__}_{handler_name}"
            target_routes[path] = composite_handler_name
            cls._handler_to_controller[composite_handler_name] = controller_class

    def do_GET(self):
        """Handles GET requests and dispatches them based on aggregated routes."""
        self.logger.info(f"CompositeController GET request: {self.path}")
        self.handle_request(self.routes_get)

    def do_POST(self):
        """Handles POST requests and dispatches them based on aggregated routes."""
        self.logger.info(f"CompositeController POST request: {self.path}")
        self.handle_request(self.routes_post)

    def do_DELETE(self):
        """Handles DELETE requests and dispatches them based on aggregated routes."""
        self.logger.info(f"CompositeController DELETE request: {self.path}")
        self.handle_request(self.routes_delete)

    def do_PUT(self):
        """Handles PUT requests and dispatches them based on aggregated routes."""
        self.logger.info(f"CompositeController PUT request: {self.path}")
        self.handle_request(self.routes_put)

    def __getattr__(self, name: str) -> Any:
        """Dynamically handle method calls for registered controller handlers.

        When handle_request() tries to call a handler method, this method
        intercepts the call and delegates it to the appropriate controller.

        Args:
            name: Handler method name (e.g., "HealthCheckHandler_handle_get_root")

        Returns:
            Callable that executes the handler on the correct controller instance
        """
        if name in self._handler_to_controller:
            controller_class = self._handler_to_controller[name]
            original_handler_name = name.split('_', 1)[1]

            def delegate_handler():
                self.logger.debug(f"Delegating {name} to {controller_class.__name__}.{original_handler_name}")

                controller_instance = controller_class.__new__(controller_class)

                if hasattr(controller_class, '_injected_services'):
                    container = get_container()
                    for service_name in controller_class._injected_services:
                        setattr(controller_instance, service_name, container.get(service_name))

                controller_instance.request = self.request
                controller_instance.client_address = self.client_address
                controller_instance.server = self.server

                self._copy_http_attributes(controller_instance)

                if hasattr(self, 'route_params'):
                    controller_instance.route_params = self.route_params

                controller_instance.logger = self.logger
                controller_instance.wfile = self.wfile

                handler_method = getattr(controller_instance, original_handler_name)
                return handler_method()

            return delegate_handler

        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")

    def _copy_http_attributes(self, target_instance: BaseHTTPRequestHandler):
        """Copy necessary HTTP attributes from self to target instance.
        
        This ensures that the target controller has all the necessary attributes
        for proper HTTP handling, including logging.
        
        Args:
            target_instance: Controller instance to copy attributes to
        """
        attributes_to_copy = [
            'requestline', 'raw_requestline', 'path', 'headers',
            'rfile', 'wfile', 'command', 'request_version'
        ]

        for attr in attributes_to_copy:
            if hasattr(self, attr):
                setattr(target_instance, attr, getattr(self, attr))

    @classmethod
    def get_registered_controllers(cls) -> List[str]:
        """Get list of registered controller names for debugging."""
        return [controller.__name__ for controller in cls._registered_controllers]

    @classmethod
    def get_all_routes(cls) -> Dict[str, Dict[str, str]]:
        """Get all aggregated routes for debugging."""
        return {
            'GET': dict(cls.routes_get),
            'POST': dict(cls.routes_post),
            'DELETE': dict(cls.routes_delete),
            'PUT': dict(cls.routes_put)
        }
