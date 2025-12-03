#!/usr/bin/env python3
"""Simple HTTP server for testing the frontend locally."""

import http.server
import socketserver
import os

# Change to the frontend directory
os.chdir(os.path.dirname(__file__))

PORT = 8080

Handler = http.server.SimpleHTTPRequestHandler

with socketserver.TCPServer(("", PORT), Handler) as httpd:
    print(f"Server running at http://localhost:{PORT}/")
    print(f"Open http://localhost:{PORT}/test.html in your browser")
    print("\nPress Ctrl+C to stop")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
