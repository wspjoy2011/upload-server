import json
import os
from multiprocessing import Process
from typing import cast
from http.server import HTTPServer, BaseHTTPRequestHandler

from python_multipart import parse_form

from exceptions.api_errors import APIError, MultipleFilesUploadError
from handlers.files import list_uploaded_images
from interfaces.protocols import RequestHandlerFactory
from handlers.upload import handle_uploaded_file
from settings.config import config


class UploadHandler(BaseHTTPRequestHandler):
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
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        response = {"detail": message}
        self.wfile.write(json.dumps(response).encode())

    def do_GET(self):
        self._handle_request(self.routes_get)

    def do_POST(self):
        self._handle_request(self.routes_post)

    def do_DELETE(self):
        self._handle_request(self.routes_delete)

    def _handle_request(self, routes: dict[str, str]) -> None:
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
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"message": "Welcome to the Upload Server"}).encode())

    def _handle_get_uploads(self):
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

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(files).encode())

    def _handle_post_upload(self):
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

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(
            f'{{"filename": "{saved_file_info["filename"]}", '
            f'"url": "{saved_file_info["url"]}"}}'.encode()
        )

    def _handle_delete_upload(self):
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

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"message": f"File '{filename}' deleted successfully."}).encode())


def run_server_on_port(port: int):
    server = HTTPServer(("0.0.0.0", port), cast(RequestHandlerFactory, UploadHandler))
    print(f"Server running on http://localhost:{port}")
    server.serve_forever()


def run(workers: int = 1, start_port: int = 8000):
    for i in range(workers):
        port = start_port + i
        p = Process(target=run_server_on_port, args=(port,))
        p.start()


if __name__ == "__main__":
    run(workers=10)
