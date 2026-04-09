"""
=============================================================
  Smart File Organizer for Windows
  Author: Built for Bishow
  
  Automatically organizes messy folders (Downloads, Desktop,
  Documents, or any folder you point it at) into clean,
  categorized subfolders.
  
  Features:
    - Sorts files by type into intuitive categories
    - Handles duplicates (appends _1, _2, etc.)
    - Dry-run mode to preview changes before committing
    - Undo log so you can reverse everything
    - Skips system/hidden files
    - Recursive option for nested chaos
    - Clean summary report at the end
  
  Usage:
    python organize_files.py                  # organizes Downloads
    python organize_files.py --folder Desktop # organizes Desktop
    python organize_files.py --path "C:/Users/You/SomeFolder"
    python organize_files.py --dry-run        # preview only
    python organize_files.py --undo           # reverse last run
    python organize_files.py --recursive      # include subfolders
=============================================================
"""

import os
import sys
import shutil
import json
import argparse
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# ──────────────────────────────────────────────
# FILE CATEGORIES — edit these to your liking!
# ──────────────────────────────────────────────
CATEGORIES = {
    "Images": {
        ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".webp",
        ".ico", ".tiff", ".tif", ".heic", ".heif", ".raw", ".cr2",
        ".nef", ".psd", ".ai", ".eps"
    },
    "Documents": {
        ".pdf", ".doc", ".docx", ".txt", ".rtf", ".odt", ".tex",
        ".md", ".log", ".pages", ".wpd", ".wps"
    },
    "Spreadsheets": {
        ".xls", ".xlsx", ".csv", ".tsv", ".ods", ".xlsm", ".xlsb"
    },
    "Presentations": {
        ".ppt", ".pptx", ".key", ".odp"
    },
    "Videos": {
        ".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv", ".webm",
        ".m4v", ".mpg", ".mpeg", ".3gp", ".vob", ".ts"
    },
    "Audio": {
        ".mp3", ".wav", ".flac", ".aac", ".ogg", ".wma", ".m4a",
        ".opus", ".aiff", ".alac", ".mid", ".midi"
    },
    "Archives": {
        ".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz",
        ".iso", ".dmg", ".cab", ".tgz"
    },
    "Code": {
        ".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".c", ".cpp",
        ".h", ".hpp", ".cs", ".go", ".rs", ".rb", ".php", ".swift",
        ".kt", ".scala", ".r", ".m", ".sql", ".sh", ".bat", ".ps1",
        ".html", ".css", ".scss", ".sass", ".less", ".vue", ".svelte",
        ".json", ".xml", ".yaml", ".yml", ".toml", ".ini", ".cfg",
        ".ipynb", ".rmd"
    },
    "Executables & Installers": {
        ".exe", ".msi", ".apk", ".app", ".deb", ".rpm", ".bin",
        ".run", ".appimage", ".snap"
    },
    "Fonts": {
        ".ttf", ".otf", ".woff", ".woff2", ".eot"
    },
    "3D & CAD": {
        ".stl", ".obj", ".fbx", ".blend", ".dwg", ".dxf", ".step",
        ".stp", ".iges", ".3ds"
    },
    "Data": {
        ".db", ".sqlite", ".sqlite3", ".mdb", ".accdb", ".parquet",
        ".feather", ".hdf5", ".h5", ".sav", ".dta", ".rdata", ".rds"
    },
    "eBooks": {
        ".epub", ".mobi", ".azw", ".azw3", ".fb2", ".djvu", ".cbr", ".cbz"
    },
}

# Files/folders to never touch
SKIP_FILES = {
    "desktop.ini", "thumbs.db", ".ds_store", "ntuser.dat",
    "organize_files.py", "undo_log.json"
}

SKIP_FOLDERS = {
    "$recycle.bin", "system volume information", ".git",
    "node_modules", "__pycache__", ".vscode", ".idea"
}


def get_category(extension: str) -> str:
    """Determine the category for a file based on its extension."""
    ext = extension.lower()
    for category, extensions in CATEGORIES.items():
        if ext in extensions:
            return category
    return "Other"


def get_target_path(dest_folder: Path, filename: str) -> Path:
    """Get a unique target path, handling duplicates by appending _1, _2, etc."""
    target = dest_folder / filename
    if not target.exists():
        return target

    stem = Path(filename).stem
    suffix = Path(filename).suffix
    counter = 1
    while True:
        new_name = f"{stem}_{counter}{suffix}"
        target = dest_folder / new_name
        if not target.exists():
            return target
        counter += 1


def should_skip(path: Path) -> bool:
    """Check if a file or folder should be skipped."""
    name = path.name.lower()
    if path.is_file() and name in SKIP_FILES:
        return True
    if path.is_dir() and name in SKIP_FOLDERS:
        return True
    # Skip hidden files on Windows (starting with .)
    if name.startswith("."):
        return True
    return False


def collect_files(source: Path, recursive: bool = False) -> list:
    """Collect all files to be organized."""
    files = []
    if recursive:
        for root, dirs, filenames in os.walk(source):
            # Filter out skip folders
            dirs[:] = [d for d in dirs if d.lower() not in SKIP_FOLDERS
                       and not d.startswith(".")]
            root_path = Path(root)
            # Don't collect files from category folders we created
            if root_path != source and root_path.parent == source:
                if root_path.name in CATEGORIES or root_path.name == "Other":
                    continue
            for f in filenames:
                fp = root_path / f
                if not should_skip(fp):
                    files.append(fp)
    else:
        for item in source.iterdir():
            if item.is_file() and not should_skip(item):
                files.append(item)
    return files


def organize(source: Path, dry_run: bool = False, recursive: bool = False):
    """Main organization logic."""
    if not source.exists():
        print(f"\n  ERROR: Folder not found: {source}")
        sys.exit(1)

    print(f"\n{'=' * 60}")
    print(f"  Smart File Organizer")
    print(f"{'=' * 60}")
    print(f"  Source:    {source}")
    print(f"  Mode:      {'DRY RUN (no files moved)' if dry_run else 'LIVE'}")
    print(f"  Recursive: {'Yes' if recursive else 'No'}")
    print(f"{'=' * 60}\n")

    files = collect_files(source, recursive)

    if not files:
        print("  No files to organize. Folder is already clean!")
        return

    # Track what we do
    moves = []
    stats = defaultdict(int)
    undo_log = []

    for filepath in files:
        ext = filepath.suffix
        category = get_category(ext)
        dest_folder = source / category

        if not dry_run:
            dest_folder.mkdir(exist_ok=True)

        target = get_target_path(dest_folder, filepath.name)

        if dry_run:
            moves.append((filepath, target, category))
        else:
            try:
                shutil.move(str(filepath), str(target))
                moves.append((filepath, target, category))
                undo_log.append({
                    "from": str(target),
                    "to": str(filepath)
                })
            except Exception as e:
                print(f"  WARNING: Could not move {filepath.name}: {e}")
                continue

        stats[category] += 1

    # Save undo log
    if not dry_run and undo_log:
        log_path = source / "undo_log.json"
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "source": str(source),
            "moves": undo_log
        }
        with open(log_path, "w") as f:
            json.dump(log_data, f, indent=2)

    # ── Print Summary ──
    print(f"  {'PLANNED' if dry_run else 'COMPLETED'} MOVES:")
    print(f"  {'-' * 50}")

    for category in sorted(stats.keys()):
        count = stats[category]
        bar = "█" * min(count, 30)
        print(f"  {category:<25} {count:>4} files  {bar}")

    print(f"  {'-' * 50}")
    print(f"  {'Total':<25} {sum(stats.values()):>4} files")
    print()

    if dry_run:
        print("  This was a DRY RUN. No files were moved.")
        print("  Run without --dry-run to apply changes.\n")

        # Show first 20 planned moves
        print(f"  Sample moves (showing up to 20):")
        print(f"  {'-' * 50}")
        for src, dst, cat in moves[:20]:
            print(f"  {src.name}")
            print(f"    -> {cat}/{dst.name}\n")
        if len(moves) > 20:
            print(f"  ... and {len(moves) - 20} more.\n")
    else:
        print(f"  All done! Undo log saved to: undo_log.json")
        print(f"  Run with --undo to reverse all changes.\n")

    # Clean up empty directories left behind (only in recursive mode)
    if not dry_run and recursive:
        for root, dirs, filenames in os.walk(source, topdown=False):
            root_path = Path(root)
            if root_path == source:
                continue
            # Don't remove our category folders
            if root_path.parent == source and root_path.name in list(CATEGORIES.keys()) + ["Other"]:
                continue
            try:
                if not any(root_path.iterdir()):
                    root_path.rmdir()
                    print(f"  Removed empty folder: {root_path.name}")
            except Exception:
                pass


def undo(source: Path):
    """Reverse the last organization run."""
    log_path = source / "undo_log.json"
    if not log_path.exists():
        print("\n  No undo log found. Nothing to reverse.\n")
        return

    with open(log_path, "r") as f:
        log_data = json.load(f)

    moves = log_data["moves"]
    print(f"\n  Undoing {len(moves)} moves from {log_data['timestamp']}...\n")

    success = 0
    for move in moves:
        src = Path(move["from"])
        dst = Path(move["to"])
        try:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(dst))
            success += 1
        except Exception as e:
            print(f"  WARNING: Could not undo {src.name}: {e}")

    # Remove empty category folders
    for category in list(CATEGORIES.keys()) + ["Other"]:
        cat_folder = source / category
        if cat_folder.exists():
            try:
                if not any(cat_folder.iterdir()):
                    cat_folder.rmdir()
            except Exception:
                pass

    log_path.unlink(missing_ok=True)
    print(f"  Restored {success}/{len(moves)} files to original locations.\n")


def resolve_folder(args) -> Path:
    """Resolve the target folder from arguments."""
    if args.path:
        return Path(args.path).expanduser().resolve()

    # Default well-known folders on Windows
    home = Path.home()
    folder_map = {
        "downloads": home / "Downloads",
        "desktop": home / "Desktop",
        "documents": home / "Documents",
        "pictures": home / "Pictures",
        "music": home / "Music",
        "videos": home / "Videos",
    }

    folder_name = (args.folder or "downloads").lower()
    if folder_name in folder_map:
        return folder_map[folder_name]
    else:
        print(f"\n  Unknown folder shortcut: '{folder_name}'")
        print(f"  Available: {', '.join(folder_map.keys())}")
        print(f"  Or use --path to specify a custom path.\n")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Smart File Organizer - Sort your messy folders instantly.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python organize_files.py                        # Organize Downloads
  python organize_files.py --folder Desktop       # Organize Desktop
  python organize_files.py --path "D:\\Projects"   # Organize custom folder
  python organize_files.py --dry-run              # Preview changes
  python organize_files.py --recursive            # Include subfolders
  python organize_files.py --undo                 # Reverse last run
  python organize_files.py --folder Desktop --undo
        """
    )
    parser.add_argument("--folder", type=str, default="downloads",
                        help="Shortcut: downloads, desktop, documents, pictures, music, videos")
    parser.add_argument("--path", type=str, default=None,
                        help="Full path to any folder you want organized")
    parser.add_argument("--dry-run", action="store_true",
                        help="Preview what would happen without moving files")
    parser.add_argument("--recursive", action="store_true",
                        help="Also organize files in subfolders")
    parser.add_argument("--undo", action="store_true",
                        help="Reverse the last organization run")

    args = parser.parse_args()
    source = resolve_folder(args)

    if args.undo:
        undo(source)
    else:
        organize(source, dry_run=args.dry_run, recursive=args.recursive)


if __name__ == "__main__":
    main()
