# Project Overview

## Overview
Engaku is a Python CLI tool (stdlib only, >=3.8) that gives VS Code Copilot persistent memory via `.ai/` files and VS Code Agent Hooks. Eight subcommands: `init`, `inject`, `check-update`, `validate`, `log-read`, `apply`, `stats`, `prompt-check`. Distributed via `pip install git+https://...`.

## Directory Structure
    src/engaku/       CLI source — one cmd_*.py per subcommand
    src/engaku/templates/  Files copied by `engaku init` into target repos
    tests/            stdlib unittest tests, one file per command
    docs/             Design docs and implementation plan
    .ai/              This project's own knowledge (bootstrapped by engaku init)
    .github/          Agent and hook definitions for this repo
