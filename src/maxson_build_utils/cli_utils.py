# src/maxson_build_utils/cli_utils.py

import typer
import click
import importlib

def get_cli_commands(entry_point: str) -> set[str]:
  """Resolves the entry point string and extracts top-level command names."""
  try:
    module_path, app_name = entry_point.split(":")
    module = importlib.import_module(module_path)
    app = getattr(module, app_name)

    if isinstance(app, typer.Typer):
      click_obj = typer.main.get_command(app)
      if isinstance(click_obj, click.Group):
        ctx = click.Context(click_obj)
        return set(click_obj.list_commands(ctx))
    elif isinstance(app, click.Group):
      ctx = click.Context(app)
      return set(app.list_commands(ctx))
  except Exception as e:
    print(f"Note: Could not inspect CLI commands for '{entry_point}': {e}")

  return set()

