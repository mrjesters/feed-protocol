"""Parse a FEED markdown document back into a FeedDocument.

Robust to extra prose between blocks: we scan for FEED markers and ignore
everything else (including the visible notice blockquote and headings).
"""

from __future__ import annotations

from .constants import (
    CLOSE_MARKER_RE,
    DEFAULT_GROUNDING,
    OPEN_MARKER_RE,
    parse_attrs,
)
from .document import FeedDocument


def parse(text: str) -> FeedDocument:
    blocks = _scan_blocks(text)

    # Document-level header.
    doc_attrs: dict[str, str] = {}
    meta: dict[str, str] = {}
    for kind, attrs, body in blocks:
        if kind == "DOC":
            doc_attrs = attrs
        elif kind == "META":
            meta = _parse_kv(body)

    grounding = doc_attrs.get("grounding") or meta.get("grounding") or DEFAULT_GROUNDING
    title = meta.get("title") or _first_heading(text) or "Untitled"

    doc = FeedDocument(
        title=title,
        author=meta.get("author"),
        grounding=grounding,
        created=meta.get("created"),
        summary=meta.get("summary"),
        version=doc_attrs.get("version", "0.2"),
    )

    # Evidence must be added before claims that reference it, so do two passes.
    for kind, attrs, body in blocks:
        if kind == "EVIDENCE":
            eid = attrs.get("id")
            if not eid:
                continue
            fields = _parse_kv(body, drop_keys={"note"}, drop_id_marker=eid)
            note = _parse_kv(body).get("note")
            doc.add_evidence(
                eid,
                type=attrs.get("type", "data"),
                confidence=attrs.get("confidence", "medium"),
                note=note,
                **fields,
            )

    for kind, attrs, body in blocks:
        if kind == "CLAIM":
            cid = attrs.get("id")
            if not cid:
                continue
            evidence = [
                e.strip()
                for e in (attrs.get("evidence", "").split(","))
                if e.strip()
            ]
            text_body = _claim_text(body)
            doc.add_claim(
                cid,
                text=text_body,
                evidence=evidence,
                decision=attrs.get("decision") or _claim_decision(body),
            )

    # Findings: the markdown under a "## Findings" heading that is not inside a
    # FEED block. Captured separately so round-tripping preserves narrative.
    for para in _findings_paragraphs(text):
        doc.add_finding(para)

    return doc


# --- low-level scanning ---------------------------------------------------
def _scan_blocks(text: str):
    """Yield (kind, attrs_dict, body_text) for every FEED block in order.

    DOC has no body. META/CLAIM/EVIDENCE run until their matching close marker.
    """
    results = []
    pos = 0
    while True:
        m = OPEN_MARKER_RE.search(text, pos)
        if not m:
            break
        kind = m.group("kind")
        attrs = parse_attrs(m.group("attrs"))
        if kind in ("DOC", "END"):
            results.append((kind, attrs, ""))
            pos = m.end()
            continue
        close = CLOSE_MARKER_RE.search(text, m.end())
        if close and close.group("kind") == kind:
            body = text[m.end() : close.start()]
            results.append((kind, attrs, body))
            pos = close.end()
        else:
            # Unterminated block — record what we have and move on.
            results.append((kind, attrs, text[m.end() :]))
            pos = m.end()
    return results


def _parse_kv(
    body: str, drop_keys: set[str] | None = None, drop_id_marker: str | None = None
) -> dict[str, str]:
    drop_keys = drop_keys or set()
    out: dict[str, str] = {}
    for raw in body.splitlines():
        line = raw.strip()
        if not line:
            continue
        if drop_id_marker and line in (f"**[{drop_id_marker}]**", f"[{drop_id_marker}]"):
            continue
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        key = key.strip()
        if not key or " " in key:
            continue  # not a key/value line (probably prose)
        if key in drop_keys:
            continue
        out[key] = value.strip()
    return out


def _claim_text(body: str) -> str:
    for raw in body.splitlines():
        line = raw.strip()
        if not line or line.startswith("- **Decision:**"):
            continue
        # strip trailing [E001][E002] citations from the stored text
        return _strip_citations(line)
    return ""


def _strip_citations(line: str) -> str:
    import re

    return re.sub(r"\s*(\[E\d{1,4}\])+\s*$", "", line).strip()


def _claim_decision(body: str) -> str | None:
    for raw in body.splitlines():
        line = raw.strip()
        if line.startswith("- **Decision:**"):
            return line.split("**Decision:**", 1)[1].strip()
    return None


def _first_heading(text: str) -> str | None:
    for raw in text.splitlines():
        line = raw.strip()
        if line.startswith("# "):
            return line[2:].strip()
    return None


def _findings_paragraphs(text: str) -> list[str]:
    """Pull paragraphs under '## Findings' up to the next heading, skipping any
    FEED comment markers."""
    lines = text.splitlines()
    out: list[str] = []
    in_section = False
    buf: list[str] = []
    for raw in lines:
        line = raw.rstrip()
        stripped = line.strip()
        if stripped.startswith("## "):
            if in_section:  # leaving the section
                break
            in_section = stripped[3:].strip().lower().startswith("finding")
            continue
        if not in_section:
            continue
        if stripped.startswith("<!--") or stripped.startswith("# "):
            continue
        if not stripped:
            if buf:
                out.append(" ".join(buf).strip())
                buf = []
            continue
        buf.append(stripped)
    if buf:
        out.append(" ".join(buf).strip())
    return [p for p in out if p]
