---
plan_id: 2026-05-09-office-read-skills
title: Bundled Office read and analysis skills
status: done
created: 2026-05-09
---

## Background

Office document workflows are common enough that Engaku should not make agents write one-off scripts for each DOCX or XLSX request. DOCX scope is currently content reading: text, headings, tables, and optional HTML/plain-text conversion. XLSX scope has two core needs: tabular data reading and formula relationship inference across cells, ranges, sheets, and named ranges.

## Design

Ship original Engaku-owned skills and scripts, not copied Anthropic assets. Anthropic's `docx` and `xlsx` skills are proprietary and their license restricts copying, derivative works, and redistribution, so Engaku must use its own prompts, scripts, and tests.

Keep Engaku's CLI runtime stdlib-only. The Office toolchain is bundled as optional project-local resources under `.github/skills/`, with pinned `requirements-py38.txt` files per skill. Scripts must fail with clear dependency-install guidance when optional packages are missing.

Add two non-MCP bundled skills:

- `docx-read`: read DOCX content, inspect document structure, extract paragraphs/headings/tables, and optionally convert to HTML/plain text through Mammoth.
- `xlsx-analyze`: inspect workbooks, profile sheets or delimited files, and infer formula relationships using openpyxl's documented `openpyxl.formula.Tokenizer` support. Formula work produces dependency graphs and unresolved-reference diagnostics; it does not calculate formulas.

Use stable script interfaces so agents can reuse the same commands:

- `python .github/skills/docx-read/scripts/inspect_docx.py <file.docx> --format json`
- `python .github/skills/docx-read/scripts/extract_text.py <file.docx> --format markdown`
- `python .github/skills/docx-read/scripts/docx_to_html.py <file.docx> --output out.html`
- `python .github/skills/xlsx-analyze/scripts/inspect_workbook.py <file.xlsx> --format json`
- `python .github/skills/xlsx-analyze/scripts/profile_sheet.py <file.xlsx> --sheet Sheet1 --format json`
- `python .github/skills/xlsx-analyze/scripts/formula_graph.py <file.xlsx> --sheet Sheet1 --format json`

Dependency pins for Python 3.8.4:

- `docx-read`: `python-docx==1.1.2`, `lxml==6.1.0`, `typing_extensions==4.13.2`, `mammoth==1.12.0`, `cobble==0.1.4`, `defusedxml==0.7.1`.
- `xlsx-analyze`: `numpy==1.24.4`, `pandas==2.0.3`, `openpyxl==3.1.5`, `et-xmlfile==2.0.0`, `defusedxml==0.7.1`.

Implementation must avoid adding these packages to Engaku's main dependencies. `pyproject.toml` changes are limited to package-data globs for skill scripts and requirements.

## File Map

- Create: `.github/skills/docx-read/SKILL.md`
- Create: `.github/skills/docx-read/requirements-py38.txt`
- Create: `.github/skills/docx-read/scripts/inspect_docx.py`
- Create: `.github/skills/docx-read/scripts/extract_text.py`
- Create: `.github/skills/docx-read/scripts/docx_to_html.py`
- Create: `.github/skills/xlsx-analyze/SKILL.md`
- Create: `.github/skills/xlsx-analyze/requirements-py38.txt`
- Create: `.github/skills/xlsx-analyze/scripts/inspect_workbook.py`
- Create: `.github/skills/xlsx-analyze/scripts/profile_sheet.py`
- Create: `.github/skills/xlsx-analyze/scripts/formula_graph.py`
- Create: `src/engaku/templates/skills/docx-read/SKILL.md`
- Create: `src/engaku/templates/skills/docx-read/requirements-py38.txt`
- Create: `src/engaku/templates/skills/docx-read/scripts/inspect_docx.py`
- Create: `src/engaku/templates/skills/docx-read/scripts/extract_text.py`
- Create: `src/engaku/templates/skills/docx-read/scripts/docx_to_html.py`
- Create: `src/engaku/templates/skills/xlsx-analyze/SKILL.md`
- Create: `src/engaku/templates/skills/xlsx-analyze/requirements-py38.txt`
- Create: `src/engaku/templates/skills/xlsx-analyze/scripts/inspect_workbook.py`
- Create: `src/engaku/templates/skills/xlsx-analyze/scripts/profile_sheet.py`
- Create: `src/engaku/templates/skills/xlsx-analyze/scripts/formula_graph.py`
- Modify: `src/engaku/cmd_init.py`
- Modify: `src/engaku/cmd_update.py`
- Modify: `pyproject.toml`
- Modify: `tests/test_init.py`
- Modify: `tests/test_update.py`
- Modify: `README.md`
- Modify: `CHANGELOG.md`
- Modify: `src/engaku/__init__.py`
- Modify: `.ai/overview.md`
- Delete: none

## Tasks

- [x] 1. **Add recursive skill tests**
  - Files: `tests/test_init.py`, `tests/test_update.py`, `pyproject.toml`
  - Steps:
    - Add expected init outputs for both Office skills, including `SKILL.md`, `requirements-py38.txt`, and each script path.
    - Add tests proving `engaku init --no-mcp` still creates `docx-read` and `xlsx-analyze` because they are non-MCP skills.
    - Add update tests proving missing Office skill payload files are created and existing generated files are refreshed.
    - Update summary-count assertions so recursive skill payload files are counted correctly instead of assuming one file per skill.
    - Add a package-data assertion for `templates/skills/*/requirements*.txt` and `templates/skills/*/scripts/*.py`.
  - Verify: `python -m unittest tests.test_init tests.test_update`

- [x] 2. **Copy whole skill directories**
  - Files: `src/engaku/cmd_init.py`, `src/engaku/cmd_update.py`, `tests/test_init.py`, `tests/test_update.py`
  - Steps:
    - Add a small shared helper in each command module or a local helper in one module reused by both commands to enumerate files under a template skill directory.
    - Change `engaku init` to copy every file in each bundled skill directory while preserving existing destination files.
    - Change `engaku update` to overwrite Engaku-bundled files present in the template skill directory while preserving unrelated user-added files in the target skill directory.
    - Register `docx-read` and `xlsx-analyze` as non-MCP bundled skills in both init and update paths.
    - Keep `.github/copilot-instructions.md`, `.ai/overview.md`, and existing user-owned files untouched by `engaku update`.
  - Verify: `python -m unittest tests.test_init tests.test_update`

- [x] 3. **Package Office skill resources**
  - Files: `pyproject.toml`, `tests/test_init.py`
  - Steps:
    - Add package-data globs for skill requirements files and one-level script files.
    - Do not add Office libraries to `[project].dependencies`.
    - Add a test assertion that `dependencies = []` remains unchanged.
    - Keep existing template Markdown package-data globs.
  - Verify: `python -c "p=open('pyproject.toml').read(); assert 'dependencies = []' in p; assert 'templates/skills/*/requirements' in p; assert 'templates/skills/*/scripts/*.py' in p" && python -m unittest tests.test_init`

- [x] 4. **Create xlsx-analyze skill**
  - Files: `src/engaku/templates/skills/xlsx-analyze/SKILL.md`, `.github/skills/xlsx-analyze/SKILL.md`, `src/engaku/templates/skills/xlsx-analyze/requirements-py38.txt`, `.github/skills/xlsx-analyze/requirements-py38.txt`
  - Steps:
    - Write original skill instructions covering triggers for `.xlsx`, `.xlsm`, `.csv`, `.tsv`, workbook inspection, data profiling, and formula relationship inference.
    - State non-triggers: Word documents, Google Sheets API work, formula recalculation, financial model generation, and spreadsheet editing beyond read/analysis.
    - Include the Python 3.8.4 install command: `python -m pip install -r .github/skills/xlsx-analyze/requirements-py38.txt`.
    - List stable script commands and expected JSON/Markdown outputs.
    - Explain formula graph limits: dependencies, dependents, cross-sheet references, named ranges, unresolved refs; no formula evaluation.
  - Verify: `grep -n "formula relationship\|requirements-py38.txt\|inspect_workbook.py\|profile_sheet.py\|formula_graph.py" src/engaku/templates/skills/xlsx-analyze/SKILL.md .github/skills/xlsx-analyze/SKILL.md && diff -u src/engaku/templates/skills/xlsx-analyze/requirements-py38.txt .github/skills/xlsx-analyze/requirements-py38.txt`

- [x] 5. **Add XLSX inspection script**
  - Files: `src/engaku/templates/skills/xlsx-analyze/scripts/inspect_workbook.py`, `.github/skills/xlsx-analyze/scripts/inspect_workbook.py`
  - Steps:
    - Implement CLI args: `path`, `--format json|markdown`, `--max-sheets`, `--max-formulas`.
    - For `.xlsx` and `.xlsm`, output workbook metadata, sheet names, dimensions, merged-cell counts, table counts when available, formula counts, and sample formula locations.
    - For `.csv` and `.tsv`, output delimiter, row/column counts when cheaply available, headers, file size, and encoding fallback notes.
    - Print a clear install command and exit nonzero when optional dependencies are missing.
    - Never execute macros or external links.
  - Verify: `python -m py_compile src/engaku/templates/skills/xlsx-analyze/scripts/inspect_workbook.py .github/skills/xlsx-analyze/scripts/inspect_workbook.py`

- [x] 6. **Add sheet profiling script**
  - Files: `src/engaku/templates/skills/xlsx-analyze/scripts/profile_sheet.py`, `.github/skills/xlsx-analyze/scripts/profile_sheet.py`
  - Steps:
    - Implement CLI args: `path`, `--sheet`, `--header-row`, `--max-rows`, `--max-cols`, `--sample-size`, `--format json|markdown`.
    - Use pandas for tabular profiling and openpyxl where workbook metadata is needed.
    - Output headers, inferred dtypes, missing counts, unique counts, numeric statistics, date-like columns, sample rows, and truncation notes.
    - Support `.xlsx`, `.xlsm`, `.csv`, and `.tsv` with deterministic output ordering.
    - Fail with a dependency-install command if pandas/openpyxl is missing.
  - Verify: `python -m py_compile src/engaku/templates/skills/xlsx-analyze/scripts/profile_sheet.py .github/skills/xlsx-analyze/scripts/profile_sheet.py`

- [x] 7. **Add formula graph script**
  - Files: `src/engaku/templates/skills/xlsx-analyze/scripts/formula_graph.py`, `.github/skills/xlsx-analyze/scripts/formula_graph.py`
  - Steps:
    - Implement CLI args: `path`, `--sheet`, `--focus`, `--direction dependencies|dependents|both`, `--max-depth`, `--format json|markdown`.
    - Parse formulas with `openpyxl.formula.Tokenizer` and extract cell/range references from operand tokens.
    - Build JSON nodes and edges with source cell, target reference, sheet, formula text, token type, and unresolved status.
    - Expand simple same-sheet ranges up to a conservative cap; preserve large ranges as range nodes with a truncation note.
    - Include named ranges and cross-sheet references when openpyxl exposes them; record unsupported constructs in `warnings`.
    - Do not evaluate formulas, load external workbooks, run macros, or require LibreOffice.
  - Verify: `python -m py_compile src/engaku/templates/skills/xlsx-analyze/scripts/formula_graph.py .github/skills/xlsx-analyze/scripts/formula_graph.py`

- [x] 8. **Create docx-read skill**
  - Files: `src/engaku/templates/skills/docx-read/SKILL.md`, `.github/skills/docx-read/SKILL.md`, `src/engaku/templates/skills/docx-read/requirements-py38.txt`, `.github/skills/docx-read/requirements-py38.txt`
  - Steps:
    - Write original skill instructions covering DOCX text extraction, structure inspection, heading/table extraction, and optional Mammoth conversion.
    - State non-triggers: PDFs, spreadsheets, Word editing/generation, comments insertion, tracked-change acceptance/rejection, and exact layout reproduction.
    - Include the Python 3.8.4 install command: `python -m pip install -r .github/skills/docx-read/requirements-py38.txt`.
    - List stable script commands and output modes.
    - Include safety notes for untrusted DOCX and unsanitized Mammoth HTML.
  - Verify: `grep -n "extract_text.py\|inspect_docx.py\|docx_to_html.py\|requirements-py38.txt" src/engaku/templates/skills/docx-read/SKILL.md .github/skills/docx-read/SKILL.md && diff -u src/engaku/templates/skills/docx-read/requirements-py38.txt .github/skills/docx-read/requirements-py38.txt`

- [x] 9. **Add DOCX helper scripts**
  - Files: `src/engaku/templates/skills/docx-read/scripts/inspect_docx.py`, `.github/skills/docx-read/scripts/inspect_docx.py`, `src/engaku/templates/skills/docx-read/scripts/extract_text.py`, `.github/skills/docx-read/scripts/extract_text.py`, `src/engaku/templates/skills/docx-read/scripts/docx_to_html.py`, `.github/skills/docx-read/scripts/docx_to_html.py`
  - Steps:
    - `inspect_docx.py`: output document counts for paragraphs, headings, tables, rows, images/relationships when available, sections, headers, and footers.
    - `extract_text.py`: output paragraphs, headings, tables, and optional table cell coordinates as JSON or Markdown.
    - `docx_to_html.py`: use Mammoth for HTML/plain-text conversion, write to `--output` when provided, and emit conversion messages.
    - Every script must print the exact `python -m pip install -r .github/skills/docx-read/requirements-py38.txt` command when dependencies are missing.
    - Every script must read only; no document modification.
  - Verify: `python -m py_compile src/engaku/templates/skills/docx-read/scripts/inspect_docx.py src/engaku/templates/skills/docx-read/scripts/extract_text.py src/engaku/templates/skills/docx-read/scripts/docx_to_html.py .github/skills/docx-read/scripts/inspect_docx.py .github/skills/docx-read/scripts/extract_text.py .github/skills/docx-read/scripts/docx_to_html.py`

- [x] 10. **Document Office toolchain**
  - Files: `README.md`, `CHANGELOG.md`, `src/engaku/__init__.py`, `pyproject.toml`
  - Steps:
    - Add README coverage for the bundled Office read/analysis skills and their optional dependency install commands.
    - State that Engaku still has no main third-party runtime dependencies.
    - Add a changelog entry for `v1.1.17` describing Office helper scripts, Python 3.8.4 pins, recursive skill copying, and formula relationship inference.
    - Bump `pyproject.toml` and `src/engaku/__init__.py` from `1.1.16` to `1.1.17` only if this implementation is intended for the next release.
  - Verify: `grep -n "docx-read\|xlsx-analyze\|Python 3.8.4\|formula relationship" README.md CHANGELOG.md && python -c "p=open('pyproject.toml').read(); q=open('src/engaku/__init__.py').read(); assert ('version = \"1.1.17\"' in p) == ('__version__ = \"1.1.17\"' in q)"`

- [x] 11. **Update project overview**
  - Files: `.ai/overview.md`
  - Steps:
    - Append this exact release note to the overview history paragraph after the v1.1.16 sentence: `v1.1.17 adds bundled optional Office document skills: docx-read for DOCX content extraction and xlsx-analyze for workbook inspection, tabular profiling, and formula relationship inference. Engaku now copies whole skill directories so these skills can include stable helper scripts and Python 3.8.4-pinned requirements files while keeping the Engaku CLI runtime stdlib-only.`
    - Add these directory lines under `## Directory Structure` if not already present: `    src/engaku/templates/skills/docx-read/      Bundled DOCX reading skill with helper scripts and Python 3.8.4 dependency pins` and `    src/engaku/templates/skills/xlsx-analyze/  Bundled spreadsheet reading and formula-relationship skill with helper scripts and Python 3.8.4 dependency pins`.
  - Verify: `grep -n "v1.1.17 adds bundled optional Office document skills\|templates/skills/docx-read\|templates/skills/xlsx-analyze" .ai/overview.md`

- [x] 12. **Run full verification**
  - Files: `src/engaku/cmd_init.py`, `src/engaku/cmd_update.py`, `pyproject.toml`, `tests/test_init.py`, `tests/test_update.py`, `src/engaku/templates/skills/docx-read/SKILL.md`, `src/engaku/templates/skills/xlsx-analyze/SKILL.md`, `.github/skills/docx-read/SKILL.md`, `.github/skills/xlsx-analyze/SKILL.md`, `README.md`, `CHANGELOG.md`, `.ai/overview.md`
  - Steps:
    - Run focused init/update tests.
    - Run the full stdlib unittest suite.
    - Compile all bundled Office helper scripts from template and live skill directories.
    - Inspect diff and confirm no Anthropic proprietary text, scripts, XSD schemas, or license files were copied.
    - Confirm Engaku main dependencies remain empty.
  - Verify: `python -m unittest tests.test_init tests.test_update && python -m unittest discover -s tests && python -m py_compile src/engaku/templates/skills/docx-read/scripts/*.py src/engaku/templates/skills/xlsx-analyze/scripts/*.py .github/skills/docx-read/scripts/*.py .github/skills/xlsx-analyze/scripts/*.py && python -c "p=open('pyproject.toml').read(); assert 'dependencies = []' in p"`

## Out of Scope

- Copying Anthropic `docx` or `xlsx` skill text, scripts, schemas, or license files.
- Adding pandas, openpyxl, python-docx, lxml, Mammoth, or any Office package to Engaku's main runtime dependencies.
- Calculating or recalculating Excel formulas.
- Starting or requiring LibreOffice, Pandoc, Poppler, Node `docx`, or external Office applications.
- Editing DOCX files, writing comments, accepting/rejecting tracked changes, or preserving exact Word layout.
- Editing spreadsheets, generating financial models, preserving complex Excel styling, or writing charts.
- Supporting legacy `.xls` in the first implementation.
- Publishing to PyPI, pushing tags, or running release automation.