"""The authoring side of FEED — self-bootstrapping, no API key required.

FEED is an AI-to-AI protocol. The AI that is *already in the loop* (the one that
wrote the report, or the user's assistant, or a pipeline step) is what produces
FEED — the library never needs its own LLM credentials.

That works because the authoring rules are portable, exactly like the ingestion
notice is portable on the reading side:

  1. `AUTHORING_PROMPT` + `FEED_JSON_SCHEMA` — hand these to *any* AI and it emits
     conformant FEED data. No FEED-specific tooling on the AI's side.
  2. `build(data)` — a pure-Python, dependency-free renderer that turns that data
     into a validated FEED document. No network, no key.

The optional `feed.tagger` module is a convenience wrapper that calls Claude for
people who don't already have an AI in the loop — it is not the primary path.
"""

from __future__ import annotations

from .document import FeedDocument

# The instruction block to give any AI so it authors FEED natively.
AUTHORING_PROMPT = """\
You are producing a FEED document (Format for Enforced Evidence-based Digestion).
FEED separates a document so a downstream AI can answer questions grounded in cited
evidence. Return ONLY JSON matching the provided schema. Structure the content as:

- evidence: every concrete fact in the source, as an atomic key/value block. Never
  prose. Each gets an id E001, E002, ... in document order. Normalise values: ISO
  dates (YYYY-MM-DD), explicit units, consistent names. Include thresholds and
  baselines as their own fields when present. `type` is one of data | quote | calc |
  observation | reference | image; `confidence` is high | medium | low; `note` is an
  optional one-line free-text aside ("" if none).
- claims: short narrative statements (ids C1, C2, ...), each grounded in one or more
  evidence ids. If a claim implies an action, put it in `decision` ("" if none).
- findings: brief narrative paragraphs (1-3 sentences) that reference evidence inline
  as [E001]. Say each fact once and reference it by id rather than repeating it.
- title and summary: the document title and a one-sentence bottom line.

Rules: extract every concrete fact as evidence; never invent facts; be dense (no
filler, no repetition); keep ids sequential and in document order.
"""

# JSON Schema the AI should emit. Compatible with Anthropic structured outputs
# (additionalProperties:false everywhere) but usable with any model — paste it
# alongside AUTHORING_PROMPT.
FEED_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "summary": {"type": "string"},
        "evidence": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "type": {
                        "type": "string",
                        "enum": ["data", "quote", "calc", "observation", "reference", "image"],
                    },
                    "confidence": {"type": "string", "enum": ["high", "medium", "low"]},
                    "fields": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "key": {"type": "string"},
                                "value": {"type": "string"},
                            },
                            "required": ["key", "value"],
                            "additionalProperties": False,
                        },
                    },
                    "note": {"type": "string"},
                },
                "required": ["id", "type", "confidence", "fields", "note"],
                "additionalProperties": False,
            },
        },
        "claims": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "text": {"type": "string"},
                    "evidence": {"type": "array", "items": {"type": "string"}},
                    "decision": {"type": "string"},
                },
                "required": ["id", "text", "evidence", "decision"],
                "additionalProperties": False,
            },
        },
        "findings": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["title", "summary", "evidence", "claims", "findings"],
    "additionalProperties": False,
}


def build(
    data: dict,
    title: str | None = None,
    author: str | None = None,
    grounding: str = "strict",
    created: str | None = None,
) -> FeedDocument:
    """Render a FeedDocument from the structured data an AI produced. Pure Python,
    no LLM call. `grounding`, `author`, `created` are author-policy overrides — they
    are not the AI's to decide, so they come from the caller, not the data.

    Resilient to imperfect AI output: claim references to non-existent evidence are
    dropped, and evidence with no fields is skipped, so a slightly-off model
    response still yields a valid document.
    """
    doc = FeedDocument(
        title=title or data.get("title") or "Untitled",
        author=author or data.get("author"),
        grounding=grounding,
        created=created or data.get("created"),
        summary=data.get("summary") or None,
    )
    for ev in data.get("evidence", []):
        fields = _fields(ev)
        if not fields:
            continue
        doc.add_evidence(
            ev["id"],
            type=ev.get("type", "data"),
            confidence=ev.get("confidence", "medium"),
            note=(ev.get("note") or None),
            **fields,
        )
    valid_ev = {e.id for e in doc.evidence}
    for c in data.get("claims", []):
        evidence = [e for e in c.get("evidence", []) if e in valid_ev]
        doc.add_claim(
            c["id"],
            text=c["text"],
            evidence=evidence,
            decision=(c.get("decision") or None),
        )
    for f in data.get("findings", []):
        if f and f.strip():
            doc.add_finding(f)
    return doc


def _fields(ev: dict) -> dict[str, str]:
    """Accept either the schema's [{key,value},...] form or a plain {key: value}
    mapping, so a hand-authored or differently-shaped AI payload still works."""
    raw = ev.get("fields", [])
    if isinstance(raw, dict):
        return {k: str(v) for k, v in raw.items() if k}
    return {f["key"]: f["value"] for f in raw if isinstance(f, dict) and f.get("key")}
