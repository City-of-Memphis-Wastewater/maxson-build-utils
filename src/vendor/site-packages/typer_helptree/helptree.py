#!/usr/bin/env python3 
# SPDX-License-Identifier: MIT
# src/typer_helptree/helpers.py
from __future__ import annotations
import click
from rich.tree import Tree
from typing import Dict, Any, List
from enum import Enum
import logging
#if not logging.getLogger().handlers:
#    logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
#logger.setLevel(logging.DEBUG)

def _get_param_data_(param: click.Parameter) -> Dict[str, Any]:
    """
    Extracts raw metadata from a Click parameter for JSON export.
    Uses original logic to handle default values and sentinel values.
    """
    return {
        "name": param.name,
        "opts": getattr(param, 'opts', []),
        "help": getattr(param, 'help', ""),
        "default": str(param.default) if param.default not in (None, click.core.UNSET) else None
    }

def _get_param_data(param: click.Parameter) -> Dict[str, Any]:
    """Extracts detailed metadata from a Click parameter."""

    # Handle the default value safely
    default_val = param.default
    if isinstance(default_val, Enum):
        default_val = default_val.value
    elif default_val is not None and not isinstance(default_val, (str, int, float, bool, list, dict)):
        default_val = str(default_val)

    return {
        "name": param.name,
        "opts": param.opts,
        "secondary_opts": param.secondary_opts,
        "type": str(param.type),
        "required": param.required,
        "default": default_val,    # Now safe for Enums/Objects
        "help": param.help or "",
        "hidden": getattr(param, "hidden", False),
        "is_flag": getattr(param, "is_flag", False),
        "envvar": param.envvar,
    }

def _format_param_label(param: click.Parameter) -> str:
    """
    Formats a Click parameter into a colorized string for the Rich tree.
    Preserves the 'human_readable_name' for Arguments and '-' check for Options.
    """
    is_option = hasattr(param, 'opts') and param.opts and param.opts[0].startswith('-')
    
    if is_option:
        flag_names = " / ".join(param.opts)
        default_value = getattr(param, 'default', None)
        
        default_str = ""
        if default_value not in (None, click.core.UNSET):
            default_str = f" [dim](default: {default_value})[/dim]"
            
        return f"[green]{flag_names}[/green]: [dim]{param.help or ''}[/dim]{default_str}"
    
    # Handling Positional Arguments
    arg_name = param.human_readable_name.upper()
    return f"[magenta]ARG: {arg_name}[/magenta]: [dim]{param.help or ''}[/dim]"

def _add_parameters_to_node(click_command: click.Command, tree_node: Tree) -> None:
    """Extracts parameters and appends them to the Rich tree node."""
    if not hasattr(click_command, 'params') or not click_command.params:
        return

    visible_params = [
        p for p in click_command.params 
        if not (hasattr(p, 'opts') and any(opt in ("-h", "--help") for opt in p.opts))
    ]

    if visible_params:
        params_branch = tree_node.add("[yellow]Parameters[/yellow]")
        for param in visible_params:
            params_branch.add(_format_param_label(param))

def build_help_tree(click_command: click.Command, tree_node: Tree, ctx: click.Context) -> None:
    """Builds the Rich Tree structure recursively."""
    _add_parameters_to_node(click_command, tree_node)

    logger.debug(
        "ENTER build_help_tree: command=%s type=%s ctx=%s",
        click_command.name,
        type(click_command).__name__,
        hex(id(ctx)),
    )

    logger.debug(
        "class=%r is_group()=%s mro=%s",
        type(click_command),
        is_group(click_command),
        type(click_command).__mro__,
    )

    if is_group(click_command):
        command_names = []
        group_names = []


        #local_ctx = click.Context(click_command)
        local_ctx = make_context(click_command,ctx)
        
        logger.debug(
            "helptree: %s commands=%s",
            click_command.name,
            click_command.list_commands(local_ctx),
        )

        for cmd_name in click_command.list_commands(local_ctx):
            logger.debug(
                "Resolving child: parent=%s child=%s",
                click_command.name,
                cmd_name,
            )

            cmd = click_command.get_command(local_ctx, cmd_name)
     
            # ---
            #if not cmd or cmd.name == "helptree":
            #    continue
            
            if cmd is None:
                logger.warning(
                    "helptree: get_command(%s) returned None under %s",
                    cmd_name,
                    click_command.name,
                )
                continue

            if cmd.name == "helptree":
                logger.debug(
                    "helptree: skipping internal helptree command"
                )
                continue
            # ---
            if is_group(cmd):
                group_names.append(cmd_name)
            else:
                command_names.append(cmd_name)

        # Sort for stability
        command_names.sort()
        group_names.sort()

        # Render commands first
        for cmd_name in command_names:
            cmd = click_command.get_command(local_ctx, cmd_name)
            raw_help = cmd.help or ""
            full_description = raw_help.splitlines()[0].strip() if raw_help else "No description available."

            sub_node = tree_node.add(
                f"[bold white]{cmd_name}[/bold white] - [dim]{full_description}[/dim]"
            )
            #md_ctx = click.Context(cmd)
            cmd_ctx = make_context(cmd, local_ctx)
    
            build_help_tree(cmd, sub_node, cmd_ctx)

        # Render sub-apps second
        for cmd_name in group_names:
            cmd = click_command.get_command(local_ctx, cmd_name)
            raw_help = cmd.help or ""
            full_description = raw_help.splitlines()[0].strip() if raw_help else "No description available."

            sub_node = tree_node.add(
                f"[bold cyan]{cmd_name}[/bold cyan] [dim](app)[/dim] - [dim]{full_description}[/dim]"
            )
            #cmd_ctx = click.Context(cmd)
            cmd_ctx = make_context(cmd, local_ctx)

            build_help_tree(cmd, sub_node, cmd_ctx)

        logger.debug(
            "Contexts: parent_ctx=%s local_ctx=%s",
            hex(id(ctx)),
            hex(id(local_ctx)),
        )
    logger.debug(
        "EXIT build_help_tree: command=%s",
        click_command.name,
    )

def build_help_data(click_command: click.Command, ctx: click.Context, version: str = None) -> Dict[str, Any]:
    """Recursively builds a dictionary for JSON export, utilizing _get_param_data."""

    is_group_cmd = is_group(click_command)

    node_data = {
        "name": click_command.name or "app",
        "help": (
            getattr(click_command, "help", None)
            or click_command.get_short_help_str()
            or ""
        ),
        "kind": "app" if is_group_cmd else "command",
        "is_group": is_group_cmd,          # kept for compatibility
        "parameters": [],
        "subcommands": [],
    }

    # Only add version to the root node
    if version:
        node_data["version"] = version

    if hasattr(click_command, 'params'):
        for param in click_command.params:
            if hasattr(param, 'opts') and any(opt in ("-h", "--help") for opt in param.opts):
                continue
            # Skip internal helptree flags # MAINTENANCE BURDEN
            if param.name in ["export_json", "export_txt"]:
                continue
            # Logic restored: uses the helper function
            node_data["parameters"].append(_get_param_data(param))

    if is_group(click_command):
        command_names: list[str] = []
        group_names: list[str] = []

        command_names_raw = click_command.list_commands(ctx)

        logger.debug(
            "helptree: command=%s list_commands=%s",
            click_command.name,
            command_names_raw,
        )
        for cmd_name in command_names_raw:
            

            cmd = click_command.get_command(ctx, cmd_name)
            # ---
            #if not cmd or cmd.name == "helptree":
            #    continue
            
            if cmd is None:
                logger.warning(
                    "helptree: get_command(%s) returned None under %s",
                    cmd_name,
                    click_command.name,
                )
                continue

            if cmd.name == "helptree":
                logger.debug(
                    "helptree: skipping internal helptree command"
                )
                continue
            # ---
            if is_group(cmd):
                group_names.append(cmd_name)
            else:
                command_names.append(cmd_name)

        # Stable ordering
        command_names.sort()
        group_names.sort()

        # Commands first
        for cmd_name in command_names:
            cmd = click_command.get_command(ctx, cmd_name)
            node_data["subcommands"].append(
                build_help_data(cmd, ctx)
            )

        # Sub-apps second
        for cmd_name in group_names:
            cmd = click_command.get_command(ctx, cmd_name)
            node_data["subcommands"].append(
                build_help_data(cmd, ctx)
            )

    return node_data

def is_group(cmd)->bool:
    return callable(getattr(cmd, "list_commands", None))

def make_context(cmd,parent=None):
    return type(cmd).context_class(cmd, parent=parent)

