# src/dworshak_env/__init__.py
__all__ = [
    "DowrshakEnv",
    "dworshak_env"
    ]

def __getattr__(name):
    if name == "DworshakEnv":
        from .core import DworshakEnv
        return DworshakEnv

    if name == "dworshak_env":
        from .core import dworshak_env
        return dworshak_env

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

def __dir__():
    return sorted(__all__ + [
        "__all__", "__builtins__", "__cached__", "__doc__", "__file__",
        "__getattr__", "__loader__", "__name__", "__package__", "__path__", "__spec__"
    ])

