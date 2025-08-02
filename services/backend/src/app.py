"""Main application entry point for the image upload server.

This module provides the main entry point for starting the HTTP server
with multiprocessing support. It handles server startup, worker process
management, and graceful shutdown.

Side effects:
    - Binds and serves HTTP servers on configured ports.
    - Logs server startup and worker information.
"""

from multiprocessing import Process, current_process
from typing import cast
from http.server import HTTPServer

from controllers.main import CompositeController
from controllers.upload import UploadController
from controllers.healthcheck import HealthCheckController
from decorators.di import setup_container
from interfaces.protocols import RequestHandlerFactory
from settings.config import config
from settings.logging_config import get_logger

logger = get_logger(__name__)

setup_container()

CompositeController.register_controller(HealthCheckController)
CompositeController.register_controller(UploadController)


def run_server_on_port(port: int):
    """Starts a single HTTP server instance on the specified port.

    Args:
        port (int): The port number to bind the HTTP server to.

    Side effects:
        - Starts blocking HTTP server loop.
        - Logs process and port information.
    """
    current_process().name = f"worker-{port}"
    logger.info(f"Starting server on http://0.0.0.0:{port}")

    logger.info(f"Registered controllers: {CompositeController.get_registered_controllers()}")

    all_routes = CompositeController.get_all_routes()
    for method, routes in all_routes.items():
        if routes:
            logger.info(f"{method} routes:")
            for path, handler in routes.items():
                logger.info(f"  {path} -> {handler}")

    server = HTTPServer(("0.0.0.0", port), cast(RequestHandlerFactory, CompositeController))
    server.serve_forever()


def run(workers: int = 1, start_port: int = 8000):
    """Starts multiple server worker processes for concurrent handling.

    Args:
        workers (int): Number of worker processes to spawn.
        start_port (int): Starting port number for workers.

    Side effects:
        - Launches `workers` processes each listening on a unique port.
        - Logs worker startup.
    """
    for i in range(workers):
        port = start_port + i
        p = Process(target=run_server_on_port, args=(port,))
        p.start()
        logger.info(f"Worker {i + 1} started on port {port}")


if __name__ == '__main__':
    run(workers=config.WEB_SERVER_WORKERS, start_port=config.WEB_SERVER_START_PORT)
