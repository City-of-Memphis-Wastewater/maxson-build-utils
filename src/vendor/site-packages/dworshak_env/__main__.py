# src/dworshak_env/__main__.py
"""
Entry point for the dworshak-env Rich/Typer CLI.
"""
TYPERSUCCESS=None
try:
    import typer
    TYPERSUCCESS=True
except (ImportError, ModuleNotFoundError):
    TYPERSUCCESS=False

if TYPERSUCCESS:
    # Attempt to use the feature-rich CLI
    from .cli import app
    def run():
        app()
else:
    import sys
    def run():
        print(
            "Please install this package with the 'typer' extra to utilize the CLI.",
            file=sys.stderr
        )
        sys.exit(1)
if __name__ == "__main__":
    run()


