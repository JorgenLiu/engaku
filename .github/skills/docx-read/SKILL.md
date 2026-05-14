---
name: docx-read
description: Read and inspect DOCX documents. Extracts text, headings, tables, and document structure. Optionally converts to HTML or plain text via Mammoth.
triggers:
  - docx file reading
  - Word document text extraction
  - document heading and table extraction
  - DOCX structure inspection
  - Word to HTML conversion
  - Word to plain text conversion
  - reading comments or tracked changes in Word documents
  - counting footnotes, endnotes, or hyperlinks in Word documents
non_triggers:
  - PDF files — use a PDF extraction tool instead
  - Spreadsheets (.xlsx/.csv) — use xlsx-analyze skill instead
  - Editing, generating, or saving Word documents
  - Modifying, inserting, or resolving comments and tracked changes
  - Accepting or rejecting tracked changes
  - Exact layout or formatting reproduction
---

# docx-read

Read DOCX documents, inspect structure, extract content, and optionally convert to HTML or plain text. Never modifies the source file.

## Triggers

Use this skill when the task involves:

- Extracting text, paragraphs, or headings from a `.docx` file
- Inspecting paragraph counts, heading levels, table dimensions, image references, sections, headers, or footers
- Extracting tables as structured JSON or Markdown
- Converting a DOCX to HTML or plain text using Mammoth

## Non-triggers

Do **not** use this skill for:

- PDF files → use a PDF extraction tool
- Spreadsheets (`.xlsx`, `.csv`) → use `xlsx-analyze` instead
- Editing, writing, or saving Word documents
- Inserting or resolving comments, tracked changes, or annotations
- Reproducing exact Word layout, fonts, or advanced formatting
- Generating new DOCX files from scratch

## Setup

```bash
python -m pip install -r .github/skills/docx-read/requirements-py38.txt
```

Works with Python 3.8.4 and above. No changes to project `dependencies` are required.

## Scripts

### `inspect_docx.py` — document structure

```bash
python .github/skills/docx-read/scripts/inspect_docx.py <file.docx> \
    [--format json|markdown]
```

Returns paragraph count, heading counts by level, table count and dimensions, image/relationship count, section count, header/footer presence, comment count, tracked insertion/deletion counts, hyperlink count, footnote count, endnote count, and core properties (author, title, created date) when available.

> **Safety note:** All inspection is read-only. Comments and tracked changes are counted and optionally extracted; they are never accepted, rejected, inserted, or modified.

### `extract_text.py` — content extraction

```bash
python .github/skills/docx-read/scripts/extract_text.py <file.docx> \
    [--format json|markdown] [--include-tables] [--heading-only] \
    [--include-changes]
```

Returns a sequential list of content blocks (paragraph, heading, table) with text content, heading level, and table cell coordinates. Use `--heading-only` to output only heading blocks. Use `--include-changes` to also output tracked insertions and deletions as text snippets under `tracked_changes`.

### `docx_to_html.py` — HTML/plain-text conversion

```bash
python .github/skills/docx-read/scripts/docx_to_html.py <file.docx> \
    [--output out.html] [--plain-text]
```

Uses Mammoth to convert DOCX to HTML. Use `--plain-text` for stripped plain text. Use `--output` to write to a file; otherwise prints to stdout. Conversion messages (unsupported features, warnings) are printed to stderr.

## Output Format

All scripts support `--format json` (default) and `--format markdown` where applicable.

### Example: `inspect_docx.py --format json`

```json
{
  "file": "report.docx",
  "paragraphs": 42,
  "headings": {"1": 3, "2": 8, "3": 5},
  "tables": 2,
  "images": 4,
  "sections": 1,
  "has_header": true,
  "has_footer": true,
  "properties": {
    "title": "Q1 Report",
    "author": "Jane Doe",
    "created": "2025-01-15T10:30:00"
  }
}
```

### Example: `extract_text.py --format json`

```json
{
  "file": "report.docx",
  "blocks": [
    {"type": "heading", "level": 1, "text": "Introduction"},
    {"type": "paragraph", "text": "This document covers..."},
    {"type": "table", "rows": 3, "cols": 4,
     "cells": [["Header A", "Header B", "Header C", "Header D"], ...]}
  ]
}
```

## Safety Notes

- Scripts open DOCX files in read-only mode and never write back to the source file.
- DOCX files are ZIP archives containing XML; python-docx parses the XML without executing macros.
- Mammoth-generated HTML is **not** sanitized — do not render it in a browser without an HTML sanitizer when the DOCX source is untrusted.
- Embedded external links or OLE objects are not followed or executed.
