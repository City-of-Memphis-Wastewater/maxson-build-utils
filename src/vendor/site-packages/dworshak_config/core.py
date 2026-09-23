# src/dworshak_config/core.py
from pathlib import Path
import json
import shutil
import logging
from typing import Any, List
import os

logger = logging.getLogger(__name__)

_raw_heal_json = os.getenv("DWORSHAK_CONFIG_AUTO_HEAL_JSON", "false").lower()
AUTO_HEAL_JSON = _raw_heal_json in ("true", "1", "yes", "on")
DEFAULT_CONFIG_PATH = Path.home() / ".dworshak" / "config.json"

class DworshakConfig:
    def __init__(self, path: str | Path | None = None, auto_heal: bool = False):
        if path and str(path).endswith(".json"):
            self.path = Path(path)
        else:
            self.path = DEFAULT_CONFIG_PATH

        self.auto_heal = auto_heal or AUTO_HEAL_JSON

    def load(self) -> dict:
        """Loads the nested JSON config."""
        if not self.path.exists():
            return {}

        content = ""
        try:
            content = self.path.read_text(encoding="utf-8")
            data = json.loads(content)
            return data if isinstance(data, dict) else {}
        
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            if self.auto_heal and content:
                return self._attempt_repair(content, e)
            
            logger.warning(f"⚠️ Config file '{self.path}' is corrupted: {e}")
            return {}
        except Exception as e:
            # Catch OS/Permission errors separately
            logger.error(f"❌ Critical error reading '{self.path}': {e}")
            return {}


    def _save(self, config: dict):
        """Saves the nested JSON config."""
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.path, "w") as f:
                json.dump(config, f, indent=4)
        except Exception as e:
            logger.error(f"⚠️ Failed to save configuration to {self.path}: {e}")

    def get(self, service: str, item: str) -> str | None:
        """Pure I/O: Retrieve from JSON, return None if missing."""
        config = self.load()
        return config.get(service, {}).get(item)

    def set(self, service: str, item: str, value: Any, overwrite: bool = True):
        """Pure I/O: Store value in JSON."""
        config = self.load()

        if not overwrite and service in config and item in config[service]:
            logger.debug(
                f"Skipping set of {service}/{item} — already exists and overwrite=False"
            )
            return
        # config.setdefault(service, {})[item] = value
        if service not in config:
            config[service] = {}
        config[service][item] = value
        self._save(config)

    def remove(self, service: str, item: str) -> bool:
        """
        Remove a specific service/item entry if it exists.

        Returns:
            True if an entry was removed, False if it didn't exist.
        """
        config = self.load()
        if service not in config or item not in config[service]:
            return False

        del config[service][item]

        # Clean up empty service dicts (optional but nice)
        if not config[service]:
            del config[service]

        self._save(config)
        return True

    def list_configs(self) -> List[tuple[str, str]]:
        """
        Return a list of all (service, item) pairs that exist in the config.
        """
        config = self.load()
        result = []
        for service, items in config.items():
            if isinstance(items, dict):
                for item in items:
                    result.append((service, item))
        return result

    
    def _attempt_repair(self, content: str, original_error: Exception) -> dict:

        source = "Env Var" if AUTO_HEAL_JSON else "Arg"
        logger.info(f"Auto-repairing corrupted config (Trigger: {source})...")

        try:
            from json_repair import repair_json
            
            # 1. Create a safety backup before touching anything
            backup_path = self.path.with_suffix(".json.bak")
            shutil.copy(self.path, backup_path)
            
            # 2. Repair the string
            repaired_json_str = repair_json(content)
            data = json.loads(repaired_json_str)
            
            # 3. Save the repaired version back to disk
            self._save(data)
            logger.info(f"Successfully healed {self.path}. Original backed up to .bak")
            return data
            
        except ImportError:
            logger.error("json-repair not installed. Use 'pip install dworshak-config[repair]'")
            return {}
        except Exception as heal_e:
            logger.error(f"Self-healing failed: {heal_e}")
            return {}
