import socketserver
import http.server
from django.core.management.base import BaseCommand

class HelloHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path in ("/", "/index.html"):
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"<html><body><h1>Hola mundo desde Django Observatory</h1></body></html>")
        else:
            self.send_error(404)

class Command(BaseCommand):
    help = "Run the Django Observatory panel on a separate port."

    def add_arguments(self, parser):
        parser.add_argument("--port", type=int, default=8001, help="Port to serve the observatory on")

    def handle(self, *args, **options):
        port = options["port"]
        socketserver.TCPServer.allow_reuse_address = True
        with socketserver.TCPServer(("", port), HelloHandler) as httpd:
            self.stdout.write(self.style.SUCCESS(f"Observatory serving on http://127.0.0.1:{port}/"))
            try:
                httpd.serve_forever()
            except KeyboardInterrupt:
                self.stdout.write("\nShutting down observatory server")