---
name: xlsx-analyze
description: Inspect and analyze Excel workbooks (.xlsx/.xlsm) and delimited files (.csv/.tsv). Covers workbook structure inspection, column profiling, and formula relationship inference.
triggers:
  - xlsx file analysis
  - xlsm workbook inspection
  - csv data profiling
  - tsv data exploration
  - formula relationship inference
  - formula dependency graph
  - cell reference mapping
  - sheet structure inspection
non_triggers:
  - Word documents (.docx/.doc) — use docx-read skill instead
  - Google Sheets API or remote spreadsheets
  - Formula evaluation or recalculation
  - Spreadsheet editing, generation, or formatting
  - Chart rendering or visual layout
---

# xlsx-analyze

Inspect Excel workbooks and delimited files, profile column data, and map formula relationships without evaluating any formula.

## Triggers

Use this skill when the task involves:

- Inspecting sheet names, dimensions, merged cells, or formula locations in an `.xlsx` or `.xlsm` file
- Profiling column dtypes, missing values, unique counts, or numeric statistics in a sheet or `.csv`/`.tsv`
- Mapping formula relationship chains: which cells a formula reads from (dependencies) or which cells reference a given cell (dependents)
- Identifying cross-sheet references or named ranges used in formulas
- Finding unresolved external references in a workbook

## Non-triggers

Do **not** use this skill for:

- `.docx` / Word files → use `docx-read` instead
- Editing, writing, or generating spreadsheet content
- Calculating or recalculating formula results (scripts do **not** evaluate formulas)
- Google Sheets or any cloud spreadsheet API
- Rendering charts or exact visual layout

## Setup

```bash
python -m pip install -r .github/skills/xlsx-analyze/requirements-py38.txt
```

Works with Python 3.8.4 and above. No changes to project `dependencies` are required.

## Scripts

### `inspect_workbook.py` — workbook structure

```bash
python .github/skills/xlsx-analyze/scripts/inspect_workbook.py <path> \
    [--format json|markdown] [--max-sheets N] [--max-formulas N]
```

Returns sheet names, row/column dimensions, merged cell count, formula count, and sample formula locations for `.xlsx`/`.xlsm`. Returns delimiter, headers, row count, and file size for `.csv`/`.tsv`.

### `profile_sheet.py` — column statistics

```bash
python .github/skills/xlsx-analyze/scripts/profile_sheet.py <path> \
    [--sheet NAME] [--header-row N] [--max-rows N] [--max-cols N] \
    [--sample-size N] [--format json|markdown]
```

Loads the sheet with pandas and reports per-column: inferred dtype, missing count, unique count, numeric min/max/mean/std, date-like flag, and sample rows.

### `formula_graph.py` — formula relationship inference

```bash
python .github/skills/xlsx-analyze/scripts/formula_graph.py <path> \
    [--sheet NAME] [--focus CELL] \
    [--direction dependencies|dependents|both] \
    [--max-depth N] [--format json|markdown]
```

Parses formulas using `openpyxl.formula.Tokenizer` and builds a graph of cell-to-cell and cell-to-range relationships. Output has `nodes`, `edges`, and `warnings`. Each edge records: `source`, `target`, `sheet`, `formula`, `token_type`, and `unresolved`. Formulas are parsed but **never evaluated**. External workbook references are flagged as `unresolved: true`.

## Output Format

All scripts support `--format json` (default) and `--format markdown`.

### Example: `inspect_workbook.py --format json`

```json
{
  "file": "budget.xlsx",
  "format": "xlsx",
  "sheet_count": 2,
  "sheets": [
    {
      "name": "Summary",
      "min_row": 1, "max_row": 50,
      "min_col": 1, "max_col": 10,
      "merged_cells": 4,
      "formula_count": 15
    }
  ],
  "sample_formulas": [
    {"sheet": "Summary", "cell": "C5", "formula": "=SUM(Data!C2:C48)"}
  ]
}
```

### Example: `formula_graph.py --format json`

```json
{
  "nodes": ["Summary!C5", "Data!C2:C48"],
  "edges": [
    {
      "source": "Summary!C5",
      "target": "C2:C48",
      "sheet": "Data",
      "formula": "=SUM(Data!C2:C48)",
      "token_type": "OPERAND",
      "unresolved": false
    }
  ],
  "warnings": []
}
```

## Limitations

- Formulas are parsed but **not evaluated** — no calculated values are returned.
- External workbook references (e.g. `[other.xlsx]Sheet1!A1`) are marked `unresolved: true`; the external file is never opened.
- Password-protected workbooks cannot be read by openpyxl and produce a clear error.
- Macro-enabled files (`.xlsm`) have formulas parsed; VBA macros are never executed.
- Very large ranges are preserved as range nodes rather than expanded to individual cells.
