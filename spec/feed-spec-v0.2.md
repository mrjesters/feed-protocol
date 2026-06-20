# FEED — Format for Enforced Evidence-based Digestion

**Specification v0.2**

FEED is a plain-text convention you embed in a document so that any AI reading it
(a) gets the core facts first, (b) cannot skim past the evidence, and (c) is
instructed to answer only from that evidence and cite it by ID — with **no
install, plugin, or prior knowledge of FEED required on either side**.

This document is the constitution: everything in the reference library conforms
to it. You can also hand-author FEED documents from this spec alone.

---

## 1. Design goals (why it is shaped this way)

1. **Works on every LLM today.** The rules are taught *inside* the document
   (§4), so a model that has never heard of FEED still follows them. No
   ecosystem buy-in, no provider "FEED mode" required.
2. **Survives small context windows.** Document order encodes priority (§3): a
   model that truncates the tail still keeps the core.
3. **Has teeth.** Stable evidence IDs + a citation contract make answers
   *mechanically verifiable* (§7) — the property that distinguishes FEED from
   "AI-friendly formatting".
4. **Invisible to humans, present for machines.** The grammar lives in HTML
   comments (§5): invisible in any renderer, readable in the raw source.
5. **Low friction.** One markdown file. No software needed to read or write one.

---

## 2. The three primitives

| Primitive    | What it is | Role |
|--------------|------------|------|
| **Header**   | Document-level marker + metadata + the visible ingestion notice | Declares version & grounding mode, teaches the rules |
| **Evidence** | An atomic, ID'd, key/value fact | The source of truth |
| **Claim**    | A narrative statement that references evidence by ID | What the author asserts/decides |

Narrative **Findings** (ordinary prose that references evidence inline as
`[E001]`) are also supported but are not a load-bearing primitive — they are
tier-1 connective tissue.

---

## 3. Document order = priority (tiers)

A FEED document is ordered most-critical-first. A reader processing top-to-bottom
gets the most important content even if it stops early.

```
Header  (DOC marker + ingestion notice + META)
Tier 0  TL;DR + Claims & Decisions          ← fits ~2–4K tokens
Tier 1  Findings (narrative)                 ← ~16K
Tier 2  Evidence appendix (full key/values)  ← everything
END marker
```

There is no separate "manifest / skeleton / full" document — the single
document's *layout* delivers the same progressive disclosure.

---

## 4. The ingestion notice (self-bootstrapping)

Immediately after the `DOC` marker, a **visible markdown blockquote** teaches the
reading AI the rules in ~150 tokens. This is the heart of FEED's portability —
it is why a never-seen-FEED model complies, and why the copy-paste path works
(the notice survives copy out of a rendered view).

It MUST instruct the reader to:

1. read top-to-bottom (core first);
2. ground statements in the `[E###]` evidence;
3. cite the evidence IDs used;
4. obey the grounding mode (§6);
5. treat evidence as the source of truth on any conflict.

The reference library generates this text from the grounding mode; see
`feed/constants.py:ingestion_notice`.

---

## 5. Grammar (markers)

All structural markers are HTML comments — invisible when rendered, present in
raw source.

| Marker | Form |
|--------|------|
| Document | `<!-- FEED:DOC version="0.2" grounding="strict" -->` (single line, no body) |
| Metadata | `<!-- FEED:META -->` … `key: value` lines … `<!-- /FEED:META -->` |
| Claim | `<!-- FEED:CLAIM id="C1" evidence="E001,E002" decision="…" -->` … text … `<!-- /FEED:CLAIM -->` |
| Evidence | `<!-- FEED:EVIDENCE id="E001" type="data" confidence="high" -->` … `key: value` lines … `<!-- /FEED:EVIDENCE -->` |
| End | `<!-- FEED:END -->` |

**Attributes** are `name="value"` pairs. **IDs**: evidence is `E` + 1–4 digits
(`E001`); claims are `C` + 1–4 digits (`C1`). IDs MUST be unique within a
document.

For the copy-paste path, the visible ingestion notice (§4) is the fallback that
carries the instructions when the comments are stripped by a rendered copy.

### Evidence block

- Body is **key/value lines only** (`key: value`), never prose.
- `type` ∈ `data | quote | calc | observation | reference | image`.
- `confidence` ∈ `high | medium | low`.
- Values SHOULD be normalised: ISO-8601 dates, explicit units, consistent names,
  and thresholds/baselines as their own fields. This is what lets a reader
  compare values across blocks without parsing natural language.
- An evidence block MUST have at least one field.

### Claim block

- Body is one short statement; it MAY end with inline `[E###]` citations.
- `evidence` attribute lists the evidence IDs it rests on (comma-separated).
- Optional `decision` attribute (or a `- **Decision:** …` body line) records the
  action implied by the claim.
- Every ID in `evidence` MUST exist as an evidence block.

---

## 6. Grounding modes (the author's dial)

Declared once in the `DOC` marker; restated in the notice.

| Mode | Contract on the reading AI |
|------|----------------------------|
| `strict` | No supporting evidence → "Not supported by this document." No inference, no outside knowledge. |
| `standard` | Cite where evidence exists; explicitly label anything beyond it as inference. |
| `open` | Ground and cite where possible; free reasoning permitted. |

---

## 7. The citation contract & verification (the teeth)

Because every evidence block has a **stable plain-text ID** and answers must
**cite by ID**, an answer can be checked mechanically — no model required:

- **Resolvable** — every `[E###]` the answer cites exists in the document.
  An invented citation is a hard failure.
- **Present** — in `strict` mode an answer with zero citations fails.
- **Corroborated** (advisory) — for each cited block, a distinctive value
  (e.g. a number) from that block appears in the answer.

The reference implementation is `feed/verify.py` (≈40 lines). This is the
property `llms.txt` and RAG-formatting have no equivalent for.

Verification does **not** require running the document through an LLM; it is a
plain-text check you can run in CI on a saved answer.

---

## 8. Authoring rules (the other half of the contract)

A FEED document is only as good as the discipline of the side that *writes* it.
A compliant document MUST:

- put evidence in **structured key/value form**, not paragraphs;
- **say each fact once** and reference it by ID rather than repeating it;
- avoid filler ("it is worth noting that", "as previously mentioned");
- use **normalised formats** (ISO dates, units, consistent names);
- order content most-critical-first (§3).

The reference library enforces the structural parts: `add_evidence()` rejects
empty/duplicate/ malformed blocks, and `add_claim()` rejects references to
evidence that does not exist — so a pipeline *cannot* emit a structurally
inconsistent document.

### Self-bootstrapping authoring (no LLM credentials in the tooling)

FEED is an AI-to-AI protocol. The AI already in the loop authors FEED — the
tooling never needs its own LLM key. The authoring side is portable in exactly
the way the ingestion notice (§4) is:

- A reusable **authoring prompt** + **JSON schema** are handed to whatever AI is
  in the pipeline; it returns structured FEED data. (Reference:
  `feed.authoring.AUTHORING_PROMPT` and `FEED_JSON_SCHEMA`; `feed prompt` emits
  both.)
- A deterministic, dependency-free **builder** renders that data into a validated
  document — no network, no key. (Reference: `feed.authoring.build`; `feed build`
  on the CLI.) The builder is resilient to imperfect model output: claim
  references to non-existent evidence are dropped and fieldless evidence is
  skipped, so a slightly-off response still yields a conformant document.
- **Manual additions** are ordinary markdown edits to the rendered file;
  `feed validate` re-checks conformance.

A direct API tagger (`feed.tagger`) is provided only as a convenience for when no
AI is already in the loop. It uses the same prompt and schema; it is not the
primary path and is the only component that requires API credentials.

---

## 9. Delivery formats

- **Markdown** is canonical — lowest friction, renders cleanly everywhere,
  comments invisible.
- **HTML** is a styled delivery format with the same markers in comments.
- **PDF / DOCX**: out of scope for v0.2 (a tooling concern, not a protocol one).
  A future version may define XMP/custom-XML embedding.

Two ingestion paths:

1. **File upload (ideal).** The AI reads the raw source and sees all markers.
2. **Copy-paste (fallback).** Markers may be stripped, but the visible
   ingestion notice still carries the instructions.

Explicitly out of scope: white-text, hidden layers, steganography — fragile and
dishonest. FEED is transparent; the tags are present in the source, just
visually quiet.

---

## 10. Conformance

A **conformant FEED document**:

- begins with a `DOC` marker carrying `version` and a valid `grounding`;
- includes the visible ingestion notice;
- has unique, well-formed evidence and claim IDs;
- has at least one field per evidence block;
- has every claim/finding citation resolving to a real evidence block.

A **conformant FEED tool** preserves IDs and structure across read/write and
implements the §7 verification semantics.

Run `feed validate <file>` for the structural checks and `feed verify --doc
<file> --answer <answer>` for the citation contract.

---

*FEED v0.2 — spec and reference implementation released under the MIT License.*
