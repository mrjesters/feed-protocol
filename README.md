# FEED — Format for Enforced Evidence-based Digestion

> Make any document tell the AI reading it: **here's what matters, here's the
> evidence, cite it or say you can't.**

FEED is a plain-text convention you embed in a document so that any LLM — Copilot,
ChatGPT, Claude, Gemini, a local model — grounds its answers in your evidence and
cites it by ID. No install, no plugin, no provider support, no prior knowledge of
FEED required on either side. It works on every model **today** because the
document teaches the rules inline.

It also has **teeth**: because evidence carries stable IDs and answers must cite
them, you can *mechanically verify* that an answer is actually grounded.

```
┌─ Header ──────────────────────────────────────────────┐
│ <!-- FEED:DOC version="0.2" grounding="strict" -->     │
│ > AI INGESTION NOTICE … ground answers, cite [E###] …  │  ← teaches any LLM the rules
├─ Tier 0: Claims & Decisions (front-loaded) ───────────┤  ← small-context-safe
├─ Tier 1: Findings (narrative, references [E001]) ─────┤
├─ Tier 2: Evidence (atomic key/value facts, IDs) ──────┤  ← the source of truth
└────────────────────────────────────────────────────────┘
```

## Why it exists

You generate AI reports and send them to people who paste them into their own AI.
Every hop loses fidelity — the reader's AI skims headings and riffs. FEED fixes
the **author** side of that loop: the document constrains how the downstream AI
reads and answers. Nothing else does this at the document level (`llms.txt` is
website-level and has no grounding contract; RAG/citation systems are all
retrieval-side, controlled by the AI, not the author).

## FEED is AI-to-AI (the library never needs its own API key)

The AI **already in your loop** — the one that wrote the report, your assistant, a
pipeline step — is what produces FEED. The library just renders, validates, and
verifies; it never calls an LLM of its own. Authoring is self-bootstrapping, the
same way ingestion is:

```
Reading side:   the document carries a notice that teaches any AI to ground & cite
Authoring side: an authoring prompt + schema teach any AI to emit FEED, then
                feed.build() renders it deterministically — no key, no network
```

### Primary flow: the AI emits FEED, you render it

```python
from feed import AUTHORING_PROMPT, FEED_JSON_SCHEMA, build

# 1. Hand AUTHORING_PROMPT + FEED_JSON_SCHEMA to whatever AI is already in your loop.
#    It returns structured JSON (no FEED tooling needed on the AI's side).
# 2. Render that JSON into a validated FEED document — pure Python, no API key:
doc = build(ai_json, grounding="strict", author="N. Gul")
doc.write("report.md")
```

Or entirely from the shell:

```bash
feed prompt > authoring-kit.txt        # the prompt + schema to give any AI
feed build ai_output.json -o report.md # render the AI's JSON into FEED (no key)
```

Manual additions are just edits: open `report.md` and add/adjust evidence and
claims by hand — it's plain markdown. `feed validate` checks it's still conformant.

> `feed tag draft.md` is an **optional** convenience that calls Claude directly,
> for when you have a plain document and *no* AI already in the loop. It is not the
> primary path and is the only thing that needs an API key.

## Quick start

### Build one in Python (manual / programmatic)

```python
from feed import FeedDocument

doc = FeedDocument("Q2 Pump Health Assessment", grounding="strict")
doc.add_evidence("E001", asset="XYZ-003", metric="vibration_rms",
                 value="12.4 mm/s",
                 threshold="11.2 mm/s (ISO 10816-3 Zone C)", confidence="high")
doc.add_claim("C1", "XYZ-003 needs intervention", evidence=["E001"],
              decision="Approve bearing replacement work order")

doc.write("report.md")    # clean markdown, FEED in HTML comments
doc.write("report.html")  # styled, opens in any browser
```

Your team opens `report.md` as a normal report. They upload it to whatever AI
they use → it reads the notice, sees the evidence, and answers grounded.

### Verify an answer was grounded (the teeth)

```python
from feed import FeedDocument, verify

doc = FeedDocument.read("report.md")
report = verify(ai_answer_text, doc)
print(report.passed)   # False if it cited evidence that doesn't exist,
                       # or (strict mode) didn't cite anything
```

### From the command line

```bash
feed prompt                                     # authoring kit for any AI (no key)
feed build ai_output.json -o report.md          # render an AI's JSON into FEED (no key)
feed validate report.md                         # is it well-formed FEED?
feed verify --doc report.md --answer answer.txt # is this answer grounded?
feed render report.md --to html -o report.html  # styled HTML
feed tag draft.md --grounding strict -o report.md  # OPTIONAL: auto-tag via Claude (needs key)
```

## What's in this repo

| Path | What it is |
|------|------------|
| `spec/feed-spec-v0.2.md` | The protocol definition (the constitution) |
| `feed/` | The reference library — build, render, validate, verify, auto-tag |
| `feed/verify.py` | The citation verifier — FEED's defensible edge, ~40 lines |
| `feed/cli.py` | The `feed` command-line tool |
| `examples/` | A complete worked example: a pump condition report (`.md` + `.html`) and the script that builds it |
| `templates/blank.feed.md` | A hand-authoring starter |
| `tests/` | Round-trip, validation, and verification tests |

## Install

```bash
pip install -e .            # library + CLI, zero dependencies
pip install -e ".[tagger]"  # adds the auto-tagger (needs anthropic + ANTHROPIC_API_KEY)
```

The core — authoring kit, build, render, validate, verify — is **pure Python with
no dependencies and never calls an LLM**. Only the optional `tag` convenience
calls Claude directly; it defaults to Claude Opus 4.8.

## The three primitives

- **Evidence** — atomic, ID'd, key/value facts. Never prose. The source of truth.
- **Claim** — a short statement grounded in evidence IDs, optionally a decision.
- **Header** — declares the grounding mode and carries the self-teaching notice.

Plus **grounding modes** (`strict` / `standard` / `open`) — the author's dial for
how strict the reading AI must be. In `strict`, no evidence means "Not supported
by this document."

## Status

v0.2 — spec + reference library + verifier + CLI + auto-tagger + worked example.
Deliberately out of scope for now: PDF/DOCX embedding, a hosted validator, and any
provider-native "FEED mode".

MIT licensed. Spec and tooling are open — adoption is the point.
