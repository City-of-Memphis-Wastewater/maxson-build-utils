# src/dworshak_prompt/web_prompt.py
from __future__ import annotations 
import threading
import urllib.parse 
import time
from typing import Any

# Setup logger
import logging
logger = logging.getLogger(__name__)

from .prompt_manager_web import PromptManagerWeb # for type hinting
from .browser_utils import launch_browser, is_server_running
from .types import SensitiveStr 

def browser_get_input(
    message: str, 
    suggestion: str | None = None, 
    hide: bool = False, 
    manager: PromptManagerWeb = None, 
    stop_event: threading.Event | None = None
    ) -> str | None:
    
    url = manager.get_server_url()
    if not is_server_running(url):
        from .server import run_prompt_server_in_thread
        run_prompt_server_in_thread(manager)
        url = manager.get_server_url()
    req_id = manager.register_prompt("input_key", message, hide, suggestion=suggestion)
    
    encoded_msg = urllib.parse.quote_plus(message)
    encoded_sug = urllib.parse.quote_plus(suggestion or "")
    full_url = f"{url}/config_modal?request_id={req_id}&message={encoded_msg}&hide_input={hide}&suggestion={encoded_sug}"
    launch_browser(full_url)
    
    logger.debug(f"[WEBPROMPT] Started polling for req_id={req_id}")

    # small timeout to auto-cancel after inactivity (e.g. 10 minutes)
    start_time = time.time()
    MAX_WAIT_SEC = 600

    # The Polling Loop
    while True:
        # 1. Check if the external shutdown event was triggered
        if stop_event and stop_event.is_set():
            logger.debug(f"[WEBPROMPT] Stop event set → cancelling req_id={req_id}") 
            manager.cancel_prompt(req_id)  # Cleanup
            return None
        
        # Check explicit user cancel
        if manager.is_cancelled(req_id):
            logger.debug(f"[WEBPROMPT] Detected cancel for req_id={req_id} → returning None")
            return None

        # Check if the user submitted data
        val = manager.get_and_clear_result(req_id)
        if val is not None: 
            # FIX: Mask the log output if 'hide' is True
            log_val = "'********'" if hide else repr(val)
            logger.debug(f"[WEBPROMPT] Got result for req_id={req_id}: {log_val}")
            return val

        # Inactivity timeout
        if time.time() - start_time > MAX_WAIT_SEC:
            logger.debug(f"[WEBPROMPT] Inactivity timeout ({MAX_WAIT_SEC}s) → cancelling")
            manager.cancel_prompt(req_id)
            return None

        # Responsive sleep (0.3s is snappier for cancel detection)
        sleep_time = 0.3
        if stop_event:
            if stop_event.wait(timeout=sleep_time):
                return None
        else:
            time.sleep(sleep_time)
