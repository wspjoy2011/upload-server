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

from db.dependencies import get_image_repository
from db.dto import ImageDTO
from exceptions.api_errors import APIError
from exceptions.repository_errors import RepositoryError
from handlers.dependencies import get_file_handler
from interfaces.pagination import InvalidPageNumberError, InvalidPerPageError
from interfaces.protocols import RequestHandlerFactory
from mixins.pagination import PaginationMixin
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
    }

    routes_post = {
        "/upload/": "_handle_post_upload",
    }

    routes_delete = {
        "/upload/": "_handle_delete_upload",
    }

    @property
    def logger(self) -> Logger:
        """Return the application logger."""
        return logger

    def do_GET(self):
        """Handles GET requests and dispatches them based on route."""
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
        if order not in ("desc", "asc"):
            self.send_json_error(400, "Order parameter must be 'desc' or 'asc'")
            return

        limit, offset = self.get_limit_offset(pagination_dto)

        repository = get_image_repository()

        total_count = repository.count()

        if not total_count:
            self.send_json_error(404, "No images found.")
            return

        try:
            images_dto = repository.list_all(limit, offset, order)
        except RepositoryError as e:
            logger.error(f"Failed to list images: {str(e)}")
            self.send_json_error(500, f"Failed to list images: {str(e)}")
        except ValueError as e:
            logger.error(f"Invalid order parameter: {str(e)}")
            self.send_json_error(400, str(e))
        else:
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
        file_handler = get_file_handler()

        try:
            on_file_callback = file_handler.get_file_collector(files)
            parse_form(headers, self.rfile, lambda _: None, on_file_callback)  # type: ignore[arg-type]
        except APIError as e:
            self.send_json_error(e.status_code, e.message)
            return

        if not files:
            self.send_json_error(400, "No files uploaded")
            return

        try:
            uploaded_file_dto = file_handler.handle_upload(files[0])
        except APIError as e:
            self.send_json_error(e.status_code, e.message)
            return

        image_dto = ImageDTO(
            filename=uploaded_file_dto.filename,
            original_name=uploaded_file_dto.original_name,
            size=uploaded_file_dto.size,
            file_type=uploaded_file_dto.extension
        )

        repository = get_image_repository()

        try:
            repository.create(image_dto)
        except RepositoryError as e:
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
        filename = self.extract_path_param("/upload/")
        if not filename:
            self.send_json_error(400, "Filename not provided.")
            return

        file_handler = get_file_handler()
        try:
            file_handler.delete_file(filename)
        except APIError as e:
            self.send_json_error(e.status_code, e.message)
            return

        repository = get_image_repository()
        try:
            db_deleted = repository.delete_by_filename(filename)
            if not db_deleted:
                logger.warning(f"File '{filename}' was not found in database while deleting")
        except RepositoryError as e:
            logger.error(f"Failed to delete file '{filename}' from database: {str(e)}")
            self.send_json_error(e.status_code, e.message)
            return

        logger.info(f"File '{filename}' deleted successfully.")
        self.send_json_response(200, {"message": f"File '{filename}' deleted successfully."})


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
