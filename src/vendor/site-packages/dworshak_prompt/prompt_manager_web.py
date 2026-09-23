# pipeline/prompt_manager_web.py
from __future__ import annotations # Delays annotation evaluation, allowing modern 3.10+ type syntax and forward references in older Python versions 3.8 and 3.9
import threading
import uuid
from typing import Dict, Any, Optional

# Setup Logging
import logging
logger = logging.getLogger(__name__)

class PromptManagerWeb:
    """
    Manages the state of active configuration prompts and submitted results.
    Designed to be instantiated once and shared across threads.
    """
    def __init__(self):
        # Stores active prompt details waiting for frontend detection
        # Key: request_id (str), Value: prompt_data (Dict[str, Any])
        self.active_prompt_request: Dict[str, Any] = {}
        self.active_prompt_lock = threading.Lock()
        
        # Stores results submitted by the frontend, waiting to unblock Python thread
        # Key: request_id (str), Value: submitted_value (str)
        self.prompt_results: Dict[str, str] = {}
        self.results_lock = threading.Lock()

        # Set of cancelled request_ids
        self._cancelled: set[str] = set()
        
        # Store the dynamically found server URL
        self.server_host_port: str = ""

    def register_prompt(self, key: str, message: str, is_credential: bool, suggestion: str | None = None) -> str:
        """Stores a new prompt request and returns its ID."""
        request_id = str(uuid.uuid4())
        prompt_data = {
            "request_id": request_id,
            "key": key,
            "message": message,
            "is_credential": is_credential,
            "suggestion": suggestion, 
        }
        with self.active_prompt_lock:
            # When singleton, defunct: Critical: Ensure only one prompt is active at a time for simplicity
            #if self.active_prompt_request:
            #     raise RuntimeError("A configuration prompt is already active.")
            self.active_prompt_request[request_id] = prompt_data
        return request_id

    def get_active_prompt(self) -> Optional[Dict[str, Any]]:
        """Retrieves the active prompt data for the frontend."""
        with self.active_prompt_lock:
            if not self.active_prompt_request:
                return None
            
            # Retrieve the single active prompt
            return next(iter(self.active_prompt_request.values()))

    def submit_result(self, request_id: str, value: str):
        """Stores a submitted result and clears the active request."""
        # ignore if already cancelled
        if request_id in self._cancelled:
            logger.debug(f"[MANAGER] Ignoring submit for cancelled req_id={request_id}")
            return
        logger.debug(f"[MANAGER] Submitting result for {request_id}")

        with self.results_lock:
            self.prompt_results[request_id] = value
        
        with self.active_prompt_lock:
            self.active_prompt_request.pop(request_id, None)

    def get_and_clear_result(self, request_id: str) -> Optional[str]:
        """Retrieves a result and removes it to unblock the waiting thread."""
        with self.results_lock:
            return self.prompt_results.pop(request_id, None)

    def cancel_prompt(self, request_id: str):
        """Mark prompt as cancelled and clear active request."""
        logger.debug(f"[MANAGER] Cancelling prompt {request_id}")
        self._cancelled.add(request_id)
        with self.active_prompt_lock:
            self.active_prompt_request.pop(request_id, None)
        with self.results_lock:
            if request_id in self.prompt_results:
                self.prompt_results[request_id] = None  # Ensure polling sees None
        logger.debug(f"[MANAGER] Cancel complete for {request_id}")

    def is_cancelled(self, request_id: str) -> bool:
        return request_id in self._cancelled
            
    def set_server_host_port(self, host_port_str: str):
        """Sets the dynamically found server host and port."""
        self.server_host_port = host_port_str
        
    def get_server_url(self) -> str:
        """Returns the full server URL."""
        if not self.server_host_port:
             return "http://127.0.0.1:8083" 
        return f"http://{self.server_host_port}"


