# FEED eval & refinement harness

Automated, no-manual-pasting environment for proving and refining FEED's cross-model
consistency. Scoring is mechanical (the real `feed.verify`), so it's reproducible and
needs no human judge.

```
suite.py       the document, notice variants, user-invocation line, questions + expectations
providers.py   one ask() over OpenAI / Anthropic / Gemini, plus a `mock` (offline) provider
score.py       grades an answer with feed.verify + a handshake check
run.py         runs the matrix (provider × variant × condition × question × repeats) → scorecard
refine.py      autonomous loop: propose a better notice from failures, keep it if it scores higher
results/       JSON transcripts + Markdown scorecards + refine log
```

## Setup

```bash
cd eval
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt          # provider SDKs you need
cp .env.example .env                      # add the keys you have
```

## Run it

**Offline (no keys) — proves the pipeline:**
```bash
python run.py --provider mock
```

**Real cross-model test:**
```bash
python run.py --provider openai,anthropic,gemini --repeats 5
```
Produces `results/run_<providers>.md` — pass-rate per provider × notice variant × condition,
plus every failure with the model's actual answer.

**Autonomous refinement (the agent improving the notice):**
```bash
python refine.py --test-provider openai,anthropic --generations 4
```
It proposes notice variants from the failures, tests each, hill-climbs to the best, and
**prints the winning notice for you to ratify**. It writes nothing to the spec.

## What it tests

- **ground_cite** — in-doc questions: answer from evidence, cite `[E###]`.
- **refuse** — out-of-doc questions: "Not supported by this document." (no invention).
- **no_invent** — must ground or refuse; never fabricate.
- **handshake** — emits the ingestion acknowledgement.
- ×2 conditions: **bare** (document only) vs **invoked** (with the user-invocation line) —
  this measures how much the trusted-channel invocation improves consistency.

## Guardrails (read these)

- **Repeats** ≥ 3 — models are stochastic; judge pass-*rate*, not single rolls.
- **Overfitting** — the suite is small. A notice that wins here must be re-checked on fresh
  questions/documents before it's ratified into the spec.
- **The agent only proposes; you ratify.** `refine.py` changes only the notice text and
  writes nothing to the spec — the winning notice is printed for human sign-off.
- **Budget** — uses cheap models and capped `max_tokens`; bound `--repeats`/`--generations`.

The example document is fictional. Never put a real or confidential report in `suite.py`.
