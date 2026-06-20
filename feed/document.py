"""The FEED data model and document builder.

Three primitives, as in the spec:
  - Header  (FeedDocument metadata + the self-teaching notice)
  - Evidence  (atomic, ID'd, structured key/value facts — the source of truth)
  - Claim   (narrative statements that reference evidence by ID)
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .constants import (
    CONFIDENCE_LEVELS,
    DEFAULT_GROUNDING,
    EVIDENCE_ID_RE,
    EVIDENCE_TYPES,
    GROUNDING_MODES,
    CLAIM_ID_RE,
    VERSION,
)


@dataclass
class Evidence:
    """An atomic, structured fact. Key/value, never prose — so a reading AI can
    compare values across blocks without parsing natural language."""

    id: str
    fields: dict[str, str] = field(default_factory=dict)
    type: str = "data"
    confidence: str = "medium"
    note: str | None = None  # one optional short free-text line

    def __post_init__(self) -> None:
        if not EVIDENCE_ID_RE.match(self.id):
            raise ValueError(f"Evidence id must look like E001, got {self.id!r}")
        if self.type not in EVIDENCE_TYPES:
            raise ValueError(
                f"Evidence type must be one of {EVIDENCE_TYPES}, got {self.type!r}"
            )
        if self.confidence not in CONFIDENCE_LEVELS:
            raise ValueError(
                f"confidence must be one of {CONFIDENCE_LEVELS}, got {self.confidence!r}"
            )


@dataclass
class Claim:
    """A narrative statement, optionally tied to a decision, grounded in evidence."""

    id: str
    text: str
    evidence: list[str] = field(default_factory=list)
    decision: str | None = None

    def __post_init__(self) -> None:
        if not CLAIM_ID_RE.match(self.id):
            raise ValueError(f"Claim id must look like C1, got {self.id!r}")


class FeedDocument:
    """Build a FEED document programmatically, then render/validate it.

    The builder enforces the structure so a pipeline *cannot* emit a bloated or
    internally inconsistent document: evidence is key/value, claim references
    must point at evidence that exists, IDs must be unique and well-formed.
    """

    def __init__(
        self,
        title: str,
        author: str | None = None,
        grounding: str = DEFAULT_GROUNDING,
        created: str | None = None,
        summary: str | None = None,
        version: str = VERSION,
    ) -> None:
        if grounding not in GROUNDING_MODES:
            raise ValueError(f"grounding must be one of {GROUNDING_MODES}")
        self.title = title
        self.author = author
        self.grounding = grounding
        self.created = created
        self.summary = summary
        self.version = version
        self.claims: list[Claim] = []
        self.findings: list[str] = []  # tier-1 narrative paragraphs
        self.evidence: list[Evidence] = []
        self._evidence_ids: set[str] = set()
        self._claim_ids: set[str] = set()

    # -- builders ----------------------------------------------------------
    def add_evidence(
        self,
        id: str,
        type: str = "data",
        confidence: str = "medium",
        note: str | None = None,
        **fields: object,
    ) -> Evidence:
        if id in self._evidence_ids:
            raise ValueError(f"Duplicate evidence id {id!r}")
        if not fields:
            raise ValueError(f"Evidence {id!r} needs at least one key/value field")
        ev = Evidence(
            id=id,
            type=type,
            confidence=confidence,
            note=note,
            fields={k: _normalise(v) for k, v in fields.items()},
        )
        self.evidence.append(ev)
        self._evidence_ids.add(id)
        return ev

    def add_claim(
        self,
        id: str,
        text: str,
        evidence: list[str] | None = None,
        decision: str | None = None,
    ) -> Claim:
        if id in self._claim_ids:
            raise ValueError(f"Duplicate claim id {id!r}")
        evidence = evidence or []
        missing = [e for e in evidence if e not in self._evidence_ids]
        if missing:
            raise ValueError(
                f"Claim {id!r} references evidence that does not exist: {missing}. "
                "Add the evidence block first."
            )
        claim = Claim(id=id, text=text, evidence=list(evidence), decision=decision)
        self.claims.append(claim)
        self._claim_ids.add(id)
        return claim

    def add_finding(self, text: str) -> None:
        """Add a tier-1 narrative paragraph. Reference evidence inline as [E001]."""
        self.findings.append(text.strip())

    # -- output ------------------------------------------------------------
    def to_markdown(self) -> str:
        from .render import to_markdown

        return to_markdown(self)

    def to_html(self) -> str:
        from .render import to_html

        return to_html(self)

    def render(self, fmt: str = "md") -> str:
        if fmt in ("md", "markdown"):
            return self.to_markdown()
        if fmt == "html":
            return self.to_html()
        raise ValueError("fmt must be 'md' or 'html'")

    def write(self, path: str, fmt: str | None = None) -> None:
        if fmt is None:
            fmt = "html" if path.endswith((".html", ".htm")) else "md"
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(self.render(fmt))

    def validate(self):
        from .validate import validate

        return validate(self)

    @classmethod
    def from_markdown(cls, text: str) -> "FeedDocument":
        from .parser import parse

        return parse(text)

    @classmethod
    def read(cls, path: str) -> "FeedDocument":
        with open(path, encoding="utf-8") as fh:
            return cls.from_markdown(fh.read())

    def __repr__(self) -> str:  # pragma: no cover - cosmetic
        return (
            f"FeedDocument(title={self.title!r}, grounding={self.grounding!r}, "
            f"claims={len(self.claims)}, evidence={len(self.evidence)})"
        )


def _normalise(value: object) -> str:
    """Render a field value as a compact, comparable string."""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, float):
        # trim trailing zeros without losing precision people care about
        return f"{value:g}"
    return str(value).strip()
