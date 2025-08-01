"""Main application entry point for the image upload server.

This module defines the UploadHandler for serving HTTP requests, including routes for:
- Health check (/)
- Image listing (/upload/)
- Image upload (/upload/)
- Image deletion (/upload/<filename>)

It also provides logic to start multiple server processes using multiprocessing.

Side effects:
    - Binds and serves HTTP servers on configured ports.
    - Writes uploaded images to disk.
    - Deletes files from disk.
    - Logs actions and errors via configured logger.
"""

from multiprocessing import Process, current_process
from typing import cast
from http.server import HTTPServer, BaseHTTPRequestHandler
from logging import Logger

from python_multipart import parse_form

from exceptions.api_errors import APIError
from exceptions.service_errors import (
    UploadServiceError,
    InvalidSortOrderError,
    ImageListServiceError,
    ImageNotFoundError,
    ImageDeletionServiceError,
    ImageDetailsServiceError
)
from helpers.files import get_file_collector
from interfaces.pagination import InvalidPageNumberError, InvalidPerPageError
from interfaces.protocols import RequestHandlerFactory
from interfaces.services import ImageUploadServiceInterface
from mixins.pagination import PaginationMixin
from services.dependencies import get_image_upload_service
from settings.config import config
from settings.logging_config import get_logger
from mixins.http import RouterMixin, JsonResponseMixin

logger = get_logger(__name__)


class UploadHandler(BaseHTTPRequestHandler, JsonResponseMixin, RouterMixin, PaginationMixin):
    """Handles HTTP requests related to file uploads, listing, and deletion.

    Routes:
        GET / → Healthcheck.
        GET /upload/ → List all uploaded image files.
        POST /upload/ → Upload a single image file.
        DELETE /upload/<filename> → Delete the specified image.

    Use:
        - Dynamic dispatch based on routes defined in route dictionaries.
    """

    routes_get = {
        "/": "_handle_get_root",
        "/upload/": "_handle_get_uploads",
        "/upload/<filename>": "_handle_get_upload_details",
    }

    routes_post = {
        "/upload/": "_handle_post_upload",
    }

    routes_delete = {
        "/upload/<filename>": "_handle_delete_upload",
    }

    @property
    def logger(self) -> Logger:
        """Return the application logger."""
        return logger

    @property
    def image_service(self) -> ImageUploadServiceInterface:
        """Return the image upload service."""
        return get_image_upload_service()

    def do_GET(self):
        """Handles GET requests and dispatches them based on route."""
        logger.info(f"GET request received: {self.path}")
        self.handle_request(self.routes_get)

    def do_POST(self):
        """Handles POST requests and dispatches them based on route."""
        self.handle_request(self.routes_post)

    def do_DELETE(self):
        """Handles DELETE requests and dispatches them based on route."""
        self.handle_request(self.routes_delete)

    def _handle_get_root(self):
        """Handles healthcheck at GET /."""
        logger.info("Healthcheck endpoint hit: /")
        self.send_json_response(200, {"message": "Welcome to the Upload Server"})

    def _handle_get_uploads(self):
        """Returns list of uploaded images as JSON.

        Query parameters:
        page (int, optional): Page number (starting from 1). Default is 1.
        per_page (int, optional): Number of items per page. Default is 10.
        order (str, optional): Sort order for upload_time ("desc" or "asc"). Default is "desc".

        Side effects:
            - Reads image directory.
            - Sends HTTP response or error.
        """
        query_params = self.parse_query_params()

        try:
            pagination_dto = self.parse_pagination(
                query_params,
                default_page=1,
                default_per_page=10,
                max_per_page=20
            )
            logger.info(
                f"Requested images list with pagination: page={pagination_dto.page}, per_page={pagination_dto.per_page}"
            )
        except InvalidPageNumberError as e:
            self.send_json_error(400, str(e))
            return
        except InvalidPerPageError as e:
            self.send_json_error(400, str(e))
            return

        order = query_params.get("order", "desc").lower()

        try:
            images_dto, total_count = self.image_service.get_images_list(pagination_dto, order)
        except InvalidSortOrderError as e:
            self.send_json_error(e.status_code, e.message)
            return
        except ImageListServiceError as e:
            logger.error(f"Failed to list images: {e.message}")
            self.send_json_error(e.status_code, e.message)
            return

        if not total_count:
            self.send_json_error(404, "No images found.")
            return

        response = {
            "items": [image_dto.as_dict() for image_dto in images_dto],
            "pagination": {
                "page": pagination_dto.page,
                "per_page": pagination_dto.per_page,
                "total": total_count,
                "pages": (total_count + pagination_dto.per_page - 1) // pagination_dto.per_page,
                "has_next": pagination_dto.page < (
                        total_count + pagination_dto.per_page - 1) // pagination_dto.per_page,
                "has_previous": pagination_dto.page > 1
            }
        }

        logger.info(
            f"Returned {len(images_dto)} images (page {pagination_dto.page}"
            f" of {(total_count + pagination_dto.per_page - 1) // pagination_dto.per_page}, order={order})")
        self.send_json_response(200, response)

    def _handle_post_upload(self):
        """Processes and saves an uploaded file.

        Side effects:
            - Parses multipart form data.
            - Validates and saves uploaded file to disk.
            - Saves file metadata to database.
            - Sends response or error.
        """
        content_type = self.headers.get("Content-Type", "")
        if "multipart/form-data" not in content_type:
            self.send_json_error(400, "Bad Request: Expected multipart/form-data")
            return

        content_length = int(self.headers.get("Content-Length", 0))
        headers = {
            "Content-Type": content_type,
            "Content-Length": str(content_length)
        }

        files = []

        try:
            on_file_callback = get_file_collector(files)
            parse_form(headers, self.rfile, lambda _: None, on_file_callback)  # type: ignore[arg-type]
        except APIError as e:
            self.send_json_error(e.status_code, e.message)
            return

        if not files:
            self.send_json_error(400, "No files uploaded")
            return

        try:
            uploaded_file_dto = self.image_service.upload_image(files[0])
        except UploadServiceError as e:
            self.send_json_error(e.status_code, e.message)
            return

        logger.info(f"File '{uploaded_file_dto.filename}' uploaded successfully.")
        self.send_json_response(200, {
            "filename": uploaded_file_dto.filename,
            "url": uploaded_file_dto.url
        })

    def _handle_delete_upload(self):
        """Deletes a file by name from the upload directory and database.

        Side effects:
            - Deletes file from filesystem.
            - Deletes record from database.
            - Sends JSON response or error.
        """
        filename = self.get_route_param("filename")
        logger.info(f"Delete request for filename: {filename}")

        if not filename:
            self.send_json_error(400, "Filename not provided.")
            return

        try:
            self.image_service.delete_image(filename)
        except ImageNotFoundError as e:
            self.send_json_error(e.status_code, e.message)
            return
        except ImageDeletionServiceError as e:
            logger.error(f"Failed to delete image '{filename}': {e.message}")
            self.send_json_error(e.status_code, e.message)
            return

        logger.info(f"File '{filename}' deleted successfully.")
        self.send_json_response(200, {"message": f"File '{filename}' deleted successfully."})

    def _handle_get_upload_details(self):
        """Returns detailed information about a specific image file.

        Side effects:
            - Queries database for file metadata.
            - Sends JSON response with image details or error.
        """
        filename = self.get_route_param("filename")
        logger.info(f"Upload details request for filename: {filename}")

        if not filename:
            self.send_json_error(400, "Filename not provided.")
            return

        try:
            image_details = self.image_service.get_image_details(filename)
        except ImageNotFoundError as e:
            self.send_json_error(e.status_code, e.message)
            return
        except ImageDetailsServiceError as e:
            logger.error(f"Failed to get image details for '{filename}': {e.message}")
            self.send_json_error(e.status_code, e.message)
            return

        image_dict = image_details.as_dict()
        image_dict["url"] = f"/images/{filename}"

        logger.info(f"Image details retrieved for '{filename}'.")
        self.send_json_response(200, image_dict)


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
    server = HTTPServer(("0.0.0.0", port), cast(RequestHandlerFactory, UploadHandler))
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
