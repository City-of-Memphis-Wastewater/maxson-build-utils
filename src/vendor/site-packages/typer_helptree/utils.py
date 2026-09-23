# src/typer_helptree/utils.py
from __future__ import annotations
import re
from pathlib import Path
from typing import Iterable, Optional, Set
import sys

def updating_target_file_references_(
    targets: Optional[Iterable[str]],
    app_name: str,
    version: str
) -> None:
    if not targets:
        return

    pattern_str = rf"({re.escape(app_name)}_v).*?(_helptree\.svg)"
    pattern = re.compile(pattern_str)

    # Use \g<1> to explicitly separate the group ID from the version digits
    replacement = rf"\g<1>{version}\g<2>"

    targets_success = set()
    
    for target in targets:
        path = Path(target)
        if not path.exists():
            continue

        content = path.read_text(encoding="utf-8")
        new_content, count = pattern.subn(replacement, content)

        if count > 0:
            path.write_text(new_content, encoding="utf-8")
            print(f"Updated {count} link(s) in {target} to v{version}", file=sys.stderr)

        targets_success.add(target)
        
    return targets_success

def updating_target_file_references(
    targets: Optional[Iterable[str]],
    app_name: str,
    version: str,
    extension: str = "svg"
) -> Set[str]:
    """
    Finds and replaces versioned image references in target files.
    Example: 'myapp_v0.1.0_helptree.svg' -> 'myapp_v0.2.0_helptree.svg'
    """
    if not targets:
        return set()

    # Ensure extension starts with a dot for the regex
    ext = extension if extension.startswith(".") else f".{extension}"
    
    # Pattern: (appname_v) [anything] (_helptree.ext)
    # Using \g<1> in replacement prevents ambiguity with version numbers.
    pattern_str = rf"({re.escape(app_name)}_v).*?(_helptree{re.escape(ext)})"
    pattern = re.compile(pattern_str)
    replacement = rf"\g<1>{version}\g<2>"

    targets_success = set()

    for target in targets:
        path = Path(target)
        if not path.exists():
            print(f"Warning: Target file not found: {target}", file=sys.stderr)
            continue

        content = path.read_text(encoding="utf-8")
        new_content, count = pattern.subn(replacement, content)

        if count > 0:
            path.write_text(new_content, encoding="utf-8")
            print(f"Updated {count} link(s) in {target} to v{version} ({extension})", file=sys.stderr)
            targets_success.add(target)
        else:
            print(f"No matches found in {target} for {app_name}_v...{ext}", file=sys.stderr)

    return targets_success
