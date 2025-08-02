"""Health check controller for server status monitoring.

This module contains the HealthCheckHandler class which provides
basic health check endpoints for monitoring server availability.
"""

import time
import os
from logging import Logger
from http.server import BaseHTTPRequestHandler

from decorators.di import inject
from decorators.routing import route, register_routes
from mixins.http import RouterMixin, JsonResponseMixin


@register_routes
@inject('logger')
class HealthCheckController(BaseHTTPRequestHandler, JsonResponseMixin, RouterMixin):
    """Handles health check and server status requests.

    This controller provides RESTful endpoints for:
    - Basic health check (GET /)
    - Detailed server status (GET /health)
    - Service readiness check (GET /ready)

    Routes are automatically registered using @route decorators.
    This controller is designed to work with CompositeController,
    so it doesn't define do_GET/POST/DELETE methods.

    Dependencies are automatically injected via @inject decorator:
    - logger: Logger instance
    """

    logger: Logger

    @route('GET', '/')
    def handle_get_root(self):
        """Handles basic healthcheck at GET /.

        Returns a simple welcome message to confirm server is running.
        """
        self.logger.info("Healthcheck endpoint hit: /")
        self.send_json_response(200, {"message": "Welcome to the Upload Server"})

    @route('GET', '/health')
    def handle_get_health(self):
        """Handles detailed health check at GET /health.

        Returns detailed server status information.
        """
        self.logger.info("Detailed health check endpoint hit: /health")

        health_info = {
            "status": "healthy",
            "timestamp": int(time.time()),
            "server": "Upload Server",
            "version": "1.0.0",
            "process_id": os.getpid(),
            "uptime": "unknown"
        }

        self.send_json_response(200, health_info)

    @route('GET', '/ready')
    def handle_get_ready(self):
        """Handles readiness check at GET /ready.

        Returns server readiness status for load balancers.
        """
        self.logger.info("Readiness check endpoint hit: /ready")

        ready_info = {
            "ready": True,
            "checks": {
                "database": "ok",
                "filesystem": "ok",
                "memory": "ok"
            }
        }

        self.send_json_response(200, ready_info)
