import os
import sys
import time

from engaku.constants import (
    FORBIDDEN_PHRASES,
    MAX_CHARS,
    MIN_CHARS,
    RECENT_SECONDS,
    REQUIRED_HEADING,
)
from engaku.utils import load_config, parse_frontmatter, parse_paths_from_frontmatter


def _validate_file(path, max_chars=None):
    """Return list of violation strings for the given file, or empty list if OK."""
    if max_chars is None:
        max_chars = MAX_CHARS
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    _fm, body = parse_frontmatter(content)
    body = body.strip()

    violations = []

    # paths: frontmatter is required for module knowledge files
    if _fm is None:
        violations.append("missing paths: frontmatter")
    else:
        paths = parse_paths_from_frontmatter(_fm)
        if not paths:
            violations.append("paths: list is empty or missing")

    char_count = len(body)

    if char_count < MIN_CHARS:
        violations.append(
            "too short ({} chars, minimum {})".format(char_count, MIN_CHARS)
        )

    if char_count > max_chars:
        violations.append(
            "too long ({} chars, maximum {})".format(char_count, max_chars)
        )

    if REQUIRED_HEADING not in body:
        violations.append('missing required heading "{}"'.format(REQUIRED_HEADING))

    for phrase in FORBIDDEN_PHRASES:
        if phrase in body:
            violations.append('forbidden phrase: "{}"'.format(phrase))

    return violations


def run(recent=False):
    cwd = os.getcwd()
    config = load_config(cwd)
    modules_dir = os.path.join(cwd, ".ai", "modules")

    if not os.path.isdir(modules_dir):
        # Nothing to validate
        return 0

    now = time.time()
    cutoff = now - RECENT_SECONDS

    files = [
        os.path.join(modules_dir, f)
        for f in os.listdir(modules_dir)
        if f.endswith(".md")
    ]

    if recent:
        files = [f for f in files if os.path.getmtime(f) >= cutoff]

    if not files:
        return 0

    any_failed = False
    for filepath in sorted(files):
        rel = os.path.relpath(filepath, cwd)
        try:
            violations = _validate_file(filepath, max_chars=config["max_chars"])
        except Exception as exc:
            sys.stderr.write("[ERROR] {}: {}\n".format(rel, exc))
            any_failed = True
            continue

        if violations:
            any_failed = True
            sys.stderr.write("[FAIL] {}:\n".format(rel))
            for v in violations:
                sys.stderr.write("  - {}\n".format(v))
        else:
            sys.stdout.write("[OK] {}\n".format(rel))

    return 2 if any_failed else 0
