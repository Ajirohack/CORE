#!/usr/bin/env python

from http.server import HTTPServer, BaseHTTPRequestHandler
import logging
from pyngrok import ngrok

# Set your ngrok auth token
ngrok.set_auth_token("2OnTqvzzBvuXVlZFc6eeBL70i9f_67ofSoD6vc7NQb4mNya3b")

class HelloHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        body = bytes("Hello", "utf-8")
        self.protocol_version = "HTTP/1.1"
        self.send_response(200)
        self.send_header("Content-Length", len(body))
        self.end_headers()
        self.wfile.write(body)

logging.basicConfig(level=logging.INFO)

# Create the server
server = HTTPServer(("localhost", 0), HelloHandler)

# Create an ngrok tunnel for the server
public_url = ngrok.connect(server.server_port, "http")
logging.info(f"ngrok tunnel created: {public_url}")

try:
    logging.info("Starting server. Press Ctrl+C to stop.")
    server.serve_forever()
except KeyboardInterrupt:
    logging.info("Shutting down server...")
    server.server_close()
    ngrok.disconnect(public_url)
    logging.info("Server stopped cleanly.")