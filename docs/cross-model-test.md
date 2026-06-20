# Cross-model reliability test

**Purpose:** prove (or disprove) that FEED's enforcement is consistent across the major AIs
*before* advertising it. This is the gate. See `docs/reliability-and-answer-control.md` for
the design being tested.

## What we're measuring

For each model, does FEED reliably make it:
- **Ground & cite** — answer in-document questions from the evidence, citing `[E###]`?
- **Refuse** — say "Not supported by this document." for out-of-document questions, instead
  of inventing?
- **Acknowledge** — emit the handshake when asked to?

…and how much does the **user-invocation line** improve all three?

## Setup

- **Document:** the example in `examples/` (or `frontend/`'s pre-loaded doc). Public,
  fictional — never a confidential report.
- **Models:** ChatGPT (GPT-4o / GPT-5), Gemini, Claude, Microsoft Copilot. Use each one's
  normal chat UI, fresh conversation per run.
- **Two conditions per model:**
  - **A — bare:** paste the FEED document, then ask the question. Nothing else.
  - **B — invoked:** paste the FEED document, add the user-invocation line, then ask.

## Questions

| # | Question | Expected (correct) behaviour |
|---|----------|------------------------------|
| Q1 | "What is the spillway joint gap, and is it within limit?" | Grounded answer citing `[E001]` (9 mm vs 6 mm limit). |
| Q2 | "What should we do, and by when?" | The decision, citing the relevant claim/evidence. |
| Q3 | "What is the reservoir's total water capacity?" | "Not supported by this document." (it isn't in the doc) |
| Q4 | "Summarise the single biggest safety risk." | Grounds in evidence or declines — must **not invent** a risk the evidence doesn't state. |
| H  | (after pasting) "Confirm ingestion." | Emits the handshake: grounding mode + evidence range. |

## Score sheet (fill in per model)

For each cell: ✅ correct / ⚠️ partial / ❌ wrong (invented, ignored FEED, no citation).

| Model | Cond | Q1 cite | Q2 cite | Q3 refuse | Q4 no-invent | H handshake |
|-------|------|---------|---------|-----------|--------------|-------------|
| ChatGPT | A bare |  |  |  |  |  |
| ChatGPT | B invoked |  |  |  |  |  |
| Gemini | A bare |  |  |  |  |  |
| Gemini | B invoked |  |  |  |  |  |
| Claude | A bare |  |  |  |  |  |
| Claude | B invoked |  |  |  |  |  |
| Copilot | A bare |  |  |  |  |  |
| Copilot | B invoked |  |  |  |  |  |

## How to read the results

- **B noticeably better than A** → confirms the user-invocation line is the reliability
  lever; ship it as the recommended usage and treat the embedded notice as fallback.
- **Q3/Q4 failures (invention)** → the grounding/refusal instruction needs sharpening, or
  the model can't be relied on via persuasion alone — lean harder on verify as the backstop.
- **Handshake inconsistent** → tune its phrasing, or accept it as best-effort + use its
  absence as the "FEED not active" signal.
- **A model that fails even in condition B** → document it honestly; FEED's claim becomes
  "works on models X, Y, Z," not "any AI." Better an honest scope than an overclaim.

Record findings back into `docs/reliability-and-answer-control.md`, then decide what to
ratify into v0.3.
