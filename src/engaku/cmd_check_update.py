import fnmatch
import json
import os
import sys
import time

from engaku.constants import RECENT_SECONDS
from engaku.utils import (
    is_code_file,
    load_config,
    parse_frontmatter,
    parse_paths_from_frontmatter,
    parse_transcript_edits,
    read_hook_input,
)

# Backward-compat alias used by existing tests.
_is_code_file = is_code_file


def _get_changed_files(cwd, hook_input=None):
    """Return list of file paths edited in the current turn, relative to cwd.

    Reads the transcript_path from hook_input and returns only edits made after
    the last user.message event (i.e. the current agent turn). Returns [] when
    the transcript is unavailable.
    """
    if hook_input:
        tp = hook_input.get("transcript_path")
        if tp and os.path.isfile(tp):
            return parse_transcript_edits(tp, cwd, last_turn_only=True)
    return []


def _suggest_modules(code_files):
    """Return deduplicated module name guesses derived from changed file paths.

    Uses basename-without-extension as the guess.
    e.g. src/engaku/cmd_check_update.py -> cmd_check_update
    """
    seen = set()
    suggestions = []
    for path in code_files:
        stem = os.path.splitext(os.path.basename(path))[0]
        if stem and stem not in seen:
            seen.add(stem)
            suggestions.append(stem)
    return suggestions


def _load_module_paths(cwd):
    """Return {stem: [declared_paths]} for all modules in .ai/modules/.

    Only modules that have a valid paths: frontmatter list are included.
    """
    modules_dir = os.path.join(cwd, ".ai", "modules")
    result = {}
    if not os.path.isdir(modules_dir):
        return result
    for filename in os.listdir(modules_dir):
        if not filename.endswith(".md"):
            continue
        stem = filename[:-3]
        filepath = os.path.join(modules_dir, filename)
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
        except OSError:
            continue
        fm, _ = parse_frontmatter(content)
        if fm is None:
            continue
        paths = parse_paths_from_frontmatter(fm)
        if paths:
            result[stem] = paths
    return result


def _match_path(changed_path, declared_path):
    """Return True if changed_path is covered by declared_path.

    Matching order (first match wins):
    1. Exact path match
    2. Directory prefix match  (declared_path ends with /  OR  is a directory)
    3. fnmatch glob pattern    (e.g. src/engaku/cmd_*.py)
    """
    cf = os.path.normpath(changed_path)
    dp = os.path.normpath(declared_path)

    # 1. Exact match
    if cf == dp:
        return True

    # 2. Directory prefix  (declared ends with sep after normalisation,
    #    OR the raw declaration ends with /)
    if declared_path.endswith("/") or declared_path.endswith(os.sep):
        return cf.startswith(dp + os.sep) or cf == dp
    if cf.startswith(dp + os.sep):
        return True

    # 3. fnmatch glob (only when pattern contains * or ?)
    if "*" in declared_path or "?" in declared_path:
        return fnmatch.fnmatch(cf, dp)

    return False


def _has_module_files(cwd):
    """Return True if .ai/modules/ contains at least one .md file."""
    modules_dir = os.path.join(cwd, ".ai", "modules")
    if not os.path.isdir(modules_dir):
        return False
    return any(f.endswith(".md") for f in os.listdir(modules_dir))


def _classify_files(cwd, code_files):
    """Split code_files into (claimed_by_stem, unclaimed).

    claimed_by_stem: {module_stem: [matched_files]} for files covered by
                     a module's paths: frontmatter.
    unclaimed:       files not covered by any module.
    """
    module_paths = _load_module_paths(cwd)
    claimed_by_stem = {}   # stem -> list of files it claims
    unclaimed = []

    for cf in code_files:
        matched_stems = []
        for stem, patterns in module_paths.items():
            for pattern in patterns:
                if _match_path(cf, pattern):
                    matched_stems.append(stem)
                    break
        if matched_stems:
            for stem in matched_stems:
                claimed_by_stem.setdefault(stem, []).append(cf)
        else:
            unclaimed.append(cf)

    return claimed_by_stem, unclaimed


def _claimed_modules_updated(cwd, claimed_by_stem, code_files):
    """Return True if ALL modules that claim changed files were updated after
    those files were last modified.

    A module is considered updated if its .md file mtime >= the newest mtime
    among the code files it claims.
    """
    modules_dir = os.path.join(cwd, ".ai", "modules")

    for stem, files in claimed_by_stem.items():
        # Newest mtime among the files this module claims
        code_mtime = 0.0
        for rel in files:
            full = os.path.join(cwd, rel)
            try:
                code_mtime = max(code_mtime, os.path.getmtime(full))
            except OSError:
                pass
        if code_mtime == 0.0:
            code_mtime = time.time() - RECENT_SECONDS

        module_file = os.path.join(modules_dir, stem + ".md")
        try:
            if os.path.getmtime(module_file) < code_mtime:
                return False
        except OSError:
            return False  # module file missing

    return True


def _is_ignored_path(path, patterns):
    """Return True if path matches any user-configured ignore pattern."""
    for pattern in patterns:
        if _match_path(path, pattern):
            return True
    return False


def run():
    hook_input = read_hook_input()

    # Anti-loop guard: if we are already running due to a previous Stop hook
    if hook_input.get("stop_hook_active", False):
        return 0

    cwd = os.getcwd()

    config = load_config(cwd)
    ignore_patterns = config["check_update"]["ignore"]
    changed = _get_changed_files(cwd, hook_input=hook_input)
    code_changes = [
        f for f in changed
        if is_code_file(f) and not _is_ignored_path(f, ignore_patterns)
    ]

    if not code_changes:
        return 0

    # ── Case 1: No module files at all ──────────────────────────────────────
    if not _has_module_files(cwd):
        output = {
            "systemMessage": (
                "No module knowledge files found.\n"
                "Run the scanner agent to build the initial module index."
            )
        }
        sys.stdout.write(json.dumps(output) + "\n")
        return 0

    # ── Classify changed files into claimed / unclaimed ──────────────────────
    claimed_by_stem, unclaimed = _classify_files(cwd, code_changes)

    # ── Case 2: Claimed files exist but their modules are stale ─────────────
    if claimed_by_stem and not _claimed_modules_updated(cwd, claimed_by_stem, code_changes):
        # Find which stems are actually stale for the error message
        modules_dir = os.path.join(cwd, ".ai", "modules")
        stale_stems = []
        for stem, files in claimed_by_stem.items():
            code_mtime = 0.0
            for rel in files:
                full = os.path.join(cwd, rel)
                try:
                    code_mtime = max(code_mtime, os.path.getmtime(full))
                except OSError:
                    pass
            if code_mtime == 0.0:
                code_mtime = time.time() - RECENT_SECONDS
            module_file = os.path.join(modules_dir, stem + ".md")
            try:
                if os.path.getmtime(module_file) < code_mtime:
                    stale_stems.append(stem)
            except OSError:
                stale_stems.append(stem)

        sys.stderr.write(
            "Code changes detected but no knowledge files were updated.\n"
            "Please call the knowledge-keeper subagent to update .ai/modules/ "
            "before ending the session.\n\n"
        )
        sys.stderr.write("Changed files in this session:\n")
        all_claimed_files = [f for files in claimed_by_stem.values() for f in files]
        for f in all_claimed_files:
            sys.stderr.write("  {}\n".format(f))
        if stale_stems:
            sys.stderr.write("\nModules that need updating: {}\n".format(
                ", ".join(stale_stems)
            ))
        return 2

    # ── Case 3: Unclaimed files detected ────────────────────────────────────
    if unclaimed:
        action = config["check_update"]["uncovered_action"]
        if action != "ignore":
            sys.stderr.write(
                "The following files are not covered by any module knowledge file:\n"
            )
            for f in unclaimed:
                sys.stderr.write("  {}\n".format(f))
            sys.stderr.write(
                "Consider running the scanner agent to add module coverage.\n"
            )
        if action == "block":
            files_str = ", ".join(unclaimed)
            prompt_str = "Add coverage for these unclaimed files: {}".format(files_str)
            output = {
                "hookSpecificOutput": {
                    "hookEventName": "Stop",
                    "decision": "block",
                    "reason": (
                        "Unclaimed files detected: {}.\n"
                        "Please call the scanner-update agent first, then call "
                        "knowledge-keeper:\n"
                        "  1. @scanner-update: \"{}\"\n"
                        "  2. @knowledge-keeper: update modules for the changes just made"
                    ).format(files_str, prompt_str),
                }
            }
            sys.stdout.write(json.dumps(output) + "\n")
        elif action != "ignore":
            # warn (default)
            output = {
                "systemMessage": (
                    "Uncovered files detected: {}.\n"
                    "Consider running the scanner agent to add module coverage."
                ).format(", ".join(unclaimed))
            }
            sys.stdout.write(json.dumps(output) + "\n")

    # ── All clear ───────────────────────────────────────────────────────────
    return 0
