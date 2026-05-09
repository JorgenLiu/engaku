"""docx_to_html.py -- DOCX to HTML/plain-text converter for docx-read skill.

Uses Mammoth to convert a DOCX file to HTML or plain text.
Mammoth-generated HTML is NOT sanitized — do not render it in a browser
without an HTML sanitizer when the source file is untrusted.

Usage:
    python docx_to_html.py <file.docx> [--output out.html] [--plain-text]

Outputs HTML to stdout or --output file. Conversion messages go to stderr.
"""
import argparse
import os
import sys

_INSTALL_CMD = (
    "python -m pip install -r .github/skills/docx-read/requirements-py38.txt"
)


def _check_deps():
    missing = []
    try:
        import mammoth  # noqa: F401
    except ImportError:
        missing.append("mammoth")
    if missing:
        sys.stderr.write(
            "Error: missing dependencies: {}\n"
            "Install with: {}\n".format(", ".join(missing), _INSTALL_CMD)
        )
        sys.exit(1)


def _convert(path, plain_text):
    import mammoth

    with open(path, "rb") as f:
        if plain_text:
            result = mammoth.extract_raw_text(f)
        else:
            result = mammoth.convert_to_html(f)

    messages = result.messages
    return result.value, messages


def main():
    parser = argparse.ArgumentParser(
        description="Convert a DOCX file to HTML or plain text using Mammoth."
    )
    parser.add_argument("path", help="Path to the .docx file")
    parser.add_argument(
        "--output", default=None,
        help="Write output to this file path instead of stdout"
    )
    parser.add_argument(
        "--plain-text", action="store_true",
        help="Extract plain text instead of HTML"
    )
    args = parser.parse_args()

    if not os.path.exists(args.path):
        sys.stderr.write("Error: file not found: {}\n".format(args.path))
        sys.exit(1)

    _check_deps()
    content, messages = _convert(args.path, args.plain_text)

    for msg in messages:
        level = getattr(msg, "type", "warning")
        text = getattr(msg, "message", str(msg))
        sys.stderr.write("[{}] {}\n".format(level, text))

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(content)
        sys.stderr.write("Written to: {}\n".format(args.output))
    else:
        sys.stdout.write(content)


if __name__ == "__main__":
    main()
