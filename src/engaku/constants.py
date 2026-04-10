"""
engaku.constants
Framework-level built-in defaults.  These are the values used when no
user configuration is present.  Do not put user-configurable settings here —
those belong in .ai/engaku.json (loaded by utils.load_config).
"""
import os

# ── check-update built-in file-type blacklists ─────────────────────────────

# Directory name components that mark a subtree as non-trackable.
# Any path segment matching one of these means the file is ignored.
IGNORED_DIR_NAMES = frozenset({
    # Python
    "__pycache__", ".venv", "venv", ".eggs", ".pytest_cache",
    ".mypy_cache", ".ruff_cache", ".tox", "htmlcov",
    # JavaScript / TypeScript
    "node_modules", ".next", ".nuxt", ".turbo", ".parcel-cache",
    # Dart / Flutter
    ".dart_tool", ".pub-cache",
    # Rust
    "target",
    # General build outputs
    "dist", "build", ".cache",
    # VCS and engaku knowledge (not source)
    ".git", ".ai",
})

# Directory name suffixes — any segment ending with one of these is ignored.
IGNORED_DIR_SUFFIXES = (".egg-info",)

# Binary / auto-generated file extensions.
IGNORED_EXTENSIONS = frozenset({
    # Python bytecode
    ".pyc", ".pyo", ".pyd",
    # Compiled native
    ".so", ".dylib", ".dll", ".exe", ".o", ".a", ".rlib", ".rmeta",
    # Dart / Flutter compiled
    ".dill", ".snapshot",
    # Archives and packages
    ".whl", ".egg", ".zip", ".tar", ".gz", ".bz2", ".xz", ".7z", ".rar",
    # Images
    ".png", ".jpg", ".jpeg", ".gif", ".ico", ".webp", ".tiff", ".bmp",
    # Audio / video
    ".mp4", ".mp3", ".wav", ".ogg", ".flac", ".mov", ".avi",
    # Documents
    ".pdf",
    # Databases
    ".db", ".sqlite", ".sqlite3",
    # Source maps
    ".map",
})

# Exact filenames that are always non-trackable.
IGNORED_FILENAMES = frozenset({
    # Secrets
    ".env",
    # Lock files (all auto-generated)
    "package-lock.json", "yarn.lock", "pnpm-lock.yaml",
    "poetry.lock", "Pipfile.lock", "Cargo.lock",
    "pubspec.lock", "go.sum",
    # OS metadata
    ".DS_Store", "Thumbs.db", "desktop.ini",
    # Tool caches
    ".eslintcache", ".stylelintcache",
})

# ── timing ──────────────────────────────────────────────────────────────────

RECENT_SECONDS = 600  # 10 minutes

# ── shared file paths ───────────────────────────────────────────────────────

ACCESS_LOG = os.path.join(".ai", "access.log")
CONFIG_FILE = os.path.join(".ai", "engaku.json")

# ── validation defaults ─────────────────────────────────────────────────────

FORBIDDEN_PHRASES = [
    "updated the logic",
    "modified the code",
    "made improvements",
]
MIN_CHARS = 50
MAX_CHARS = 1500
REQUIRED_HEADING = "## Overview"

# ── stats defaults ───────────────────────────────────────────────────────────

STALE_DAYS = 7
