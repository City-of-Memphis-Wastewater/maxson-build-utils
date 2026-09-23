# src/dworshak_prompt/server.py
from __future__ import annotations
import http.server
import socketserver
import json
import urllib.parse
import threading

# Setup logger
import logging
logger = logging.getLogger(__name__)

from .browser_utils import find_open_port

class PromptHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # Silence the console noise

    def do_GET(self):
        parsed_url = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed_url.query)

        # USE LOCAL MANAGER FROM SERVER
        manager = self.server.manager

        if parsed_url.path == "/config_modal":
            self._serve_html(params)
        elif parsed_url.path == "/api/get_active_prompt":
            self._serve_json(manager.get_active_prompt())
        else:
            self.send_error(404)

    def do_POST(self):
        parsed_url = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed_url.query)
        if parsed_url.path == "/api/submit_value":
            # 1. Determine how much data to read
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length == 0:
                self.send_error(400, "Empty submission")
                #self.use_empty_string() ?
                return

            # 2. Read and parse the URL-encoded form data
            post_data = self.rfile.read(content_length).decode('utf-8')
            fields = urllib.parse.parse_qs(post_data)
            
            # 3. Extract our specific fields
            req_id = fields.get('request_id', [None])[0]
            val = fields.get('input_value', [None])[0]
            is_empty_str = fields.get('is_empty_str', ['false'])[0] == 'true'

            if is_empty_str:
                val = ""
            
            if req_id is not None and val is not None:
                #if req_id and val is not None:
                # --- THE HANDOFF VIA ATTACHED MANAGER ---
                self.server.manager.submit_result(req_id, val) 
                self.send_response(200)
                self.end_headers()
            else:
                self.send_error(400, "Missing request_id or input_value")
        # allow user to hit the cancel button
        elif parsed_url.path == "/api/cancel":
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length or 0).decode('utf-8')
            fields = urllib.parse.parse_qs(post_data)
            req_id = fields.get('request_id', [None])[0]
            if req_id:
                logger.debug(f"[SERVER] Received cancel request for req_id={req_id}")
                self.server.manager.cancel_prompt(req_id)
                self._send_response("<html><body><h2>Cancelled</h2><br><script>window.close();</script></body></html>")
                logger.debug(f"[SERVER] Cancel processed for req_id={req_id}")
            else:
                self.send_error(400, "Missing request_id")
                logger.warning(f"[SERVER] Cancel request missing req_id")
        else:
            self.send_error(404)

    def _serve_html(self, params):
        req_id = params.get('request_id', [''])[0]
        msg = params.get('message', ['Input Required'])[0]
        suggestion = params.get('suggestion', [''])[0] 
        hide = params.get('hide_input', ['false'])[0].lower() == 'true'
        input_type = "password" if hide else "text"
        
        # Only add the Toggle Button and Script if we are in hide mode
        toggle_html = ""
        toggle_script = ""
        if hide:
            toggle_html = '<button type="button" id="toggleBtn" onclick="toggleSecret()" style="background:#6c757d; margin-left: 5px;">Show</button>'
            toggle_script = """
            <script>
                function toggleSecret() {
                    var x = document.getElementById("input_field");
                    var btn = document.getElementById("toggleBtn");
                    if (x.type === "password") {
                        x.type = "text";
                        btn.innerText = "Hide";
                    } else {
                        x.type = "password";
                        btn.innerText = "Show";
                    }
                }
            </script>
            """

        # cancel button added
        html = f"""<!DOCTYPE html>
        <html>
        <head>
            <title>Dworshak Prompt</title>
            <style>
                body {{ font-family: sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; background: #f0f2f5; }}
                .card {{ background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.15); width: 100%; max-width: 400px; }}
                h2 {{ margin-top: 0; color: #1c1e21; font-size: 1.2rem; }}
                .input-group {{ display: flex; margin: 20px 0; }}
                input {{ flex-grow: 1; padding: 12px; border: 1px solid #ddd; border-radius: 6px; font-size: 1rem; }}
                button {{ background: #007bff; color: white; border: none; padding: 12px 20px; border-radius: 6px; cursor: pointer; font-weight: bold; }}
                button:hover {{ opacity: 0.9; }}
                .cancel-btn {{ background: #dc2626; margin-right: 10px; }}  /* red for visibility */
                .actions {{ display: flex; justify-content: flex-end; align-items: center; }}
            </style>
        </head>
        <body>
            <div class="card">
                <h2>{msg}</h2>
                <form action="/api/submit_value" method="post">
                    <input type="hidden" name="request_id" value="{req_id}">
                    <div class="input-group">
                        <input id="input_field"
                            type="{input_type}"
                            name="input_value"
                            value="{suggestion}"
                            autofocus
                            onfocus="this.select()"
                            autocomplete="off"
                            spellcheck="false"
                            required>
                        {toggle_html}
                    </div>
                    <div class="actions">
                        <button type="button" class="cancel-btn" onclick="cancelPrompt()">Cancel</button>
                        <button type="button" onclick="submitValue()">Submit</button>
                        <!--button type="submit">Submit</button-->
                    </div>
                </form>
            </div>
            {toggle_script}
            <script>
                function cancelPrompt() {{
                    fetch('/api/cancel', {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/x-www-form-urlencoded' }},
                        body: 'request_id={req_id}'
                    }}).then(() => {{
                        window.close();
                    }}).catch(err => {{
                        console.error('Cancel failed:', err);
                    }});
                }}
                function submitValue() {{
                    const val = document.getElementById('input_field').value;
                    // Explicitly send a type flag
                    const payload = new URLSearchParams({{
                        request_id: '{req_id}',
                        input_value: val,
                        is_empty_str: val.trim() === "" ? "true" : "false" 
                    }});
                    fetch('/api/submit_value', {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/x-www-form-urlencoded' }},
                        body: payload.toString()
                    }}).then(() => window.close());
                }}
            </script>
        </body></html>"""
        self._send_response(html, "text/html")

    def _send_response(self, content, content_type="text/html"):
        self.send_response(200)
        self.send_header("Content-Type", f"{content_type}; charset=utf-8")
        self.end_headers()
        self.wfile.write(content.encode("utf-8"))

    def _serve_json(self, data):
        self._send_response(json.dumps(data or {"show": False}), "application/json")

# Global reference to the running server so we can shut it down cleanly
_current_server: ThreadedServer | None = None

class ThreadedServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True
    daemon_threads = True

def run_prompt_server_in_thread(manager,port=8083):
    global _current_server
    
    # Don't spin up multiple servers if one is already active
    if _current_server is not None:
        #logger.debug(f"[DIAGNOSTIC] Server already active. Hot-swapping manager: {id(manager)}")
        _current_server.manager = manager # Re-point the existing server
        # Ensure the manager knows the existing port
        host, actual_port = _current_server.server_address
        manager.set_server_host_port(f"{host}:{actual_port}")
        return None
    

    port = find_open_port(port)
    _current_server = ThreadedServer(("127.0.0.1", port), PromptHandler)
    _current_server.manager = manager
    manager.set_server_host_port(f"127.0.0.1:{port}")

    thread = threading.Thread(target=_current_server.serve_forever, daemon=True)
    thread.start()
    return thread

def stop_prompt_server():
    """Tells the server to stop the loop and release the socket."""
    global _current_server
    if _current_server:
        # shutdown() stops the serve_forever() loop
        _current_server.shutdown()
        # server_close() releases the socket port
        _current_server.server_close()
        _current_server = None
