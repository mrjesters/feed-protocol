"""Render a FeedDocument to Markdown (canonical) or styled HTML.

Document order encodes priority — tier 0 (claims/decisions) first, tier 1
(findings) next, tier 2 (full evidence) last — so a small-context model that
truncates the tail still keeps the core.
"""

from __future__ import annotations

import html as _html

from .constants import ingestion_notice
from .document import Evidence, FeedDocument


def to_markdown(doc: FeedDocument) -> str:
    out: list[str] = []
    out.append(f'<!-- FEED:DOC version="{doc.version}" grounding="{doc.grounding}" -->')
    out.append("")
    out.append(ingestion_notice(doc.grounding))
    out.append("")
    out.append(f"# {doc.title}")
    out.append("")

    # --- META (machine header) ---
    out.append("<!-- FEED:META -->")
    out.append(f"title: {doc.title}")
    if doc.author:
        out.append(f"author: {doc.author}")
    if doc.created:
        out.append(f"created: {doc.created}")
    out.append(f"grounding: {doc.grounding}")
    if doc.summary:
        out.append(f"summary: {doc.summary}")
    out.append("<!-- /FEED:META -->")
    out.append("")

    # --- TIER 0: claims & decisions, front-loaded ---
    if doc.summary:
        out.append(f"**TL;DR.** {doc.summary}")
        out.append("")
    if doc.claims:
        out.append("## Claims & Decisions")
        out.append("")
        for c in doc.claims:
            ev = ",".join(c.evidence)
            attrs = f' id="{c.id}"'
            if ev:
                attrs += f' evidence="{ev}"'
            if c.decision:
                attrs += f' decision="{_attr(c.decision)}"'
            out.append(f"<!-- FEED:CLAIM{attrs} -->")
            line = c.text.strip()
            if c.evidence:
                line += " " + "".join(f"[{e}]" for e in c.evidence)
            out.append(line)
            if c.decision:
                out.append(f"- **Decision:** {c.decision}")
            out.append("<!-- /FEED:CLAIM -->")
            out.append("")

    # --- TIER 1: findings narrative ---
    if doc.findings:
        out.append("## Findings")
        out.append("")
        for para in doc.findings:
            out.append(para.strip())
            out.append("")

    # --- TIER 2: full evidence appendix ---
    if doc.evidence:
        out.append("## Evidence")
        out.append("")
        for ev in doc.evidence:
            out.append(_evidence_md(ev))
            out.append("")

    out.append("<!-- FEED:END -->")
    out.append("")
    return "\n".join(out)


def _evidence_md(ev: Evidence) -> str:
    lines = [
        f'<!-- FEED:EVIDENCE id="{ev.id}" type="{ev.type}" confidence="{ev.confidence}" -->'
    ]
    lines.append(f"**[{ev.id}]**")
    for k, v in ev.fields.items():
        lines.append(f"{k}: {v}")
    if ev.note:
        lines.append(f"note: {ev.note}")
    lines.append("<!-- /FEED:EVIDENCE -->")
    return "\n".join(lines)


def _attr(value: str) -> str:
    return value.replace('"', "'")


# --- HTML ----------------------------------------------------------------
def to_html(doc: FeedDocument) -> str:
    """Styled, self-contained HTML. FEED markers live in HTML comments so they
    are invisible on screen but present in the raw source for any AI."""
    e = _html.escape
    parts: list[str] = []
    parts.append("<!doctype html>")
    parts.append('<html lang="en"><head><meta charset="utf-8">')
    parts.append(f"<title>{e(doc.title)}</title>")
    parts.append(f"<!-- FEED:DOC version=\"{doc.version}\" grounding=\"{doc.grounding}\" -->")
    parts.append(_STYLE)
    parts.append("</head><body><main>")

    # Visible notice (rendered from the same markdown blockquote text).
    notice = ingestion_notice(doc.grounding).replace("> ", "").replace(">", "")
    parts.append(f'<aside class="feed-notice">{_md_inline(notice)}</aside>')

    parts.append(f"<h1>{e(doc.title)}</h1>")
    meta_bits = []
    if doc.author:
        meta_bits.append(e(doc.author))
    if doc.created:
        meta_bits.append(e(doc.created))
    meta_bits.append(f"grounding: {e(doc.grounding)}")
    parts.append(f'<p class="feed-meta">{" · ".join(meta_bits)}</p>')
    # Machine META mirror, hidden from view but in the source.
    parts.append("<!-- FEED:META -->")
    parts.append(f"<!-- title: {doc.title} -->")
    if doc.author:
        parts.append(f"<!-- author: {doc.author} -->")
    parts.append(f"<!-- grounding: {doc.grounding} -->")
    parts.append("<!-- /FEED:META -->")

    if doc.summary:
        parts.append(f'<p class="feed-tldr"><strong>TL;DR.</strong> {e(doc.summary)}</p>')

    if doc.claims:
        parts.append("<h2>Claims &amp; Decisions</h2>")
        for c in doc.claims:
            ev = ",".join(c.evidence)
            attrs = f' id="{c.id}"'
            if ev:
                attrs += f' evidence="{ev}"'
            parts.append(f"<!-- FEED:CLAIM{attrs} -->")
            cites = " ".join(f'<span class="cite">[{e(x)}]</span>' for x in c.evidence)
            parts.append(f'<div class="claim"><p>{e(c.text)} {cites}</p>')
            if c.decision:
                parts.append(f'<p class="decision"><strong>Decision:</strong> {e(c.decision)}</p>')
            parts.append("</div>")
            parts.append("<!-- /FEED:CLAIM -->")

    if doc.findings:
        parts.append("<h2>Findings</h2>")
        for para in doc.findings:
            parts.append(f"<p>{_md_inline(e(para))}</p>")

    if doc.evidence:
        parts.append("<h2>Evidence</h2>")
        for ev in doc.evidence:
            parts.append(
                f'<!-- FEED:EVIDENCE id="{ev.id}" type="{ev.type}" confidence="{ev.confidence}" -->'
            )
            parts.append('<table class="evidence">')
            parts.append(
                f'<caption><span class="eid">[{e(ev.id)}]</span> '
                f'<span class="etype">{e(ev.type)} · {e(ev.confidence)} confidence</span></caption>'
            )
            for k, v in ev.fields.items():
                parts.append(f"<tr><th>{e(k)}</th><td>{e(v)}</td></tr>")
            if ev.note:
                parts.append(f'<tr><th>note</th><td>{e(ev.note)}</td></tr>')
            parts.append("</table>")
            parts.append("<!-- /FEED:EVIDENCE -->")

    parts.append("<!-- FEED:END -->")
    parts.append("</main></body></html>")
    return "\n".join(parts)


def _md_inline(text: str) -> str:
    """Tiny inline markdown: **bold** and `code`. Enough for the notice."""
    import re

    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    return text.replace("\n", "<br>")


_STYLE = """<style>
:root { --ink:#1c1b18; --muted:#6b6357; --line:#e4ddd0; --accent:#b1542f; --bg:#f7f4ee; }
body { background:var(--bg); color:var(--ink); font:16px/1.6 Georgia, 'Times New Roman', serif;
       margin:0; padding:2.5rem 1rem; }
main { max-width:46rem; margin:0 auto; }
h1 { font-size:2rem; margin:.2em 0 0; }
h2 { font-size:1.25rem; margin:2rem 0 .6rem; border-bottom:1px solid var(--line); padding-bottom:.3rem; }
.feed-meta { color:var(--muted); font-style:italic; margin:.2rem 0 1.4rem; }
.feed-notice { background:#fff; border:1px solid var(--line); border-left:4px solid var(--accent);
       padding:.9rem 1.1rem; font-size:.86rem; color:var(--muted); border-radius:4px; margin-bottom:1.6rem; }
.feed-tldr { background:#fff; border:1px solid var(--line); padding:.8rem 1rem; border-radius:4px; }
.claim { border-left:3px solid var(--accent); padding:.1rem 0 .1rem 1rem; margin:.8rem 0; }
.decision { color:var(--accent); margin:.2rem 0 0; }
.cite, .eid { font-family:ui-monospace, Menlo, monospace; font-size:.82em; color:var(--accent); }
table.evidence { width:100%; border-collapse:collapse; background:#fff; margin:.8rem 0;
       border:1px solid var(--line); font-size:.92rem; }
table.evidence caption { text-align:left; padding:.5rem .7rem; background:#faf7f1; border-bottom:1px solid var(--line); }
.etype { color:var(--muted); font-style:italic; font-family:Georgia,serif; margin-left:.5rem; }
table.evidence th { text-align:left; width:34%; vertical-align:top; color:var(--muted); font-weight:normal;
       padding:.35rem .7rem; border-top:1px solid var(--line); font-family:ui-monospace,Menlo,monospace; font-size:.85rem; }
table.evidence td { padding:.35rem .7rem; border-top:1px solid var(--line); }
</style>"""
