"""Structural validation for FEED documents.

Errors block compliance; warnings flag quality/robustness issues. The intent is
that a CI step can run `feed validate` and fail the build on errors.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .constants import (
    CONFIDENCE_LEVELS,
    EVIDENCE_ID_RE,
    EVIDENCE_TYPES,
    GROUNDING_MODES,
    CLAIM_ID_RE,
)
from .document import FeedDocument


@dataclass
class ValidationReport:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors

    def __str__(self) -> str:  # pragma: no cover - cosmetic
        lines = []
        for e in self.errors:
            lines.append(f"  ERROR   {e}")
        for w in self.warnings:
            lines.append(f"  WARN    {w}")
        if not lines:
            lines.append("  OK — valid FEED document")
        return "\n".join(lines)


def validate(doc: FeedDocument) -> ValidationReport:
    r = ValidationReport()

    if doc.grounding not in GROUNDING_MODES:
        r.errors.append(f"grounding {doc.grounding!r} is not one of {GROUNDING_MODES}")

    if not doc.title or not doc.title.strip():
        r.errors.append("document has no title")

    # Evidence checks.
    seen: set[str] = set()
    for ev in doc.evidence:
        if not EVIDENCE_ID_RE.match(ev.id):
            r.errors.append(f"evidence id {ev.id!r} is malformed (expected E001)")
        if ev.id in seen:
            r.errors.append(f"duplicate evidence id {ev.id!r}")
        seen.add(ev.id)
        if not ev.fields:
            r.errors.append(f"evidence {ev.id!r} has no key/value fields")
        if ev.type not in EVIDENCE_TYPES:
            r.warnings.append(f"evidence {ev.id!r} has unusual type {ev.type!r}")
        if ev.confidence not in CONFIDENCE_LEVELS:
            r.warnings.append(
                f"evidence {ev.id!r} has unusual confidence {ev.confidence!r}"
            )

    # Claim checks.
    claim_ids: set[str] = set()
    for c in doc.claims:
        if not CLAIM_ID_RE.match(c.id):
            r.errors.append(f"claim id {c.id!r} is malformed (expected C1)")
        if c.id in claim_ids:
            r.errors.append(f"duplicate claim id {c.id!r}")
        claim_ids.add(c.id)
        for e in c.evidence:
            if e not in seen:
                r.errors.append(f"claim {c.id!r} cites missing evidence {e!r}")
        if doc.grounding == "strict" and not c.evidence:
            r.warnings.append(
                f"claim {c.id!r} has no evidence, but grounding is strict"
            )

    # Whole-document sanity.
    if not doc.evidence:
        r.warnings.append("document has no evidence blocks — nothing to ground answers in")
    if not doc.claims and not doc.findings:
        r.warnings.append("document has no claims or findings — nothing for a reader to act on")

    # Cheap density check: flag evidence written as prose rather than key/value.
    for ev in doc.evidence:
        for k, v in ev.fields.items():
            if len(v) > 240:
                r.warnings.append(
                    f"evidence {ev.id!r} field {k!r} is very long — "
                    "prefer compact key/value facts over prose"
                )
                break

    return r
