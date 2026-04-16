---
plan_id: 2026-04-16-cicd-and-pypi-publish
title: GitHub CI/CD and PyPI publish
status: in-progress
created: 2026-04-16
---

## Background

engaku is at v0.2.0 with 70 passing tests and a clean `pyproject.toml`.
The PyPI infra, GitHub Actions workflows, and a few pre-publish metadata
fixes are the only remaining steps before `pip install engaku` works from
PyPI. This plan covers everything needed end-to-end: metadata fixes, CI
test workflow, PyPI publish workflow using Trusted Publisher (no stored
token required), and the manual PyPI configuration steps.

## Design

### Release strategy

- Every push/PR to `main` → run tests (`ci.yml`).
- Pushing a tag `v*` (e.g. `v0.2.0`) → build + publish to PyPI (`publish.yml`).
- PyPI project uses **Trusted Publisher** (OIDC) — no API token stored in
  GitHub Secrets. This is the modern PyPI-recommended approach.

### Workflow: `ci.yml`

Triggers: `push` to `main`, `pull_request` to `main`.
Matrix: Python 3.8, 3.9, 3.11 on `ubuntu-latest`.
Steps: checkout → setup-python → install package in editable mode → pytest.

### Workflow: `publish.yml`

Triggers: push of a tag matching `v*.*.*`.
Permissions: `id-token: write` (required for OIDC Trusted Publisher).
Steps: checkout → setup-python 3.11 → install `build` → `python -m build`
→ `pypa/gh-action-pypi-publish` (official action, publishes from `dist/`).

### Version consistency

`pyproject.toml` version and `src/engaku/__init__.py` `__version__` must
match. Single source of truth is `pyproject.toml`; `__init__.py` is kept
in sync manually at release time.

### Pre-publish metadata fixes

`YOUR_USERNAME` placeholder in `pyproject.toml` and `README.md` must be
replaced with `JorgenLiu` before the first publish.

## File Map

- Create: `.github/workflows/ci.yml`
- Create: `.github/workflows/publish.yml`
- Modify: `pyproject.toml` (fix YOUR_USERNAME placeholders)
- Modify: `README.md` (fix YOUR_USERNAME placeholder)

## Manual Steps (not automated — must be done by human)

1. **Create PyPI project with Trusted Publisher**
   - Go to https://pypi.org/manage/account/publishing/
   - Add a new pending publisher:
     - PyPI project name: `engaku`
     - GitHub owner: `JorgenLiu`
     - GitHub repo: `engaku`
     - Workflow filename: `publish.yml`
     - Environment: (leave blank)
   - This must be done *before* the first release tag is pushed.

2. **Push `v0.2.0` tag to trigger publish**
   ```
   git tag v0.2.0
   git push origin v0.2.0
   ```

## Tasks

- [x] 1. **Fix YOUR_USERNAME placeholders in pyproject.toml and README.md**
  - Files: `pyproject.toml`, `README.md`
  - Steps:
    - In `pyproject.toml`: replace both `YOUR_USERNAME` in `[project.urls]`
      with `JorgenLiu`
    - In `README.md`: replace `YOUR_USERNAME` in the pip install git+ line
      with `JorgenLiu`
  - Verify: `grep -r YOUR_USERNAME pyproject.toml README.md` → no output

- [x] 2. **Create CI workflow**
  - Files: `.github/workflows/ci.yml`
  - Steps:
    - Create `.github/workflows/ci.yml` with:
      - `on: push: branches: [main]` and `on: pull_request: branches: [main]`
      - `jobs.test` with `strategy.matrix.python-version: ["3.8", "3.9", "3.11"]`
      - `runs-on: ubuntu-latest`
      - Steps: `actions/checkout@v4`, `actions/setup-python@v5` with
        `python-version: ${{ matrix.python-version }}`, `pip install -e .`,
        `pytest --tb=short -q`
  - Verify: `python -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml'))" 2>/dev/null && echo VALID || python -c "import json; print('yaml not available, check manually')"` — or just: `cat .github/workflows/ci.yml`

- [x] 3. **Create publish workflow**
  - Files: `.github/workflows/publish.yml`
  - Steps:
    - Create `.github/workflows/publish.yml` with:
      - `on: push: tags: ["v*.*.*"]`
      - `permissions: id-token: write; contents: read`
      - `jobs.publish` on `ubuntu-latest`
      - Steps: `actions/checkout@v4`, `actions/setup-python@v5` (3.11),
        `pip install build`, `python -m build`,
        `pypa/gh-action-pypi-publish@release/v1` (no password/token needed
        with Trusted Publisher)
  - Verify: `cat .github/workflows/publish.yml` — shows correct structure

- [x] 4. **Verify package builds cleanly locally**
  - Files: (none → also fixed `pyproject.toml` package-data patterns during this task)
  - Steps:
    - Install `build` locally: `pip install build`
    - Run `python -m build` in repo root
    - Confirm `dist/engaku-0.2.0.tar.gz` and `dist/engaku-0.2.0-py3-none-any.whl` appear
    - Inspect sdist contents: `tar tzf dist/engaku-0.2.0.tar.gz | grep -E "templates|SKILL|agent"` to confirm template files are bundled
  - Verify: `ls dist/ | grep 0.2.0` → both sdist and wheel present; `pip install dist/engaku-0.2.0-py3-none-any.whl --force-reinstall -q && engaku --version` → prints `engaku 0.2.0`

- [ ] 5. **Commit and push, then create and push release tag**
  - Files: (all changed files)
  - Steps:
    - Stage and commit: `git add .github/workflows/ pyproject.toml README.md && git commit -m "ci: add CI/CD workflows and fix metadata placeholders"`
    - Push to main: `git push origin main`
    - Create annotated tag: `git tag -a v0.2.0 -m "Release v0.2.0"`
    - Push tag: `git push origin v0.2.0`
    - This triggers `publish.yml` which publishes to PyPI via Trusted Publisher
  - Verify: after workflow completes → `pip install engaku` in a fresh venv and `engaku --version` prints `engaku 0.2.0`

## Out of Scope

- TestPyPI dry-run (acceptable given clean local build verification).
- Automated version bumping or changelog generation scripts.
- Code signing or attestations (can be added later).
- Release notes automation (GitHub Releases can be written manually).
- Branch protection rules (separate concern).
