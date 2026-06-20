"""Verify that an AI's answer is actually grounded in a FEED document.

This is FEED's defensible edge over plain "AI-friendly" formats: because every
evidence block has a stable plain-text ID and answers must cite by ID, you can
mechanically check an answer:

  - every [E###] it cites exists in the document         (no invented citations)
  - in strict mode, the answer cites at least one block   (it didn't free-wheel)
  - optionally, cited figures actually appear in the answer (loose corroboration)

It is deliberately simple and dependency-free — a 20-line idea with teeth.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .constants import CITATION_RE
from .document import FeedDocument


@dataclass
class VerificationReport:
    cited: list[str] = field(default_factory=list)        # all IDs cited, in order
    valid: list[str] = field(default_factory=list)        # cited and exist
    invalid: list[str] = field(default_factory=list)      # cited but do not exist
    uncited_evidence: list[str] = field(default_factory=list)  # exist but never cited
    corroborated: list[str] = field(default_factory=list)      # cited & a value appears in answer
    grounding: str = "strict"
    passed: bool = False
    reasons: list[str] = field(default_factory=list)

    def __str__(self) -> str:  # pragma: no cover - cosmetic
        status = "PASS" if self.passed else "FAIL"
        lines = [f"  grounding: {self.grounding}    result: {status}"]
        lines.append(f"  cited: {', '.join(self.cited) or '(none)'}")
        if self.invalid:
            lines.append(f"  INVALID citations (no such evidence): {', '.join(self.invalid)}")
        if self.corroborated:
            lines.append(f"  corroborated (a value appears in the answer): {', '.join(self.corroborated)}")
        if self.uncited_evidence:
            lines.append(f"  unused evidence: {', '.join(self.uncited_evidence)}")
        for reason in self.reasons:
            lines.append(f"  - {reason}")
        return "\n".join(lines)


def verify(answer: str, doc: FeedDocument) -> VerificationReport:
    evidence_by_id = {ev.id: ev for ev in doc.evidence}

    cited: list[str] = []
    for match in CITATION_RE.finditer(answer):
        for part in match.group(1).split(","):
            cited.append(part.strip())

    # Preserve order, dedupe for set operations.
    seen: list[str] = []
    for c in cited:
        if c not in seen:
            seen.append(c)

    valid = [c for c in seen if c in evidence_by_id]
    invalid = [c for c in seen if c not in evidence_by_id]
    uncited = [eid for eid in evidence_by_id if eid not in seen]

    lower_answer = answer.lower()
    corroborated: list[str] = []
    for cid in valid:
        ev = evidence_by_id[cid]
        for value in ev.fields.values():
            token = _significant_token(value)
            if token and token.lower() in lower_answer:
                corroborated.append(cid)
                break

    report = VerificationReport(
        cited=cited,
        valid=valid,
        invalid=invalid,
        uncited_evidence=uncited,
        corroborated=corroborated,
        grounding=doc.grounding,
    )

    # Decide pass/fail.
    passed = True
    if invalid:
        passed = False
        report.reasons.append(
            f"answer cites {len(invalid)} evidence ID(s) that do not exist in the document"
        )
    if doc.grounding == "strict" and not cited:
        passed = False
        report.reasons.append(
            "grounding is strict but the answer contains no [E###] citations"
        )
    if doc.grounding == "open" and not cited:
        report.reasons.append("no citations found (allowed in open mode)")
    report.passed = passed
    if passed and not report.reasons:
        report.reasons.append("all citations resolve to real evidence")
    return report


def _significant_token(value: str) -> str | None:
    """Pull a distinctive token (e.g. a number) from an evidence value to look
    for in the answer. Returns None if nothing distinctive enough."""
    import re

    m = re.search(r"\d[\d,.]*", value)
    if m and len(m.group(0)) >= 2:
        return m.group(0)
    # else fall back to the longest word if it is reasonably specific
    words = [w for w in re.findall(r"[A-Za-z0-9_\-]{4,}", value)]
    words.sort(key=len, reverse=True)
    return words[0] if words else None
