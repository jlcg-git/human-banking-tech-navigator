"""
Local dev server for Human + Banking + Tech Navigator.
Usage:
  python serve.py           → runs on http://localhost:8000
  python serve.py 9000      → runs on http://localhost:9000
"""

import http.server
import socketserver
import webbrowser
import sys
import os

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8000

os.chdir(os.path.dirname(os.path.abspath(__file__)))


class Handler(http.server.SimpleHTTPRequestHandler):
    extensions_map = {
        **http.server.SimpleHTTPRequestHandler.extensions_map,
        ".json": "application/json",
        ".html": "text/html; charset=utf-8",
    }

    def log_message(self, format, *args):
        print(f"  {self.address_string()} — {format % args}")


print(f"\n  Human + Banking + Tech Navigator")
print(f"  Local server: http://localhost:{PORT}")
print(f"  Press Ctrl+C to stop.\n")

webbrowser.open(f"http://localhost:{PORT}")

with socketserver.TCPServer(("", PORT), Handler) as httpd:
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n  Server stopped.")
