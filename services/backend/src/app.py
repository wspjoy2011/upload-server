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

import json
import os
from multiprocessing import Process, current_process
from typing import cast
from http.server import HTTPServer, BaseHTTPRequestHandler

from python_multipart import parse_form

from exceptions.api_errors import APIError, MultipleFilesUploadError
from handlers.files import list_uploaded_images
from interfaces.protocols import RequestHandlerFactory
from handlers.upload import handle_uploaded_file
from settings.config import config
from settings.logging_config import get_logger

logger = get_logger(__name__)


class UploadHandler(BaseHTTPRequestHandler):
    """Handles HTTP requests related to file uploads, listing, and deletion.

    Routes:
        GET / → Healthcheck.
        GET /upload/ → List all uploaded image files.
        POST /upload/ → Upload a single image file.
        DELETE /upload/<filename> → Delete the specified image.

    Use:
        - Dynamic dispatch based on `routes_get`, `routes_post`, and `routes_delete`.
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

    def _send_json_error(self, status_code: int, message: str) -> None:
        """Sends a JSON error response and logs the message.

        Args:
            status_code (int): HTTP status code to return.
            message (str): Error message to return and log.

        Side effects:
            - Logs the error or warning.
            - Writes JSON response to the client.
        """
        if status_code >= 500:
            logger.error(f"{self.command} {self.path} → {status_code}: {message}")
        else:
            logger.warning(f"{self.command} {self.path} → {status_code}: {message}")

        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        response = {"detail": message}
        self.wfile.write(json.dumps(response).encode())

    def do_GET(self):
        """Handles GET requests and dispatches them based on route."""
        self._handle_request(self.routes_get)

    def do_POST(self):
        """Handles POST requests and dispatches them based on route."""
        self._handle_request(self.routes_post)

    def do_DELETE(self):
        """Handles DELETE requests and dispatches them based on route."""
        self._handle_request(self.routes_delete)

    def _handle_request(self, routes: dict[str, str]) -> None:
        """Resolves path to appropriate handler method and calls it.

        Args:
            routes (dict[str, str]): Mapping of path to handler method names.

        Side effects:
            - Calls appropriate handler method.
            - Sends 404 or 500 response if handler is not found or not implemented.
        """
        handler_name = routes.get(self.path)
        if not handler_name:
            for route_prefix, candidate_handler in routes.items():
                if self.path.startswith(route_prefix):
                    handler_name = candidate_handler
                    break

        if not handler_name:
            self._send_json_error(404, "Not Found")
            return

        handler = getattr(self, handler_name, None)
        if not handler:
            self._send_json_error(500, "Handler not implemented.")
            return

        handler()

    def _handle_get_root(self):
        """Handles healthcheck at GET /."""
        logger.info("Healthcheck endpoint hit: /")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"message": "Welcome to the Upload Server"}).encode())

    def _handle_get_uploads(self):
        """Returns list of uploaded images as JSON.

        Side effects:
            - Reads image directory.
            - Sends HTTP response or error.
        """
        try:
            files = list_uploaded_images()
        except FileNotFoundError:
            self._send_json_error(500, "Images directory not found.")
            return
        except PermissionError:
            self._send_json_error(500, "Permission denied to access images directory.")
            return

        if not files:
            self._send_json_error(404, "No images found.")
            return

        logger.info(f"Returned list of {len(files)} uploaded images.")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(files).encode())

    def _handle_post_upload(self):
        """Processes and saves an uploaded file.

        Side effects:
            - Parses multipart form data.
            - Validates and saves uploaded file to disk.
            - Sends response or error.
        """
        content_type = self.headers.get("Content-Type", "")
        if "multipart/form-data" not in content_type:
            self._send_json_error(400, "Bad Request: Expected multipart/form-data")
            return

        content_length = int(self.headers.get("Content-Length", 0))
        headers = {
            "Content-Type": content_type,
            "Content-Length": str(content_length)
        }

        files = []

        def on_file(file):
            if len(files) >= 1:
                raise MultipleFilesUploadError()
            files.append(file)

        try:
            parse_form(headers, self.rfile, lambda _: None, on_file)  # type: ignore[arg-type]
        except APIError as e:
            self._send_json_error(e.status_code, e.message)
            return

        saved_file_info = handle_uploaded_file(files[0])
        logger.info(f"File '{saved_file_info['filename']}' uploaded successfully.")

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(
            f'{{"filename": "{saved_file_info["filename"]}", '
            f'"url": "{saved_file_info["url"]}"}}'.encode()
        )

    def _handle_delete_upload(self):
        """Deletes a file by name from the upload directory.

        Side effects:
            - Deletes file from filesystem.
            - Sends JSON response or error.
        """
        if not self.path.startswith("/upload/"):
            self._send_json_error(404, "Not Found")
            return

        filename = self.path[len("/upload/"):]

        if not filename:
            self._send_json_error(400, "Filename not provided.")
            return

        filepath = os.path.join(config.IMAGES_DIR, filename)
        ext = os.path.splitext(filename)[1].lower()

        if ext not in config.SUPPORTED_FORMATS:
            self._send_json_error(400, "Unsupported file format.")
            return

        if not os.path.isfile(filepath):
            self._send_json_error(404, "File not found.")
            return

        try:
            os.remove(filepath)
        except PermissionError:
            self._send_json_error(500, "Permission denied to delete file.")
            return
        except Exception as e:
            self._send_json_error(500, f"Internal Server Error: {str(e)}")
            return

        logger.info(f"File '{filename}' deleted successfully.")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"message": f"File '{filename}' deleted successfully."}).encode())


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
    run(workers=10)
