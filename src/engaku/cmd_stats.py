"""
engaku stats
Prints a plain-text report with three sections:
  1. Knowledge coverage  — modules with a .ai/modules/*.md vs discovered modules
  2. Knowledge freshness — modules whose knowledge file is >7 days old (via git log)
  3. Access log stats    — reads from .ai/access.log (total reads, unique sessions,
                           per-file breakdown)

With --history: adds a fourth section showing recent git commit history for
each knowledge file, so you can audit what changed and when.
"""
import datetime
import os
import subprocess
import sys

from engaku.constants import STALE_DAYS


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _discover_source_modules(cwd):
    """Return a sorted list of candidate module names from the project source.

    Looks for top-level directories under src/ (if present) or the project
    root, excluding hidden dirs, __pycache__, .ai/, build artifacts, and
    layout-only directories like src/ itself.
    """
    SKIP = {"tests", "test", "docs", "dist", "build", "node_modules", "src"}
    candidates = []

    for base in ("src", "."):
        srcdir = os.path.join(cwd, base)
        if not os.path.isdir(srcdir):
            continue
        for entry in os.listdir(srcdir):
            if entry.startswith(".") or entry.startswith("_"):
                continue
            if entry in SKIP:
                continue
            if entry.endswith(".egg-info") or entry.endswith(".dist-info"):
                continue
            if os.path.isdir(os.path.join(srcdir, entry)):
                candidates.append(entry)
        # If we found anything under src/, don't also scan the root
        if base == "src" and candidates:
            break

    return sorted(set(candidates))


def _knowledge_modules(cwd):
    """Return dict of {stem: abs_path} for .ai/modules/*.md files."""
    modules_dir = os.path.join(cwd, ".ai", "modules")
    result = {}
    if not os.path.isdir(modules_dir):
        return result
    for fname in os.listdir(modules_dir):
        if fname.endswith(".md") and fname != ".gitkeep":
            stem = fname[:-3]
            result[stem] = os.path.join(modules_dir, fname)
    return result


def _git_last_commit_time(path, cwd):
    """Return Unix timestamp of last git commit touching path, or None."""
    try:
        result = subprocess.run(
            ["git", "log", "-1", "--format=%ct", "--", path],
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        out = result.stdout.decode("utf-8", errors="replace").strip()
        if out:
            return int(out)
    except (OSError, ValueError):
        pass
    return None


def _read_access_log(cwd):
    """Return list of (timestamp_str, rel_path, session_id) tuples."""
    log_path = os.path.join(cwd, ".ai", "access.log")
    entries = []
    if not os.path.exists(log_path):
        return entries
    with open(log_path, encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            parts = line.split("\t")
            if len(parts) == 3:
                entries.append((parts[0], parts[1], parts[2]))
    return entries


def _readable_age(ts):
    """Return a human-readable age string from a Unix timestamp."""
    age_sec = int(datetime.datetime.now(datetime.timezone.utc).timestamp()) - ts
    days = age_sec // 86400
    if days > 0:
        return "{} day(s) ago".format(days)
    hours = age_sec // 3600
    if hours > 0:
        return "{} hour(s) ago".format(hours)
    return "< 1 hour ago"


def _git_commit_history(path, cwd, n=5):
    """Return list of commit summary strings (up to n) for path, oldest-last.

    Each entry is a string like: "a1b2c3d  2026-04-08  Update auth module"
    Returns empty list if path has no git history or git is unavailable.
    """
    try:
        result = subprocess.run(
            ["git", "log", "-{}".format(n), "--format=%h\t%ci\t%s", "--", path],
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if result.returncode != 0:
            return []
        lines = result.stdout.decode("utf-8", errors="replace").splitlines()
        entries = []
        for line in lines:
            parts = line.split("\t", 2)
            if len(parts) == 3:
                h, ts, subject = parts
                # Shorten ISO timestamp to date only
                date = ts[:10]
                entries.append("{}  {}  {}".format(h.strip(), date, subject.strip()))
        return entries
    except OSError:
        return []


def _section_history(cwd, out, n=5):
    knowledge = _knowledge_modules(cwd)

    out.append("")
    out.append("## Knowledge History  (last {} commits per file)".format(n))

    if not knowledge:
        out.append("  No knowledge files found.")
        return

    any_history = False
    for stem in sorted(knowledge):
        abs_path = knowledge[stem]
        rel = os.path.relpath(abs_path, cwd)
        entries = _git_commit_history(rel, cwd, n=n)
        out.append("")
        out.append("  {}".format(stem))
        if entries:
            any_history = True
            for entry in entries:
                out.append("    {}".format(entry))
        else:
            out.append("    (no commits yet)")

    if not any_history:
        out.append("")
        out.append("  No git history found. Commit your .ai/modules/ files to track changes.")


# ---------------------------------------------------------------------------
# Report sections
# ---------------------------------------------------------------------------

def _section_coverage(cwd, out):
    source_modules = _discover_source_modules(cwd)
    knowledge = _knowledge_modules(cwd)

    total = len(source_modules)
    covered = sum(1 for m in source_modules if m in knowledge)

    out.append("## Knowledge Coverage")
    if total == 0:
        out.append("  No source modules discovered.")
    else:
        pct = int(covered * 100 / total)
        out.append("  {}/{} modules have knowledge files ({}%)".format(covered, total, pct))
        for m in source_modules:
            marker = "[OK]  " if m in knowledge else "[miss]"
            out.append("  {}  {}".format(marker, m))

    # Show knowledge files without a matching source module
    extra = [m for m in sorted(knowledge) if m not in source_modules]
    if extra:
        out.append("")
        out.append("  Knowledge files with no matching source module:")
        for m in extra:
            out.append("    {}".format(m))


def _section_freshness(cwd, out):
    knowledge = _knowledge_modules(cwd)
    now_ts = int(datetime.datetime.now(datetime.timezone.utc).timestamp())
    stale_cutoff = now_ts - STALE_DAYS * 86400

    out.append("")
    out.append("## Knowledge Freshness  (stale = last commit >{} days ago)".format(STALE_DAYS))

    if not knowledge:
        out.append("  No knowledge files found.")
        return

    for stem in sorted(knowledge):
        abs_path = knowledge[stem]
        rel = os.path.relpath(abs_path, cwd)
        ts = _git_last_commit_time(rel, cwd)
        if ts is None:
            # Fall back to file mtime if not yet committed
            ts = int(os.path.getmtime(abs_path))
            source = "(mtime)"
        else:
            source = ""

        if ts < stale_cutoff:
            label = "[STALE]"
        else:
            label = "[fresh]"
        out.append("  {} {}  {}{}".format(label, stem, _readable_age(ts), "  " + source if source else ""))


def _section_access_log(cwd, out):
    entries = _read_access_log(cwd)

    out.append("")
    out.append("## Access Log")

    if not entries:
        out.append("  No entries in .ai/access.log.")
        return

    out.append("  Total reads:     {}".format(len(entries)))

    sessions = set(e[2] for e in entries if e[2])
    out.append("  Unique sessions: {}".format(len(sessions)))

    counts = {}
    for _, rel_path, _ in entries:
        counts[rel_path] = counts.get(rel_path, 0) + 1

    out.append("")
    out.append("  Reads per file:")
    for path in sorted(counts, key=lambda p: -counts[p]):
        out.append("    {:4d}  {}".format(counts[path], path))


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def run(history=False):
    cwd = os.getcwd()
    out = []

    out.append("engaku stats  —  {}".format(
        datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    ))
    out.append("=" * 60)

    _section_coverage(cwd, out)
    _section_freshness(cwd, out)
    _section_access_log(cwd, out)

    if history:
        _section_history(cwd, out)

    out.append("")
    sys.stdout.write("\n".join(out) + "\n")
    return 0


def main(argv=None):
    import sys as _sys
    _sys.exit(run())

