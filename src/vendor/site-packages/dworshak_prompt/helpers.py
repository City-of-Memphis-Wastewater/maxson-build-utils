# src/dworshak_prompt/helpers.py
from __future__ import annotations
import re
from typing import List, Set
from enum import Enum
import logging
logger=logging.getLogger(__name__)

SHOULD_ALLOW_HIDDEN_CLI_SUGGESTIONS = False

class PromptMode(Enum):
    #CONSOLE = "console"
    CLI = "cli"
    GUI = "gui"
    WEB = "web"

class InterruptBehavior(Enum):
    EXIT = "exit"
    RETURN_DEFAULT = "use_default"
    RETURN_NONE = "return_none"
    RAISE = "raise"

def _map_alias(item: str) -> str:
    # Map "CLI" to "CONSOLE" if the user types it
    if item.upper() == "CLI":
        return "CONSOLE"
    return item.upper()

def resolve_str_to_set(instance: str | Set[PromptMode] | None) -> Set[PromptMode]:
    if not instance:
        return set()
    if isinstance(instance, set):
        return instance
    if isinstance(instance, str):
        # Split on commas, spaces, or +; filter empties
        items = re.split(r'[,\s+]+', instance)
        items = [i.strip() for i in items if i.strip()]
        try:
            return {PromptMode[_map_alias(item)] for item in items}  # Enum keys are uppercase, e.g., "gui" -> GUI
        except KeyError as e:
            raise ValueError(f"Invalid PromptMode: {e}")
    raise ValueError(f"Invalid type for set: {type(instance)}")

def resolve_str_to_list(instance: str | List[PromptMode] | None) -> List[PromptMode]:
    if not instance:
        return []
    if isinstance(instance, list):
        return instance
    if isinstance(instance, str):
        # Split on commas, spaces, or +; filter empties
        items = re.split(r'[,\s+]+', instance)
        items = [i.strip() for i in items if i.strip()]
        try:
            return [PromptMode[item.upper()] for item in items]
        except KeyError as e:
            raise ValueError(f"Invalid PromptMode: {e}")
    raise ValueError(f"Invalid type for list: {type(instance)}")

