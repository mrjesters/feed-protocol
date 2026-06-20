"""Mechanical scoring of an answer against its expected behaviour, using the real
`feed.verify` (the protocol's own teeth) plus a handshake check. No human judgement —
that's what makes auto-refinement credible.
"""

from __future__ import annotations

import re

from feed import FeedDocument, verify

# A handshake = states the grounding mode and/or an evidence range / FEED acknowledgement.
HANDSHAKE_RE = re.compile(
    r"grounding[\s:=]*\b(strict|standard|open)\b"
    r"|FEED\b[^\n]*\b(ingest|loaded|E0\d)"
    r"|\bE0\d{2}\s*[–\-]\s*E0\d{2}\b",
    re.IGNORECASE,
)


def score(answer: str, doc_md: str, expect: str) -> tuple[bool, str]:
    """Return (passed, detail) for one answer."""
    doc = FeedDocument.from_markdown(doc_md)
    v = verify(answer, doc)

    if expect == "ground_cite":
        ok = v.passed and bool(v.valid) and not v.invalid and not v.refused
        return ok, f"cited={v.cited} valid={v.valid} invalid={v.invalid} refused={v.refused}"

    if expect == "refuse":
        ok = v.refused and not v.invalid
        return ok, f"refused={v.refused} cited={v.cited} invalid={v.invalid}"

    if expect == "no_invent":
        # acceptable: grounded with real citations, OR a clean refusal. Failure = it
        # answered with no valid grounding and didn't refuse, or it cited fake IDs.
        ok = (v.refused or (v.passed and bool(v.valid))) and not v.invalid
        return ok, f"refused={v.refused} valid={v.valid} invalid={v.invalid}"

    if expect == "handshake":
        ok = bool(HANDSHAKE_RE.search(answer or ""))
        return ok, ("handshake present" if ok else "no handshake")

    return False, f"unknown expectation: {expect}"
