"""Optional convenience: auto-tag a plain document into FEED by calling Claude.

THIS IS NOT THE PRIMARY PATH. FEED is AI-to-AI — normally the AI already in your
loop emits FEED natively using `feed.authoring.AUTHORING_PROMPT` +
`FEED_JSON_SCHEMA`, and you render it with `feed.authoring.build()` (no API key).

This module exists only for the case where you have a plain document and *no* AI
already in the loop, and want a one-shot CLI. It needs the `anthropic` package and
an ANTHROPIC_API_KEY (`pip install feed-protocol[tagger]`). Defaults to Opus 4.8.
"""

from __future__ import annotations

import json

from .authoring import AUTHORING_PROMPT, FEED_JSON_SCHEMA, build
from .document import FeedDocument

DEFAULT_MODEL = "claude-opus-4-8"


def auto_tag(
    text: str,
    title: str | None = None,
    author: str | None = None,
    grounding: str = "strict",
    created: str | None = None,
    model: str = DEFAULT_MODEL,
) -> FeedDocument:
    """Read a plain document and return a FeedDocument, using Claude to extract the
    structure. Raises if `anthropic` is missing or no API key is configured.

    Note this reuses the exact same portable prompt and schema any other AI would
    use — the API call is just one way to drive it."""
    try:
        import anthropic
    except ImportError as exc:  # pragma: no cover - environment dependent
        raise RuntimeError(
            "The auto-tagger needs the anthropic package. Install with: "
            "pip install feed-protocol[tagger]. (Or skip it: have the AI already "
            "in your pipeline emit FEED JSON using feed.authoring, then feed.build.)"
        ) from exc

    client = anthropic.Anthropic()
    instruction = "Convert the following document into FEED structure."
    if title:
        instruction += f' Use the title "{title}".'

    response = client.messages.create(
        model=model,
        max_tokens=16000,
        system=AUTHORING_PROMPT,
        output_config={"format": {"type": "json_schema", "schema": FEED_JSON_SCHEMA}},
        messages=[{"role": "user", "content": f"{instruction}\n\n---\n\n{text}"}],
    )
    raw = next(b.text for b in response.content if b.type == "text")
    data = json.loads(raw)
    return build(data, title=title, author=author, grounding=grounding, created=created)
