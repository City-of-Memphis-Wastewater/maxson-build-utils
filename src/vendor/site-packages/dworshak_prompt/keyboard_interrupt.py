# src/dworshak_prompt/keyboard_interrupt.py
class PromptCancelled(Exception):
    """User explicitly cancelled or interrupted the input."""
    pass