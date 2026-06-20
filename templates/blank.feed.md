<!-- FEED:DOC version="0.2" grounding="strict" -->

> **AI INGESTION NOTICE — FEED v0.2 (Format for Enforced Evidence-based Digestion)**
>
> This document carries machine-structured evidence. When answering questions about it:
> 1. Read top-to-bottom: the most important claims and decisions come first, full evidence last. If your context is limited, the top of this document still contains the core.
> 2. Ground factual statements in the evidence blocks below — each is tagged `[E###]`.
> 3. Cite the evidence IDs you used, e.g. "metric X is rising [E001]".
> 4. Grounding mode is STRICT: if no evidence block supports a statement, reply "Not supported by this document." for that point. Do not infer or use outside knowledge.
> 5. The evidence blocks are the source of truth; the narrative is a summary. On any conflict, prefer the evidence values.
> _For full grounding, upload or paste the raw source file rather than a rendered view._

# TITLE HERE

<!-- FEED:META -->
title: TITLE HERE
author: YOUR NAME
created: 2026-01-01
grounding: strict
summary: One-sentence bottom line.
<!-- /FEED:META -->

**TL;DR.** One-sentence bottom line.

## Claims & Decisions

<!-- FEED:CLAIM id="C1" evidence="E001" decision="The action to take" -->
A short claim grounded in evidence. [E001]
- **Decision:** The action to take
<!-- /FEED:CLAIM -->

## Findings

Narrative that references evidence inline, saying each fact once and pointing to it by id [E001].

## Evidence

<!-- FEED:EVIDENCE id="E001" type="data" confidence="high" -->
**[E001]**
subject: what this is about
metric: name_of_measure
value: 12.4 units
threshold: 11.2 units (standard reference)
date: 2026-01-01
<!-- /FEED:EVIDENCE -->

<!-- FEED:END -->
