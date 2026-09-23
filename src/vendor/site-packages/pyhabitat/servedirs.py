#!/usr/bin/env python3
"""
servedirs.py - tiny directory server with UI + shutdown button
"""

from __future__ import annotations

import os
import threading
from pathlib import Path
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from urllib.parse import quote
from string import Template
from html import escape

# ----------------------------
# HTML template
# ----------------------------

HTML_PAGE = Template("""<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>servedirs</title>
  <style>
    body {
      font-family: system-ui, sans-serif;
      max-width: 900px;
      margin: 40px auto;
      background: #f6f7f9;
      color: #111;
    }
    h1 { font-size: 20px; }
    .bar {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 20px;
    }
    button {
      padding: 8px 12px;
      border: 0;
      border-radius: 6px;
      background: #d9534f;
      color: white;
      cursor: pointer;
    }
    button:hover {
      background: #c9302c;
    }
    ul {
      list-style: none;
      padding: 0;
      background: white;
      border-radius: 10px;
      padding: 10px;
      box-shadow: 0 2px 10px rgba(0,0,0,0.08);
    }
    li {
      padding: 6px 8px;
    }
    a {
      text-decoration: none;
      color: #0d6efd;
    }
  </style>
</head>
<body>
  <div class="bar">
    <h1>servedirs</h1>
    <button onclick="fetch('/shutdown', {method: 'POST'})
      .then(() => document.body.innerHTML='<h2>Server stopped</h2>')">
      Stop server
    </button>
  </div>

  <ul>
    $items
  </ul>
</body>
</html>
""")


# ----------------------------
# Handler
# ----------------------------

class ServedirsHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, directory=None, **kwargs):
        self.base_directory = Path(directory or os.getcwd()).resolve()
        super().__init__(*args, directory=str(self.base_directory), **kwargs)

    def log_message(self, format, *args):
        print(f"[servedirs] {self.address_string()} - {format % args}")

    def do_POST(self):
        if self.path == "/shutdown":
            self.send_response(204)
            self.end_headers()

            # shutdown must run in another thread
            threading.Thread(
                target=self.server.shutdown,
                daemon=True,
            ).start()
            return

        self.send_error(404)

    def list_directory(self, path):
        """Override directory listing with custom HTML."""
        try:
            entries = sorted(os.listdir(path))
        except OSError:
            self.send_error(404, "No permission to list directory")
            return None

        items = []

        # parent link
        if os.path.abspath(path) != str(self.base_directory):
            items.append('<li><a href="../">../ (parent)</a></li>')

        for name in entries:
            full = os.path.join(path, name)
            #display = name + ("/" if os.path.isdir(full) else "")
            display = escape(name) + ("/" if os.path.isdir(full) else "")
            link = quote(name)

            if os.path.isdir(full):
                link += "/"

            items.append(f'<li><a href="{link}">{display}</a></li>')

        html = HTML_PAGE.substitute(items="\n".join(items)) # Template()
        #html = HTML_PAGE.replace("{items}", "\n".join(items)) # no CSS
        encoded = html.encode("utf-8")

        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)
        return None


# ----------------------------
# Server runner
# ----------------------------

def serve_directory_custom(path: str | Path, host="127.0.0.1", port=8000):
    path = Path(path).resolve()

    if not path.exists():
        raise FileNotFoundError(path)

    httpd = ThreadingHTTPServer(
        (host, port),
        lambda *args, **kwargs: ServedirsHandler(*args, directory=path, **kwargs),
    )

    print(f"Serving: {path}")
    print(f"URL: http://{host}:{port}/")
    print("Press Ctrl+C or use /shutdown")

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()
        print("Server stopped")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--path", default=".")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)

    args = parser.parse_args()

    serve_directory_custom(args.path, args.host, args.port)
