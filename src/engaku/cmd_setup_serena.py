"""engaku setup-serena
Install and configure the Serena MCP server for the current project.

Steps:
  1. Check if `serena` is already installed (shutil.which).
  2. If not found, find or install `uv`.
  3. Install Serena via `uv tool install -p 3.13 serena-agent@latest --prerelease=allow`.
  4. Discover the concrete `serena` executable.
  5. Run `serena init` in cwd.
  6. Patch `.vscode/mcp.json` to use the absolute serena path when discovered.

Failures warn but never block `engaku init` when called_from_init=True.
"""
import json
import os
import shutil
import subprocess
import sys


def _find_uv():
    """Return path to uv executable or None."""
    return shutil.which("uv")


def _install_uv_via_pip():
    """Attempt to install uv via pip. Return True if successful."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "uv"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=120,
        )
        return result.returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


def _find_uv_after_install():
    """Search common locations for uv after pip install."""
    uv = shutil.which("uv")
    if uv:
        return uv
    try:
        import sysconfig
        scripts = sysconfig.get_path("scripts")
        if scripts:
            candidate = os.path.join(scripts, "uv")
            if os.path.isfile(candidate):
                return candidate
    except Exception:
        pass
    try:
        import site
        if hasattr(site, "getuserbase"):
            user_base = site.getuserbase()
            if user_base:
                for subdir in ("bin", "Scripts"):
                    candidate = os.path.join(user_base, subdir, "uv")
                    if os.path.isfile(candidate):
                        return candidate
    except Exception:
        pass
    return None


def _install_serena(uv_path):
    """Install Serena via uv tool install. Return (success, error_message)."""
    try:
        result = subprocess.run(
            [uv_path, "tool", "install", "-p", "3.13",
             "serena-agent@latest", "--prerelease=allow"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=300,
        )
        if result.returncode == 0:
            return True, ""
        return False, result.stderr.decode("utf-8", errors="replace")
    except subprocess.TimeoutExpired:
        return False, "uv tool install timed out"
    except OSError as exc:
        return False, str(exc)


def _find_serena_executable(uv_path):
    """Discover the concrete serena executable after installation."""
    serena = shutil.which("serena")
    if serena:
        return serena
    # Inspect uv tool directory
    try:
        result = subprocess.run(
            [uv_path, "tool", "dir"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=30,
        )
        if result.returncode == 0:
            tool_dir = result.stdout.decode("utf-8", errors="replace").strip()
            # uv places bin/ one level above the tool dir in some layouts
            for candidate in (
                os.path.join(tool_dir, "..", "bin", "serena"),
                os.path.join(tool_dir, "serena-agent", "bin", "serena"),
                os.path.join(tool_dir, "bin", "serena"),
            ):
                candidate = os.path.abspath(candidate)
                if os.path.isfile(candidate):
                    return candidate
    except (OSError, subprocess.TimeoutExpired):
        pass
    return None


def _validate_serena(serena_path):
    """Return True if the serena executable responds to --version or --help."""
    for flag in ("--version", "--help"):
        try:
            result = subprocess.run(
                [serena_path, flag],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=15,
            )
            if result.returncode == 0:
                return True
        except (OSError, subprocess.TimeoutExpired):
            continue
    return False


def _run_serena_init(serena_path, cwd):
    """Run `serena init` under a timeout. Return (success, error_message)."""
    try:
        result = subprocess.run(
            [serena_path, "init"],
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=60,
        )
        if result.returncode == 0:
            return True, ""
        return False, result.stderr.decode("utf-8", errors="replace")
    except subprocess.TimeoutExpired:
        return False, "serena init timed out after 60 seconds"
    except OSError as exc:
        return False, str(exc)


def _patch_mcp_json(cwd, serena_cmd):
    """Update .vscode/mcp.json serena entry to use the given command.

    Returns True if the file was modified, False otherwise.
    """
    mcp_path = os.path.join(cwd, ".vscode", "mcp.json")
    if not os.path.isfile(mcp_path):
        return False
    try:
        with open(mcp_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (ValueError, OSError):
        return False
    servers = data.get("servers", {})
    if "serena" not in servers:
        return False
    if servers["serena"].get("command") == serena_cmd:
        return False  # already correct
    servers["serena"]["command"] = serena_cmd
    try:
        with open(mcp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
            f.write("\n")
        return True
    except OSError:
        return False


def run(cwd=None, called_from_init=False):
    """Install and configure Serena MCP server.

    Returns 0 on success.  Returns 1 on failure only when called directly
    (not from engaku init).  When called_from_init=True, failures are
    printed as warnings and 0 is returned so init never blocks.
    """
    if cwd is None:
        cwd = os.getcwd()

    def _warn(msg):
        sys.stderr.write("Warning: {}\n".format(msg))

    def _fail(msg):
        if called_from_init:
            _warn(msg)
            return 0
        sys.stderr.write("{}\n".format(msg))
        return 1

    # Step 1: Check if serena is already available
    serena_path = shutil.which("serena")
    if serena_path:
        sys.stdout.write("Serena already installed: {}\n".format(serena_path))
    else:
        # Step 2: Find or install uv
        uv_path = _find_uv()
        if not uv_path:
            sys.stdout.write("uv not found — installing via pip...\n")
            if _install_uv_via_pip():
                uv_path = _find_uv_after_install()
            if not uv_path:
                return _fail(
                    "uv is not available and could not be installed.\n"
                    "Manual recovery:\n"
                    "  python -m pip install uv\n"
                    "  uv tool install -p 3.13 serena-agent@latest --prerelease=allow\n"
                    "  serena init\n"
                )

        # Step 3: Install Serena
        sys.stdout.write("Installing Serena via uv...\n")
        success, err = _install_serena(uv_path)
        if not success:
            return _fail(
                "Failed to install Serena: {}\n"
                "Manual recovery:\n"
                "  uv tool install -p 3.13 serena-agent@latest --prerelease=allow\n"
                "  serena init\n"
                "Or rerun: engaku setup-serena\n".format(err)
            )

        # Step 4: Discover serena executable
        serena_path = _find_serena_executable(uv_path)
        if not serena_path:
            return _fail(
                "Serena was installed but executable not found on PATH.\n"
                "Manual recovery:\n"
                "  serena init\n"
                "Or rerun after PATH update: engaku setup-serena\n"
            )
        sys.stdout.write("Serena installed: {}\n".format(serena_path))

    # Validate executable
    if not _validate_serena(serena_path):
        return _fail(
            "serena at {} failed validation.\n"
            "Rerun: engaku setup-serena\n".format(serena_path)
        )

    # Step 5: Run serena init
    sys.stdout.write("Running serena init...\n")
    ok, err = _run_serena_init(serena_path, cwd)
    if not ok:
        return _fail(
            "serena init failed: {}\n"
            "Manual recovery: cd {} && serena init\n"
            "Or rerun: engaku setup-serena\n".format(err, cwd)
        )

    # Step 6: Patch mcp.json if we have an absolute path
    if os.path.isabs(serena_path):
        if _patch_mcp_json(cwd, serena_path):
            sys.stdout.write(
                "Patched .vscode/mcp.json: serena command -> {}\n".format(serena_path)
            )

    sys.stdout.write("Serena setup complete.\n")
    return 0


def main(argv=None):
    sys.exit(run())
