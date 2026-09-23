#!/usr/bin/env python3 
# SPDX-License-Identifier: MIT
# src/typer_helptree/dev.py

"""
Developer-facing CLI visibility. Great for screenshotting.

```bash
typer-helptree helptree
```

```python
import typer_helptree
subprocess.run("typer-helptree", "helptree")
```
"""
from __future__ import annotations
import typer
from typing import Optional, List
from pathlib import Path
from rich.tree import Tree 
from rich.panel import Panel
from rich.console import Console

from .helptree import build_help_tree
from .utils import updating_target_file_references

console_stderr = Console(stderr = True)

def add_typer_helptree(app, console, version: str = "unknown", hidden: bool =True):
    @app.command(name="helptree", hidden = hidden, help="Visualize your entire CLI, beautifully. Export to JSON and TXT.")
    def help_tree_command(
        ctx: typer.Context,
        version: str = version,
        export_json: bool = typer.Option(False, "--export-json", "-ej",help="Export to JSON."),
        export_txt: bool = typer.Option(False, "--export-txt", "-et", help="Export to TXT."),
        export_svg: bool = typer.Option(False, "--export-svg","-es", help="Export to SVG (Vector Image)."),
        output_dir: Optional[Path] = typer.Option(
            None, 
            "--output-dir", "-o",
            help="Specify a directory for exports. Defaults to ~/.typer_helptree"
        ),
        update_target: Optional[List[Path]] = typer.Option(
            None, 
            "--path-update", "-p",
            help="Idenfity file reference to the exported SVG image in the local asset file and bump the version to match the new export. Repeatable."
        )
    ):
        # Ensure we use ctx.parent.command to get the main app's root command
        root_command = ctx.parent.command 
        app_name = root_command.name or "app"
        
        app_tree = Tree(f"[bold blue]{app_name}[/bold blue] (v{version})", guide_style="cyan")
        
        # This now recurses through the root_command using your original logic
        build_help_tree(root_command, app_tree, ctx)
        
        # 2. Optional Exports
        
        if export_json:
            from typer_helptree.helptree import build_help_data
            from typer_helptree.io import export_help_json
            data = build_help_data(root_command, ctx, version=version)
            export_help_json(data, app_name, version, output_dir)

        if export_txt:
            from typer_helptree.io import export_help_txt
            # Capture the Rich tree as plain text using a dummy console
            capture_console = Console(width=200, force_terminal=False, color_system=None)
            with capture_console.capture() as capture:
                capture_console.print(app_tree)
            export_help_txt(capture.get(), app_name, version,output_dir)
            
        # Handle SVG Export (Requires a recording console)
        if export_svg:
            from .io import export_help_svg
            # Create a dedicated recording console to ensure clean output
            recording_console = Console(record=True, width=120)
            recording_console.print(app_tree)
            export_help_svg(recording_console, app_name, version, output_dir)
            
        if not(export_json or export_txt or export_svg):
            # ONLY print if no export flags are set
            console_stderr.print(Panel(app_tree, title=f"[bold]{app_name} CLI Help Tree[/bold]", expand=False))

        if update_target:
            if export_svg and output_dir:
                update_target_set = set(update_target)
                try:
                    targets_success = updating_target_file_references(
                        targets=update_target_set, 
                        app_name=app_name, 
                        version=version,
                        extension = "svg"
                    )
                    #console_stderr.print(f"Target files updated: {targets_success}")
                except Exception as e:
                    console_stderr.print(f"Target file update failed: {e}")
            else:
               # Clarify the expectation, though this is a maintenance risk. #maintenancerisk
               console_stderr.print("No targets updated; the `--output-dir` flag and the `--export-svg` flag are expected for this.") 
