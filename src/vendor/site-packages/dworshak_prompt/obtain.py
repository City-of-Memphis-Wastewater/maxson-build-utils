# src/dworshak_prompt/obtain.py
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, Any

from dworshak_config import DworshakConfig
from dworshak_env import DworshakEnv
from .multiplexer import DworshakPrompt
from .helpers import PromptMode, InterruptBehavior

"""
The obtain pattern.
"""

@dataclass
class ObtainResult:
    value: Optional[str] = None
    is_new: Optional[bool] = False  # True=New, False=Known, None=Cancelled

    @property
    def status_message(self) -> str:
        """Generic statuses that work for any key/service."""
        return {
            True: "Value stored.",
            False: "Value resolved.",
            None: "Exited."
        }.get(self.is_new, "Error.")

    def __bool__(self):
        return self.value is not None

@dataclass
class SecretData(ObtainResult):
    """Overrides status for secret-specific phrasing."""
    @property
    def status_message(self) -> str:
        return {
            True: "Secret stored.",
            False: "Secret known.",
            None: "Exited."
        }.get(self.is_new, "Error.")

    def __repr__(self):
        return f"SecretData(is_new={self.is_new}, value='********')"

# Alias for clarity, or specialized if Config needs different status phrasing
ConfigData = ObtainResult
EnvData = ObtainResult

class Obtain:
    def __init__(self,
        config_path: str | Path | None = None,
        secret_path: str | Path | None = None,
        env_path: str | Path | None = None,
        key_path: str | Path | None = None,
        interface_priority: list[PromptMode] | None = None,
        interface_avoid: set[PromptMode] | None =None,
        interrupt_behavior: InterruptBehavior = InterruptBehavior.RETURN_NONE
        #force_prompt: bool |None=False
        #debug: bool = False,
        #verbose: bool = False
    ):
        self.config_path = config_path
        self.secret_path = secret_path
        self.env_path = env_path
        self.key_path = key_path
        self.interface_priority = interface_priority
        self.interface_avoid = interface_avoid
        self.interrupt_behavior = interrupt_behavior
        #self.force_prompt = force_prompt
        self.prompt = DworshakPrompt(
            interface_priority=interface_priority, # instantiated value can be overrode for each function call
            interface_avoid=interface_avoid, # instantiated value can be overrode for each function call 
            interrupt_behavior=interrupt_behavior, # only instantitated here
        )

    def config(
        self,
        service: str, 
        item: str, 
        message: str | None = None,
        suggestion: str | None = None,
        default: Any | None = None,
        interface_priority: list[PromptMode] | None = None,
        interface_avoid: set[PromptMode] | None = None,
        path: str | Path | None = None,
        overwrite: bool = False,
        forget: bool = False
        #force_prompt: bool|None = None
    ) -> ConfigData:
        if path is None:
            path = self.config_path

        if interface_priority is None:
            interface_priority = self.interface_priority
        if interface_avoid is None:
            interface_avoid = self.interface_avoid
            
        #if force_prompt is None:
        #    force_prompt=self.force_prompt

        config_mgr = DworshakConfig(path = path)
        value = config_mgr.get(service, item)

        """
        # Out June 2026, the overwrite was doing two jobs, both set and re-get.
        # Logic: If it exists and we aren't forcing a refresh, return it.
        if value is not None and not overwrite:
            return ConfigData(value=value, is_new=False)
        """

        # Added force_prompt arg June 2026, allows promot to be made even if it exists, in a way that differs from just overwrite, i think. 
        # Logic: Forcing a prompt, with the existing plain text value as thw auggeation.
        if value is not None and not overwrite: # and not force_prompt:
            return ConfigData(value=value, is_new=False)

        # If missing or overwriting, we use the multiplexer
        new_value = self.prompt.ask(
            message = message or f"Please input CONFIG value\n(service = {service}, item = {item})",
            suggestion = suggestion or value,
            default = default,
            interface_priority = interface_priority,
            interface_avoid = interface_avoid, 
            hide_input=False,
        )

        # Persistence logic
        if new_value is None:
            return ConfigData(value=None, is_new=None)
            
        if not forget:
            config_mgr.set(service, item, new_value, overwrite=overwrite)
            
        return ConfigData(value=new_value, is_new=True)

    def secret(
        self,
        service: str, 
        item: str, 
        message: str | None = None,
        suggestion: str | None = None,
        default: Any | None = None,
        interface_priority: list[PromptMode] | None = None,
        interface_avoid: set[PromptMode] | None = None,
        vault_path: str | Path | None = None,
        key_path: str | Path | None = None,
        overwrite: bool = False,
        forget: bool = False,
        hide: bool = True # expect hide to be True always but allow user to set to false
        #force_prompt: bool|None = None
        )-> SecretData:

        if vault_path is None:
            vault_path = self.secret_path

        if key_path is None:
            key_path = self.key_path

        if interface_priority is None:
            interface_priority = self.interface_priority

        if interface_avoid is None:
            interface_avoid = self.interface_avoid

        #if force_prompt is None:
        #    force_prompt=self.force_prompt
            
        try:
            # Lazy Import dworshak_secret here to mitigate top-level crashes
            import cryptography
            from dworshak_secret import DworshakSecret
            secret_mgr = DworshakSecret(db_path = vault_path, key_path=key_path)

        except:
            # Trigger the "Lifeboat" redirection error
            from pyhabitat import safe_notify
            from .messages import notify_missing_function_redirect, MSG_CRYPTO_EXTRA
            # We pass a specific context so the user knows why it failed
            full_msg = notify_missing_function_redirect("Obtain.secret()") + MSG_CRYPTO_EXTRA
            safe_notify(full_msg)
            raise SystemExit(1)
        
        # Similar logic for secrets, but using dworshak-secret
        value = secret_mgr.get(service = service, item=item)
        if value is not None and not overwrite: # and not force_prompt:
            return SecretData(value = value, is_new = False)
        
        new_value = self.prompt.ask(
            message=message or f"Please input SECRET value\n(service = {service}, item = {item})",
            hide_input=hide,
            suggestion = suggestion,# or value,
            default = default,
            interface_priority = interface_priority,
            interface_avoid = interface_avoid
        )
        
        if new_value is None:
            # User cancelled (KeyboardInterrupt)
            return SecretData(value=None, is_new=None)
        
        if not forget:
            secret_mgr.set(service = service, item=item, value = new_value, overwrite=overwrite)
        return SecretData(value = new_value, is_new = True)
    
    def env(
        self, 
        key: str, 
        message: str | None = None,
        suggestion: str | None = None,
        default: Any | None = None,
        interface_priority: list[PromptMode] | None = None,
        interface_avoid: set[PromptMode] | None = None,
        path: str | Path | None = None,
        overwrite: bool = False,
        forget: bool = False
        #force_prompt: bool|None = None
    ) -> EnvData:
        """
        Checks key from os.environ or .env file, using the dworshak-env library. 
        Prompts user if not found or overwrite is True.
        """
        if path is None:
            path = self.env_path # Defaults to None, DworshakEnv handles Path(".env")

        if interface_priority is None:
            interface_priority = self.interface_priority

        if interface_avoid is None:
            interface_avoid = self.interface_avoid

        #if force_prompt is None:
        #    force_prompt=self.force_prompt
            
        env_mgr = DworshakEnv(path=path)
        value = env_mgr.get(key)

        # Logic: If it exists and we aren't forcing a refresh, return it.
        if value is not None and not overwrite: # and not force_prompt:
            return EnvData(value=value, is_new=False)

        # If missing or overwriting, we use the multiplexer
        new_value = self.prompt.ask(
            message=message or f"Please input ENV value\n(key = {key})",
            suggestion = suggestion or value,
            default = default,
            interface_priority = interface_priority,
            interface_avoid = interface_avoid, 
            hide_input=False
        )

        # Persistence logic: Save to .env file if not forgotten
        if new_value is None:
            return EnvData(value=None, is_new=None)

        if not forget:
            env_mgr.set(key, new_value, overwrite=overwrite)

        return EnvData(value=new_value, is_new=True)

obtain = Obtain() # the default settings
