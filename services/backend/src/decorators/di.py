"""Dependency injection container and decorators.

This module provides a dependency injection system that allows automatic
resolution and injection of dependencies into classes and methods.
"""

from typing import Dict, Any, Callable, TypeVar, Type
from logging import Logger

T = TypeVar('T')


class DIContainer:
    """Dependency injection container for managing service instances.
    
    Provides registration and resolution of dependencies with support for
    singleton and transient lifetimes.
    """

    def __init__(self):
        self._services: Dict[str, Callable[[], Any]] = {}
        self._singletons: Dict[str, Any] = {}
        self._singleton_flags: Dict[str, bool] = {}
        self._service_types: Dict[str, type] = {}

    def register(self, name: str, factory: Callable[[], Any], singleton: bool = True,
                 service_type: type = None) -> None:
        """Register a service with the container.
        
        Args:
            name: Service name to register
            factory: Factory function that creates the service instance
            singleton: Whether to create only one instance (default: True)
            service_type: Type hint for the service (optional)
        """
        self._services[name] = factory
        self._singleton_flags[name] = singleton
        if service_type:
            self._service_types[name] = service_type

    def get(self, name: str) -> Any:
        """Resolve a service by name.
        
        Args:
            name: Service name to resolve
            
        Returns:
            Service instance
            
        Raises:
            ValueError: If service is not registered
        """
        if name not in self._services:
            raise ValueError(f"Service '{name}' is not registered")

        if self._singleton_flags.get(name, True) and name in self._singletons:
            return self._singletons[name]

        factory = self._services[name]
        instance = factory()

        if self._singleton_flags.get(name, True):
            self._singletons[name] = instance

        return instance

    def is_registered(self, name: str) -> bool:
        """Check if a service is registered.
        
        Args:
            name: Service name to check
            
        Returns:
            True if service is registered, False otherwise
        """
        return name in self._services

    def get_service_type(self, name: str) -> type:
        """Get the registered type for a service.
        
        Args:
            name: Service name
            
        Returns:
            Service type if registered, Any otherwise
        """
        return self._service_types.get(name, Any)


_container = DIContainer()


def get_container() -> DIContainer:
    """Get the global DI container instance.
    
    Returns:
        Global DIContainer instance
    """
    return _container


def inject(*service_names: str) -> Callable[[Type[T]], Type[T]]:
    """Class decorator that automatically injects dependencies.
    
    Injects specified services as instance attributes during class instantiation.
    The services are resolved from the global DI container.
    
    IMPORTANT: Dependencies are injected BEFORE calling the original __init__,
    which is crucial for classes like BaseHTTPRequestHandler where handle()
    is called inside __init__.
    
    Note: For proper IDE support and type checking, you should explicitly
    declare the injected attributes in your class with type annotations:
    
    @inject('image_service', 'logger')
    class MyController:
        image_service: ImageUploadServiceInterface  # <- explicit type annotation
        logger: Logger                              # <- explicit type annotation
        
        def handle_request(self):
            self.image_service.upload_image(...)    # <- IDE will provide autocomplete
            self.logger.info("Request handled")     # <- IDE will provide autocomplete
    
    Args:
        *service_names: Names of services to inject
        
    Returns:
        Decorated class with dependency injection
    """

    def decorator(cls: Type[T]) -> Type[T]:
        original_init = cls.__init__

        def new_init(self, *args, **kwargs):
            container = get_container()
            for service_name in service_names:
                if container.is_registered(service_name):
                    setattr(self, service_name, container.get(service_name))
                else:
                    raise ValueError(f"Service '{service_name}' is not registered in DI container")

            original_init(self, *args, **kwargs)

        cls.__init__ = new_init

        cls._injected_services = service_names

        return cls

    return decorator


def setup_container() -> None:
    """Setup the DI container with default service registrations.
    
    Registers all available services with their factory functions.
    This should be called once during application startup.
    """
    from services.dependencies import get_image_upload_service
    from interfaces.services import ImageUploadServiceInterface
    from settings.logging_config import get_logger

    container = get_container()

    container.register(
        'image_service',
        get_image_upload_service,
        singleton=True,
        service_type=ImageUploadServiceInterface
    )
    container.register(
        'logger',
        lambda: get_logger(__name__),
        singleton=True,
        service_type=Logger
    )
