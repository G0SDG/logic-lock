#!/usr/bin/env python3
"""
Move backup and temporary files out of the project root into a timestamped folder.

This script is conservative: it moves files and folders it considers clutter
instead of deleting them so you can review the results.
"""
import os
import shutil
import fnmatch
from datetime import datetime


ROOT = os.getcwd()

PATTERNS = [
    "*.bak",
    "*.tmp",
    "*.old",
    "*.log",
    "*~",
    "*.pyc",
    ".DS_Store",
    "Thumbs.db",
]

DIR_NAMES_TO_MOVE = {"bak", "backups"}


def is_ignored_dir(name):
    # keep common venv/.git/__pycache__ out of processing
    return name in {"venv", ".git", "__pycache__", "removed_backups"}


def main():
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest_root = os.path.join(ROOT, f"removed_backups_{ts}")
    os.makedirs(dest_root, exist_ok=True)

    moved_items = []

    for current_root, dirs, files in os.walk(ROOT):
        # skip the destination folder if it's inside the workspace
        if os.path.commonpath([os.path.abspath(current_root), os.path.abspath(dest_root)]) == os.path.abspath(dest_root):
            continue

        # skip hidden/system or virtual env dirs
        dirs[:] = [d for d in dirs if not is_ignored_dir(d) and not d.startswith(".")]

        # Move matching directories (e.g., any folder named 'bak' or 'backups')
        for d in list(dirs):
            if d.lower() in DIR_NAMES_TO_MOVE:
                src_dir = os.path.join(current_root, d)
                rel = os.path.relpath(src_dir, ROOT)
                target_dir = os.path.join(dest_root, rel)
                os.makedirs(os.path.dirname(target_dir), exist_ok=True)
                try:
                    shutil.move(src_dir, target_dir)
                    moved_items.append((src_dir, target_dir))
                except Exception as e:
                    print(f"Failed to move directory {src_dir}: {e}")
                # remove from dirs so os.walk won't descend into it
                dirs.remove(d)

        # Move files matching patterns
        for f in files:
            fp = os.path.join(current_root, f)
            # skip the script itself if run from repo
            if os.path.abspath(fp) == os.path.abspath(__file__):
                continue

            lower = f.lower()
            matched = any(fnmatch.fnmatch(lower, p.lower()) for p in PATTERNS)
            if matched:
                rel_dir = os.path.relpath(current_root, ROOT)
                target_dir = os.path.join(dest_root, rel_dir)
                os.makedirs(target_dir, exist_ok=True)
                try:
                    shutil.move(fp, os.path.join(target_dir, f))
                    moved_items.append((fp, os.path.join(target_dir, f)))
                except Exception as e:
                    print(f"Failed to move file {fp}: {e}")

    print(f"Moved {len(moved_items)} items to: {dest_root}")
    if moved_items:
        for src, dst in moved_items:
            print(f"  {src} -> {dst}")


if __name__ == "__main__":
    main()
