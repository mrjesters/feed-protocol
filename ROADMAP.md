# FEED Roadmap

Proposals under consideration for future versions. **Nothing on this page is part
of the ratified spec** (`spec/feed-spec-v0.2.md`) until it is moved there and the
spec version is bumped. These are captured to show direction and invite feedback.

> **Active refinement (pre-v0.3).** Before any of this is ratified or advertised, the
> priority is making FEED's enforcement *consistent across models*. Design draft:
> [`docs/reliability-and-answer-control.md`](docs/reliability-and-answer-control.md);
> the gating cross-model test: [`docs/cross-model-test.md`](docs/cross-model-test.md). The
> handshake below is being folded into that work.

---

## Proposed for v0.3 — Ingestion handshake (read-receipt)

**Status: proposed, not ratified. Backward-compatible.**

### Problem

FEED currently gives no signal at *ingestion time*. You paste a document (or its
FEED twin) into an AI and have to *trust* it honoured the notice. This matters
most in **twin-file** delivery (see spec §9, *Delivery models*): the recipient may
feed their AI only the human report and get ungrounded answers, with no indication
the FEED layer was missed. Markers stripped by a rendered copy fail the same way,
silently.

### Proposal

The ingestion notice gains a step-zero instruction: **before answering anything,
the reading AI emits a standard handshake line** confirming it ingested the FEED
layer. The user sees it and knows grounding is active.

To make it un-fakeable it is **proof-of-read** — the AI must echo content it could
only produce by parsing the structure: the grounding mode, the evidence **count
and ID range**, and the TL;DR. Example:

```
✅ FEED v0.2 ingested — grounding: strict — 6 evidence (E001–E006), 3 claims.
   Answers will be grounded and cited.
```

The **negative case is the point** — absence must be loud, not silent:

```
⚠️ No FEED structure detected — answers will NOT be grounded or cited.
   (Was the FEED layer attached, or stripped by a rendered copy?)
```

### Extensions (open questions)

- **Author canary.** An author-planted token near the document's end that the
  handshake must echo — proving the AI read the *whole* document, not just the
  front-loaded top. Strongest completeness signal; small authoring cost. In or
  out by default?
- **Machine-parseable form.** A fixed grammar (e.g.
  `FEED-ACK v0.2 grounding=strict evidence=E001-E006 claims=3`) so tooling — a
  `feed handshake-check` — can verify the AI reported the right grounding and ID
  range, turning the receipt into a checkable gate in a pipeline. Trade-off:
  machine-checkability vs. not making the AI sound robotic.
- **Suppressible / quiet mode.** A visible line is helpful in a chat UI but noise
  in an automated pipeline (where the machine form alone suffices).

### Relationship to `feed verify`

The handshake confirms **ingestion** ("did the AI load the FEED layer?"). It does
**not** prove every later answer is grounded — that remains the job of
`feed verify`, which checks a specific answer's citations. The two are
complementary: handshake = receipt at the door; verify = spot-check on an answer.

---

## Proposed — In-place annotation ("tag mode")

**Status: proposed, not ratified.**

Today the library *regenerates* a FEED-native document from structured data. A
complementary capability would **annotate an existing Markdown/HTML report in
place** — inserting evidence/claim markers as invisible comments into the author's
real document — so the embed-mode "one file for both audiences" workflow needs no
rewrite of the source. (Does not apply to PDF; see spec §9.)

---

## Out of scope (for now)

PDF/DOCX marker embedding (the format reality makes twin-file the answer — see
spec §9), a hosted validator, and any provider-native "FEED mode".
