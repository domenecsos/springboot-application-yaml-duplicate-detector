#!/usr/bin/env python3
"""
spring_yaml_sanity.py

Walks a directory tree and, for each folder containing a base application.yaml,
compares it with any application-*.yaml/yml files in the same folder.

For every key (flattened with dot-paths like `server.port` or `http.routes[0].path`)
that has the same value in both the base and the profile-specific file, an error
line is printed.

Notes:
- Supports multi-document YAML (---). Later docs override earlier ones.
- Only compares scalar leaf values (str, int, float, bool, None).
- Handles both .yaml and .yml extensions.
- Requires PyYAML: `pip install pyyaml`.
"""

import argparse
import os
from pathlib import Path
from typing import Any, Dict, Iterable, Tuple, Union

try:
    import yaml  # PyYAML
except ImportError as e:
    print("ERROR: PyYAML is required. Install with: pip install pyyaml")
    raise

Scalar = Union[str, int, float, bool, None]
YAML = Dict[str, Any]


def is_scalar(v: Any) -> bool:
    return isinstance(v, (str, int, float, bool)) or v is None


def deep_merge(a: YAML, b: YAML) -> YAML:
    """
    Merge dict b into dict a (recursively), returning a new dict.
    Values in b override values in a.
    """
    out = dict(a)  # shallow copy
    for k, v in b.items():
        if k in out and isinstance(out[k], dict) and isinstance(v, dict):
            out[k] = deep_merge(out[k], v)
        else:
            out[k] = v
    return out


def load_yaml_merged(path: Path) -> YAML:
    """
    Load YAML file. If it contains multiple documents, merge them in order
    (later documents override earlier ones).
    """
    with path.open("r", encoding="utf-8") as f:
        docs = list(yaml.safe_load_all(f))
    merged: YAML = {}
    for d in docs:
        if d is None:
            continue
        if not isinstance(d, dict):
            # Non-mapping root; wrap it for uniform handling
            d = {"_": d}
        merged = deep_merge(merged, d)
    return merged


def flatten(data: Any, prefix: str = "") -> Dict[str, Scalar]:
    """
    Flatten a nested structure (dicts/lists) into dot-path keys.
    Only leaf scalar values are included.

    Examples:
      {"server": {"port": 8080}} -> {"server.port": 8080}
      {"http": {"routes": [{"path": "/a"}, {"path": "/b"}]}}
        -> {"http.routes[0].path": "/a", "http.routes[1].path": "/b"}
    """
    flat: Dict[str, Scalar] = {}

    def _walk(node: Any, pfx: str) -> None:
        if is_scalar(node):
            flat[pfx if pfx else ""] = node
            return
        if isinstance(node, dict):
            for k, v in node.items():
                key = f"{pfx}.{k}" if pfx else str(k)
                _walk(v, key)
        elif isinstance(node, list):
            for i, v in enumerate(node):
                key = f"{pfx}[{i}]" if pfx else f"[{i}]"
                _walk(v, key)
        else:
            # Skip non-scalar leaves like sets, tuples, etc.
            pass

    _walk(data, prefix)
    # Remove empty-key entries (possible if root itself is scalar)
    return {k: v for k, v in flat.items() if k}


def find_profile_files(folder: Path) -> Iterable[Path]:
    for ext in (".yaml", ".yml"):
        yield from folder.glob(f"application-*-*{ext}")  # e.g. application-dev-us.yaml
        yield from folder.glob(f"application-*{ext}")   # e.g. application-dev.yaml


def compare_and_report(base_path: Path, profile_path: Path) -> int:
    """
    Compare base application.yaml with a profile-specific application-*.yaml.
    Print an error for each key with the same scalar value.
    Returns the number of duplicate keys found.
    """
    try:
        base_data = load_yaml_merged(base_path)
    except Exception as e:
        print(f"ERROR: Failed to load base YAML '{base_path}': {e}")
        return 0

    try:
        prof_data = load_yaml_merged(profile_path)
    except Exception as e:
        print(f"ERROR: Failed to load profile YAML '{profile_path}': {e}")
        return 0

    base_flat = flatten(base_data)
    prof_flat = flatten(prof_data)

    duplicates = []
    for key, prof_val in prof_flat.items():
        if key in base_flat and base_flat[key] == prof_val:
            duplicates.append((key, prof_val))

    duplicates.sort(key=lambda kv: kv[0])

    count = 0
    for key, val in duplicates:
        # Render value compactly
        shown = repr(val)
        if len(shown) > 80:
            shown = shown[:77] + "..."
        print(f"ERROR: {profile_path}: key '{key}' duplicates base value {shown}")
        count += 1

    return count


def process_folder(folder: Path) -> int:
    """
    If `folder` contains an application.yaml/.yml, compare it with any
    application-*.yaml/.yml in the same folder. Returns total duplicate count.
    """
    base_path = None
    for candidate in (folder / "application.yaml", folder / "application.yml"):
        if candidate.exists():
            base_path = candidate
            break

    if not base_path:
        return 0

    # Log the path to the base file (including folder name)
    print(f"\nFolder: {folder}")
    print(f"Base:   {base_path}")

    total = 0
    profiles = sorted(set(find_profile_files(folder)))
    
    # Filter out the base itself if pattern catches it
    profiles = [p for p in profiles if p.name not in ("application.yaml", "application.yml")]

    if not profiles:
        print("No profile-specific files found.")
        return 0

    for prof in profiles:
        total += compare_and_report(base_path, prof)

    if total == 0:
        print("No duplicate key values found.")
    return total


def walk_and_check(root: Path) -> int:
    """
    Recursively walk from root, processing each folder that has a base application.yaml/yml.
    Returns total number of duplicate findings.
    """
    total = 0
    for dirpath, dirnames, filenames in os.walk(root):
        folder = Path(dirpath)
        if "application.yaml" in filenames or "application.yml" in filenames:
            total += process_folder(folder)
    return total


def main():
    ap = argparse.ArgumentParser(
        description="Find duplicated key values between base application.yaml and profile-specific application-*.yaml files."
    )
    ap.add_argument(
        "root",
        nargs="?",
        default=".",
        help="Root folder to scan (default: current directory)"
    )
    args = ap.parse_args()
    root = Path(args.root).resolve()

    if not root.exists() or not root.is_dir():
        print(f"ERROR: '{root}' is not a directory.")
        raise SystemExit(2)

    total = walk_and_check(root)
    # Exit with non-zero if duplicates found, useful in CI
    if total > 0:
        print(f"\nCompleted with {total} duplicated key value(s) found.")
        raise SystemExit(1)
    else:
        print("\nCompleted with no duplicated key values found.")
        raise SystemExit(0)


if __name__ == "__main__":
    main()
