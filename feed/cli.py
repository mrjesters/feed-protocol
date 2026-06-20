"""`feed` command-line interface.

    feed validate report.md
    feed verify --doc report.md --answer answer.txt
    feed render report.md --to html -o report.html
    feed tag draft.md --title "Q2 Report" --grounding strict -o report.md
"""

from __future__ import annotations

import argparse
import sys

from .document import FeedDocument
from .verify import verify


def _read(path: str) -> str:
    if path == "-":
        return sys.stdin.read()
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def _write(text: str, out: str | None) -> None:
    if out and out != "-":
        with open(out, "w", encoding="utf-8") as fh:
            fh.write(text)
        print(f"wrote {out}", file=sys.stderr)
    else:
        sys.stdout.write(text)


def cmd_validate(args) -> int:
    doc = FeedDocument.from_markdown(_read(args.file))
    report = doc.validate()
    print(f"FEED {doc.version} · grounding={doc.grounding} · "
          f"{len(doc.evidence)} evidence · {len(doc.claims)} claims")
    print(report)
    return 0 if report.ok else 1


def cmd_verify(args) -> int:
    doc = FeedDocument.from_markdown(_read(args.doc))
    answer = _read(args.answer)
    report = verify(answer, doc)
    print(report)
    return 0 if report.passed else 1


def cmd_render(args) -> int:
    doc = FeedDocument.from_markdown(_read(args.file))
    _write(doc.render(args.to), args.output)
    return 0


def cmd_prompt(args) -> int:
    """Emit the portable authoring kit so any AI can produce FEED — no key needed."""
    import json as _json

    from .authoring import AUTHORING_PROMPT, FEED_JSON_SCHEMA

    if args.schema_only:
        print(_json.dumps(FEED_JSON_SCHEMA, indent=2))
        return 0
    print(AUTHORING_PROMPT)
    print("\n--- JSON SCHEMA (the AI must emit JSON matching this) ---\n")
    print(_json.dumps(FEED_JSON_SCHEMA, indent=2))
    return 0


def cmd_build(args) -> int:
    """Render FEED from the structured JSON an AI produced. Pure Python, no key."""
    import json as _json

    from .authoring import build

    data = _json.loads(_read(args.file))
    doc = build(
        data,
        title=args.title,
        author=args.author,
        grounding=args.grounding,
        created=args.created,
    )
    report = doc.validate()
    if not report.ok:
        print("built document failed validation:", file=sys.stderr)
        print(report, file=sys.stderr)
    _write(doc.render(args.to), args.output)
    return 0 if report.ok else 1


def cmd_tag(args) -> int:
    from .tagger import auto_tag

    doc = auto_tag(
        _read(args.file),
        title=args.title,
        author=args.author,
        grounding=args.grounding,
        created=args.created,
        model=args.model,
    )
    report = doc.validate()
    if not report.ok:
        print("tagged document failed validation:", file=sys.stderr)
        print(report, file=sys.stderr)
    _write(doc.render(args.to), args.output)
    return 0 if report.ok else 1


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="feed", description="FEED protocol toolkit")
    p.add_argument("--version", action="version", version=f"feed {_version()}")
    sub = p.add_subparsers(dest="command", required=True)

    v = sub.add_parser("validate", help="check a FEED document is well-formed")
    v.add_argument("file", help="FEED markdown file ('-' for stdin)")
    v.set_defaults(func=cmd_validate)

    vf = sub.add_parser("verify", help="check an AI answer is grounded in a FEED doc")
    vf.add_argument("--doc", required=True, help="the FEED document")
    vf.add_argument("--answer", required=True, help="the AI's answer text ('-' for stdin)")
    vf.set_defaults(func=cmd_verify)

    r = sub.add_parser("render", help="render a FEED document to md or html")
    r.add_argument("file", help="FEED markdown file ('-' for stdin)")
    r.add_argument("--to", choices=["md", "html"], default="html")
    r.add_argument("-o", "--output", help="output path (default: stdout)")
    r.set_defaults(func=cmd_render)

    pr = sub.add_parser(
        "prompt",
        help="print the authoring prompt + JSON schema for any AI to emit FEED (no key)",
    )
    pr.add_argument("--schema-only", action="store_true", help="print just the JSON schema")
    pr.set_defaults(func=cmd_prompt)

    b = sub.add_parser(
        "build", help="render FEED from the JSON an AI produced (pure Python, no key)"
    )
    b.add_argument("file", help="JSON file matching the FEED schema ('-' for stdin)")
    b.add_argument("--title")
    b.add_argument("--author")
    b.add_argument("--created")
    b.add_argument("--grounding", choices=["strict", "standard", "open"], default="strict")
    b.add_argument("--to", choices=["md", "html"], default="md")
    b.add_argument("-o", "--output", help="output path (default: stdout)")
    b.set_defaults(func=cmd_build)

    t = sub.add_parser(
        "tag",
        help="OPTIONAL convenience: auto-tag a plain doc via Claude (needs ANTHROPIC_API_KEY)",
    )
    t.add_argument("file", help="plain markdown/text file ('-' for stdin)")
    t.add_argument("--title")
    t.add_argument("--author")
    t.add_argument("--created")
    t.add_argument("--grounding", choices=["strict", "standard", "open"], default="strict")
    t.add_argument("--model", default="claude-opus-4-8")
    t.add_argument("--to", choices=["md", "html"], default="md")
    t.add_argument("-o", "--output", help="output path (default: stdout)")
    t.set_defaults(func=cmd_tag)

    return p


def _version() -> str:
    from . import __version__

    return __version__


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
