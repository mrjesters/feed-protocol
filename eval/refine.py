"""Autonomous refinement loop — the "agent refines the protocol" engine.

It proposes a better ingestion-notice variant from the observed failures, tests it across
the configured models, and keeps it only if the pass-rate goes up (hill-climb). Runs
unattended; logs every generation.

    python eval/refine.py --test-provider openai,anthropic --generations 4

GUARDRAILS (deliberate):
- It only changes the NOTICE text — never the evidence/claims (can't game grounding).
- It optimises pass-rate over the suite; treat the suite as small — risk of overfitting is
  real, so a winning notice must be re-checked on fresh questions before ratifying.
- It writes NOTHING to the spec. The winning notice is printed + logged for YOU to ratify.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))

import providers  # noqa: E402
import score as scorer  # noqa: E402
import suite  # noqa: E402

PROPOSER_MODEL = os.getenv("FEED_EVAL_PROPOSER_MODEL", "gpt-4o-mini")


def assemble_raw(notice: str) -> str:
    return f"{suite.DOC_HEADER}\n\n{notice}\n\n{suite.DOC_BODY}"


def evaluate(notice: str, test_providers, conditions, repeats):
    """Return (pass_rate, failures) for a candidate notice."""
    doc = assemble_raw(notice)
    total = passed = 0
    failures = []
    for provider in test_providers:
        for condition in conditions:
            for q in suite.QUESTIONS:
                for _ in range(repeats):
                    content = suite.user_message(doc, q["text"], condition)
                    try:
                        answer = providers.ask(provider, content)
                    except Exception as e:
                        answer = ""
                        failures.append(f"{provider}/{condition}/{q['id']}: call error {e}")
                        total += 1
                        continue
                    ok, detail = scorer.score(answer, doc, q["expect"])
                    total += 1
                    passed += 1 if ok else 0
                    if not ok:
                        failures.append(f"{provider}/{condition}/{q['id']} ({q['expect']}): "
                                        f"{detail} :: {answer[:120].strip()}")
    return (passed / total if total else 0.0), failures


def propose(current_notice: str, failures) -> str:
    """Ask an LLM to rewrite the notice to fix the failures. Returns the new notice text."""
    from openai import OpenAI
    client = OpenAI()
    digest = "\n".join(f"- {f}" for f in failures[:40]) or "(no failures)"
    prompt = (
        "You are improving the AI INGESTION NOTICE of the FEED protocol — a short instruction "
        "block embedded in a document that should make any AI ground its answers in the "
        "document's [E###] evidence, cite the IDs, and reply 'Not supported by this document.' "
        "for anything unsupported.\n\n"
        "CURRENT NOTICE:\n" + current_notice + "\n\n"
        "MODELS FAILED IN THESE WAYS:\n" + digest + "\n\n"
        "Rewrite the notice to maximise compliance across different AI models. Keep it short "
        "(under ~140 words), imperative, and clearly framed as instructions to follow rather "
        "than content to summarise. Output ONLY the new notice as markdown blockquote lines "
        "(each line starting with '> '). Do not invent facts or change the document's data."
    )
    r = client.chat.completions.create(
        model=PROPOSER_MODEL, max_tokens=400, temperature=0.7,
        messages=[{"role": "user", "content": prompt}],
    )
    text = (r.choices[0].message.content or "").strip()
    # keep only blockquote lines
    lines = [ln for ln in text.splitlines() if ln.strip().startswith(">")]
    return "\n".join(lines) if lines else text


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--test-provider", default="openai", help="comma-separated models to test against")
    ap.add_argument("--start", default="strengthened", help="starting notice variant key")
    ap.add_argument("--condition", default=",".join(suite.CONDITIONS))
    ap.add_argument("--repeats", type=int, default=3)
    ap.add_argument("--generations", type=int, default=4)
    args = ap.parse_args()

    test_providers = [p.strip() for p in args.test_provider.split(",") if p.strip()]
    conditions = [c.strip() for c in args.condition.split(",") if c.strip()]

    best = suite.NOTICE_VARIANTS[args.start]
    best_score, fails = evaluate(best, test_providers, conditions, args.repeats)
    print(f"gen 0 (start='{args.start}'): pass-rate {best_score:.0%}  ({len(fails)} failures)")
    log = [{"gen": 0, "score": best_score, "notice": best, "accepted": True}]

    for g in range(1, args.generations + 1):
        candidate = propose(best, fails)
        cand_score, cand_fails = evaluate(candidate, test_providers, conditions, args.repeats)
        accept = cand_score > best_score
        print(f"gen {g}: candidate pass-rate {cand_score:.0%}  -> {'ACCEPT' if accept else 'reject'}")
        log.append({"gen": g, "score": cand_score, "notice": candidate, "accepted": accept})
        if accept:
            best, best_score, fails = candidate, cand_score, cand_fails

    out = os.path.join(HERE, "results", "refine_log.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(log, f, indent=2, ensure_ascii=False)

    print(f"\nBest pass-rate: {best_score:.0%}\nWinning notice (review before ratifying):\n")
    print(best)
    print(f"\nFull log: {out}")


if __name__ == "__main__":
    main()
