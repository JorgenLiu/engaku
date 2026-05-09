"""extract_text.py -- Content extractor for docx-read skill.

Usage:
    python extract_text.py <file.docx> [--format json|markdown]
                           [--include-tables] [--heading-only]

Outputs paragraphs, headings, and tables as sequential content blocks.
"""
import argparse
import json
import os
import sys

_INSTALL_CMD = (
    "python -m pip install -r .github/skills/docx-read/requirements-py38.txt"
)


def _check_deps():
    try:
        import docx  # noqa: F401
    except ImportError:
        sys.stderr.write(
            "Error: python-docx is not installed.\n"
            "Install with: {}\n".format(_INSTALL_CMD)
        )
        sys.exit(1)


def _extract(path, include_tables, heading_only):
    from docx import Document

    doc = Document(path)
    blocks = []

    # Build a set of paragraphs that belong to tables so we can skip them
    # when iterating doc.paragraphs independently (avoid double output)
    table_para_ids = set()
    for tbl in doc.tables:
        for row in tbl.rows:
            for cell in row.cells:
                for para in cell.paragraphs:
                    table_para_ids.add(id(para._element))

    # Walk document body elements in order to preserve sequence
    from docx.oxml.ns import qn

    body = doc.element.body
    for child in body:
        tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag

        if tag == "p":
            # It's a paragraph element
            from docx.text.paragraph import Paragraph
            para = Paragraph(child, doc)
            if id(child) in table_para_ids:
                continue
            style_name = para.style.name if para.style else ""
            text = para.text

            if style_name.startswith("Heading"):
                parts = style_name.split()
                level_str = parts[-1] if parts[-1].isdigit() else "1"
                level = int(level_str)
                blocks.append({
                    "type": "heading",
                    "level": level,
                    "text": text,
                })
            elif not heading_only:
                if text.strip():
                    blocks.append({
                        "type": "paragraph",
                        "text": text,
                    })

        elif tag == "tbl" and include_tables and not heading_only:
            from docx.table import Table
            tbl = Table(child, doc)
            cells = []
            for row in tbl.rows:
                row_cells = [c.text for c in row.cells]
                cells.append(row_cells)
            row_count = len(tbl.rows)
            col_count = max((len(r.cells) for r in tbl.rows), default=0)
            blocks.append({
                "type": "table",
                "rows": row_count,
                "cols": col_count,
                "cells": cells,
            })

    return {
        "file": os.path.basename(path),
        "block_count": len(blocks),
        "blocks": blocks,
    }


def _to_markdown(data):
    lines = ["# Content: {}".format(data.get("file", "")), ""]
    for block in data.get("blocks", []):
        btype = block.get("type")
        if btype == "heading":
            level = block.get("level", 1)
            lines.append("{} {}".format("#" * level, block.get("text", "")))
            lines.append("")
        elif btype == "paragraph":
            lines.append(block.get("text", ""))
            lines.append("")
        elif btype == "table":
            cells = block.get("cells", [])
            if cells:
                header = cells[0]
                lines.append("| " + " | ".join(header) + " |")
                lines.append("| " + " | ".join(["---"] * len(header)) + " |")
                for row in cells[1:]:
                    lines.append("| " + " | ".join(row) + " |")
                lines.append("")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Extract text content from a DOCX file."
    )
    parser.add_argument("path", help="Path to the .docx file")
    parser.add_argument(
        "--format", choices=["json", "markdown"], default="json",
        dest="fmt", help="Output format (default: json)"
    )
    parser.add_argument(
        "--include-tables", action="store_true",
        help="Include table content in output"
    )
    parser.add_argument(
        "--heading-only", action="store_true",
        help="Output only heading blocks"
    )
    args = parser.parse_args()

    if not os.path.exists(args.path):
        sys.stderr.write("Error: file not found: {}\n".format(args.path))
        sys.exit(1)

    _check_deps()
    data = _extract(args.path, args.include_tables, args.heading_only)

    if args.fmt == "markdown":
        print(_to_markdown(data))
    else:
        print(json.dumps(data, indent=2))


if __name__ == "__main__":
    main()
