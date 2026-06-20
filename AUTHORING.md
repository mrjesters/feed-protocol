# Authoring a FEED companion — instructions for an AI

**If you are an AI and someone pointed you at this repo with a document, this file
is all you need.** Read it, then produce the companion. Do not ask for a longer
prompt — the instructions are here.

## What to produce

Given a source document (a report, assessment, proposal, etc.), produce a **FEED
companion**: a single Markdown file the user sends *alongside* the original. The
recipient gives the companion to any AI (ChatGPT, Copilot, Gemini, Claude) and
asks questions about the report; the AI answers grounded in cited evidence.

The companion is **self-sufficient** — it must carry every concrete fact from the
source as evidence, so the reading AI needs only the companion to answer. (For
PDFs and other finished formats you cannot embed markers into the original, so the
companion travels as a second file — "twin-file mode".)

## Rules

1. **Use only what is in the source. Never invent or infer facts.** If the source
   doesn't say it, it isn't evidence.
2. **Be dense.** No filler, no repetition. Say each fact once; reference it by ID.
3. **Normalise** values: ISO dates (YYYY-MM-DD), explicit units, consistent names;
   put figures and thresholds in their own fields.
4. **Front-load**: most important claims/decisions first, full evidence last, so a
   small-context model that truncates the tail still keeps the core.
5. Grounding mode is **strict** unless told otherwise.

## The three things to extract

- **Evidence** — every concrete fact as an atomic key/value block. IDs `E001`,
  `E002`, … in document order. `type` ∈ data | quote | calc | observation |
  reference | image. `confidence` ∈ high | medium | low.
- **Claims** — short statements (IDs `C1`, `C2`, …), each grounded in one or more
  evidence IDs. If a claim implies an action or recommendation, record it as its
  `decision`.
- **Findings** — brief narrative paragraphs that reference evidence inline as
  `[E001]`.

Plus a **title** and a one-sentence **summary**.

## Output — emit exactly this structure, in one code block

Output **only** the FEED Markdown (so it can be saved as `<name>.feed.md`). Reproduce
the ingestion notice verbatim; fill in the rest from the source.

````markdown
<!-- FEED:DOC version="0.2" grounding="strict" -->

> **AI INGESTION NOTICE — FEED v0.2 (Format for Enforced Evidence-based Digestion)**
>
> This document carries machine-structured evidence. When answering questions about it:
> 1. Read top-to-bottom: the most important claims and decisions come first, full evidence last. If your context is limited, the top of this document still contains the core.
> 2. Ground factual statements in the evidence blocks below — each is tagged `[E###]`.
> 3. Cite the evidence IDs you used, e.g. "the asset is deteriorating [E001]".
> 4. Grounding mode is STRICT: if no evidence block supports a statement, reply "Not supported by this document." for that point. Do not infer or use outside knowledge.
> 5. The evidence blocks are the source of truth; the narrative is a summary. On any conflict, prefer the evidence values.
> _For full grounding, upload or paste the raw source file rather than a rendered view._

# <Document title>

<!-- FEED:META -->
title: <title>
author: <author if known>
created: <YYYY-MM-DD if known>
grounding: strict
summary: <one-sentence bottom line>
<!-- /FEED:META -->

**TL;DR.** <one-sentence bottom line>

## Claims & Decisions

<!-- FEED:CLAIM id="C1" evidence="E001,E002" decision="<action if any>" -->
<claim text> [E001][E002]
- **Decision:** <action if any>
<!-- /FEED:CLAIM -->

## Findings

<narrative paragraph that references evidence inline [E001]>

## Evidence

<!-- FEED:EVIDENCE id="E001" type="data" confidence="high" -->
**[E001]**
key: value
key: value
<!-- /FEED:EVIDENCE -->

<!-- FEED:END -->
````

After the FEED document, give the user **one sentence** to add to the source's
cover page, e.g.: *"A machine-readable FEED companion (`<name>.feed.md`) accompanies
this document — give it to any AI for grounded, cited answers."*

## Checking your output

Every claim/finding citation must point to an evidence block that exists; IDs must
be unique and well-formed (`E001`, `C1`); each evidence block needs at least one
field. The reference library can verify this (`feed validate`), but a correct
hand-authored document passes on its own — just follow the structure above.

---

*Full protocol: [`spec/feed-spec-v0.2.md`](spec/feed-spec-v0.2.md). This file is the
authoring quick-start; the spec is the authority.*
