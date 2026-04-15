"""
engaku.constants
Framework-level built-in defaults.  These are the values used when no
user configuration is present.  Do not put user-configurable settings here —
those belong in .ai/engaku.json (loaded by utils.load_config).
"""
import os

# ── shared file paths ───────────────────────────────────────────────────────

CONFIG_FILE = os.path.join(".ai", "engaku.json")
