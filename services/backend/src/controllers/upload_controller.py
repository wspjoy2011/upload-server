"""Upload controller for handling image upload, listing, and management requests.

This module contains the UploadHandler class which handles all HTTP requests
related to image operations including upload, listing, viewing, and deletion.
"""

from logging import Logger
from http.server import BaseHTTPRequestHandler

from python_multipart import parse_form

from decorators.di import inject
from decorators.routing import route, register_routes
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
from interfaces.services import ImageUploadServiceInterface
from mixins.pagination import PaginationMixin
from mixins.http import RouterMixin, JsonResponseMixin


@register_routes
@inject('image_service', 'logger')
class UploadHandler(BaseHTTPRequestHandler, JsonResponseMixin, RouterMixin, PaginationMixin):
    """Handles HTTP requests related to file uploads, listing, and deletion.

    This controller provides RESTful endpoints for:
    - Health check (GET /)
    - Image listing with pagination (GET /upload/)
    - Image upload (POST /upload/)
    - Image deletion (DELETE /upload/<filename>)
    - Image details (GET /upload/<filename>)

    Routes are automatically registered using @route decorators.
    The @register_routes class decorator scans for @route decorated methods
    and populates the appropriate routes dictionaries.

    Dependencies are automatically injected via @inject decorator:
    - image_service: ImageUploadServiceInterface
    - logger: Logger instance

    Use:
        - Dynamic dispatch based on routes defined via decorators.
        - Automatic dependency injection for services.
    """

    image_service: ImageUploadServiceInterface
    logger: Logger

    def do_GET(self):
        """Handles GET requests and dispatches them based on route."""
        self.logger.info(f"GET request received: {self.path}")
        self.handle_request(self.routes_get)

    def do_POST(self):
        """Handles POST requests and dispatches them based on route."""
        self.handle_request(self.routes_post)

    def do_DELETE(self):
        """Handles DELETE requests and dispatches them based on route."""
        self.handle_request(self.routes_delete)

    @route('GET', '/')
    def handle_get_root(self):
        """Handles healthcheck at GET /."""
        self.logger.info("Healthcheck endpoint hit: /")
        self.send_json_response(200, {"message": "Welcome to the Upload Server"})

    @route('GET', '/upload/')
    def handle_get_uploads(self):
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
            self.logger.info(
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
            self.logger.error(f"Failed to list images: {e.message}")
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

        self.logger.info(
            f"Returned {len(images_dto)} images (page {pagination_dto.page}"
            f" of {(total_count + pagination_dto.per_page - 1) // pagination_dto.per_page}, order={order})")
        self.send_json_response(200, response)

    @route('POST', '/upload/')
    def handle_post_upload(self):
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

        self.logger.info(f"File '{uploaded_file_dto.filename}' uploaded successfully.")
        self.send_json_response(200, {
            "filename": uploaded_file_dto.filename,
            "url": uploaded_file_dto.url
        })

    @route('DELETE', '/upload/<filename>')
    def handle_delete_upload(self):
        """Deletes a file by name from the upload directory and database.

        Side effects:
            - Deletes file from filesystem.
            - Deletes record from database.
            - Sends JSON response or error.
        """
        filename = self.get_route_param("filename")
        self.logger.info(f"Delete request for filename: {filename}")

        if not filename:
            self.send_json_error(400, "Filename not provided.")
            return

        try:
            self.image_service.delete_image(filename)
        except ImageNotFoundError as e:
            self.send_json_error(e.status_code, e.message)
            return
        except ImageDeletionServiceError as e:
            self.logger.error(f"Failed to delete image '{filename}': {e.message}")
            self.send_json_error(e.status_code, e.message)
            return

        self.logger.info(f"File '{filename}' deleted successfully.")
        self.send_json_response(200, {"message": f"File '{filename}' deleted successfully."})

    @route('GET', '/upload/<filename>')
    def handle_get_upload_details(self):
        """Returns detailed information about a specific image file.

        Side effects:
            - Queries database for file metadata.
            - Sends JSON response with image details or error.
        """
        filename = self.get_route_param("filename")
        self.logger.info(f"Upload details request for filename: {filename}")

        if not filename:
            self.send_json_error(400, "Filename not provided.")
            return

        try:
            image_details = self.image_service.get_image_details(filename)
        except ImageNotFoundError as e:
            self.send_json_error(e.status_code, e.message)
            return
        except ImageDetailsServiceError as e:
            self.logger.error(f"Failed to get image details for '{filename}': {e.message}")
            self.send_json_error(e.status_code, e.message)
            return

        image_dict = image_details.as_dict()
        image_dict["url"] = f"/images/{filename}"

        self.logger.info(f"Image details retrieved for '{filename}'.")
        self.send_json_response(200, image_dict)
