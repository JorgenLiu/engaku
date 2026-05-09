"""profile_sheet.py -- Column profiler for xlsx-analyze skill.

Usage:
    python profile_sheet.py <path> [--sheet NAME] [--header-row N]
                            [--max-rows N] [--max-cols N]
                            [--sample-size N] [--format json|markdown]

Supported file types: .xlsx, .xlsm, .csv, .tsv
"""
import argparse
import json
import math
import os
import sys

_INSTALL_CMD = (
    "python -m pip install -r .github/skills/xlsx-analyze/requirements-py38.txt"
)


def _check_deps():
    missing = []
    try:
        import pandas  # noqa: F401
    except ImportError:
        missing.append("pandas")
    try:
        import openpyxl  # noqa: F401
    except ImportError:
        missing.append("openpyxl")
    if missing:
        sys.stderr.write(
            "Error: missing dependencies: {}\n"
            "Install with: {}\n".format(", ".join(missing), _INSTALL_CMD)
        )
        sys.exit(1)


def _json_safe(val):
    if val is None:
        return None
    try:
        f = float(val)
        if math.isnan(f) or math.isinf(f):
            return None
        return f
    except (TypeError, ValueError):
        return None


def _profile_df(df, sample_size):
    import pandas as pd

    columns = []
    for col in df.columns:
        series = df[col]
        total = len(series)
        missing = int(series.isna().sum())
        unique = int(series.nunique(dropna=True))

        col_info = {
            "name": str(col),
            "dtype": str(series.dtype),
            "total": total,
            "missing": missing,
            "missing_pct": round(missing / total * 100, 2) if total > 0 else 0.0,
            "unique": unique,
        }

        if pd.api.types.is_numeric_dtype(series):
            desc = series.describe()
            col_info["min"] = _json_safe(desc.get("min"))
            col_info["max"] = _json_safe(desc.get("max"))
            col_info["mean"] = _json_safe(desc.get("mean"))
            col_info["std"] = _json_safe(desc.get("std"))

        if pd.api.types.is_datetime64_any_dtype(series):
            col_info["date_like"] = True
        elif str(series.dtype) == "object":
            sample = series.dropna().head(10)
            date_hits = 0
            for v in sample:
                try:
                    pd.to_datetime(str(v))
                    date_hits += 1
                except Exception:
                    pass
            col_info["date_like"] = date_hits >= max(1, len(sample) // 2)
        else:
            col_info["date_like"] = False

        columns.append(col_info)

    sample_rows = df.head(sample_size).fillna("").astype(str).values.tolist()
    return columns, sample_rows


def _load_dataframe(path, sheet, header_row, max_rows, max_cols):
    import pandas as pd

    ext = os.path.splitext(path)[1].lower()
    header_idx = (header_row - 1) if header_row and header_row >= 1 else 0

    if ext in (".csv", ".tsv"):
        delimiter = "\t" if ext == ".tsv" else ","
        df = pd.read_csv(
            path,
            delimiter=delimiter,
            header=header_idx,
            nrows=max_rows if max_rows else None,
            low_memory=False,
        )
    elif ext in (".xlsx", ".xlsm"):
        df = pd.read_excel(
            path,
            sheet_name=sheet if sheet is not None else 0,
            header=header_idx,
            nrows=max_rows if max_rows else None,
            engine="openpyxl",
        )
    else:
        sys.stderr.write(
            "Error: unsupported file type '{}'. "
            "Supported: .xlsx, .xlsm, .csv, .tsv\n".format(ext)
        )
        sys.exit(1)

    truncated_cols = False
    if max_cols and len(df.columns) > max_cols:
        df = df.iloc[:, :max_cols]
        truncated_cols = True

    return df, truncated_cols


def _to_markdown(data):
    lines = ["# Sheet Profile: {}".format(data.get("file", ""))]
    if data.get("sheet"):
        lines.append("**Sheet:** {}".format(data["sheet"]))
    lines.append("**Rows:** {} | **Columns:** {}".format(
        data.get("row_count", "?"), data.get("column_count", "?")
    ))
    for note in data.get("truncation_notes", []):
        lines.append("**Note:** {}".format(note))
    lines.append("")
    lines.append("## Columns")
    lines.append("")
    lines.append("| Column | Dtype | Missing | Unique | Min | Max | Mean |")
    lines.append("|--------|-------|---------|--------|-----|-----|------|")
    for c in data.get("columns", []):
        lines.append("| {} | {} | {}/{} ({:.1f}%) | {} | {} | {} | {} |".format(
            c["name"], c["dtype"],
            c["missing"], c["total"], c["missing_pct"],
            c["unique"],
            c.get("min", ""),
            c.get("max", ""),
            c.get("mean", ""),
        ))
    lines.append("")
    lines.append("## Sample Rows")
    lines.append("")
    headers = [c["name"] for c in data.get("columns", [])]
    if headers:
        lines.append("| " + " | ".join(headers) + " |")
        lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
        for row in data.get("sample_rows", []):
            lines.append("| " + " | ".join(str(v) for v in row) + " |")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Profile columns in a spreadsheet or delimited file."
    )
    parser.add_argument("path", help="Path to .xlsx, .xlsm, .csv, or .tsv file")
    parser.add_argument(
        "--sheet", default=None,
        help="Sheet name (xlsx/xlsm only; default: first sheet)"
    )
    parser.add_argument(
        "--header-row", type=int, default=1,
        help="1-based header row index (default: 1)"
    )
    parser.add_argument(
        "--max-rows", type=int, default=None,
        help="Max data rows to load"
    )
    parser.add_argument(
        "--max-cols", type=int, default=None,
        help="Max columns to profile"
    )
    parser.add_argument(
        "--sample-size", type=int, default=5,
        help="Number of sample rows to include (default: 5)"
    )
    parser.add_argument(
        "--format", choices=["json", "markdown"], default="json",
        dest="fmt", help="Output format (default: json)"
    )
    args = parser.parse_args()

    if not os.path.exists(args.path):
        sys.stderr.write("Error: file not found: {}\n".format(args.path))
        sys.exit(1)

    _check_deps()

    df, truncated_cols = _load_dataframe(
        args.path, args.sheet, args.header_row, args.max_rows, args.max_cols
    )
    columns, sample_rows = _profile_df(df, args.sample_size)

    truncation_notes = []
    if truncated_cols:
        truncation_notes.append("Column count truncated to {}.".format(args.max_cols))
    if args.max_rows and len(df) >= args.max_rows:
        truncation_notes.append("Row count limited to {}.".format(args.max_rows))

    data = {
        "file": os.path.basename(args.path),
        "sheet": args.sheet,
        "row_count": len(df),
        "column_count": len(df.columns),
        "columns": columns,
        "sample_rows": sample_rows,
        "truncation_notes": truncation_notes,
    }

    if args.fmt == "markdown":
        print(_to_markdown(data))
    else:
        print(json.dumps(data, indent=2))


if __name__ == "__main__":
    main()
