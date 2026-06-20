"""Run the cross-model reliability matrix for one or more providers and notice variants.

    python eval/run.py --provider mock                 # offline, proves the pipeline
    python eval/run.py --provider openai,anthropic     # real models (needs keys)
    python eval/run.py --provider openai --variant strengthened_handshake --repeats 5

Writes a JSON transcript + a Markdown scorecard to eval/results/. Scoring is mechanical
(feed.verify) so runs are reproducible and auditable.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)                      # suite / providers / score
sys.path.insert(0, os.path.dirname(HERE))     # repo root, for `import feed`

import providers  # noqa: E402
import score as scorer  # noqa: E402
import suite  # noqa: E402


def run(provider_list, variants, conditions, repeats, out_dir):
    rows = []  # one per (provider, variant, condition, question, repeat)
    for provider in provider_list:
        for variant in variants:
            doc = suite.assemble(variant)
            for condition in conditions:
                for q in suite.QUESTIONS:
                    for i in range(repeats):
                        content = suite.user_message(doc, q["text"], condition)
                        try:
                            answer = providers.ask(provider, content)
                            err = None
                        except Exception as e:  # provider/key/SDK failure
                            answer, err = "", str(e)
                        passed, detail = (False, f"call error: {err}") if err \
                            else scorer.score(answer, doc, q["expect"])
                        rows.append({
                            "provider": provider, "variant": variant, "condition": condition,
                            "question": q["id"], "expect": q["expect"], "repeat": i,
                            "passed": passed, "detail": detail, "answer": answer, "error": err,
                        })
                        mark = "PASS" if passed else "FAIL"
                        print(f"  {provider:9} {variant:22} {condition:7} {q['id']:3} {mark}  {detail[:70]}")
    return rows


def aggregate(rows):
    """pass-rate per (provider, variant, condition)."""
    agg = defaultdict(lambda: [0, 0])
    for r in rows:
        k = (r["provider"], r["variant"], r["condition"])
        agg[k][1] += 1
        if r["passed"]:
            agg[k][0] += 1
    return agg


def scorecard_md(rows, agg):
    lines = ["# FEED cross-model scorecard", "", "Pass-rate per provider × notice variant × condition.", ""]
    lines.append("| provider | variant | condition | pass-rate |")
    lines.append("|---|---|---|---|")
    for (provider, variant, condition), (p, n) in sorted(agg.items()):
        pct = f"{100*p/n:.0f}%" if n else "—"
        lines.append(f"| {provider} | {variant} | {condition} | {pct} ({p}/{n}) |")
    lines += ["", "## Failures", ""]
    fails = [r for r in rows if not r["passed"]]
    if not fails:
        lines.append("None.")
    for r in fails:
        lines.append(f"- **{r['provider']} · {r['variant']} · {r['condition']} · {r['question']}** "
                     f"({r['expect']}): {r['detail']}")
        if r["answer"]:
            lines.append(f"  - answer: _{r['answer'][:160].strip()}_")
    return "\n".join(lines) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--provider", default="mock", help="comma-separated: mock,openai,anthropic,gemini")
    ap.add_argument("--variant", default=",".join(suite.NOTICE_VARIANTS),
                    help="comma-separated notice variants")
    ap.add_argument("--condition", default=",".join(suite.CONDITIONS), help="bare,invoked")
    ap.add_argument("--repeats", type=int, default=1)
    ap.add_argument("--tag", default="run")
    args = ap.parse_args()

    provider_list = [p.strip() for p in args.provider.split(",") if p.strip()]
    variants = [v.strip() for v in args.variant.split(",") if v.strip()]
    conditions = [c.strip() for c in args.condition.split(",") if c.strip()]

    print(f"providers={provider_list} variants={variants} conditions={conditions} repeats={args.repeats}\n")
    rows = run(provider_list, variants, conditions, args.repeats, HERE)
    agg = aggregate(rows)

    out = os.path.join(HERE, "results")
    os.makedirs(out, exist_ok=True)
    base = f"{args.tag}_{'-'.join(provider_list)}"
    with open(os.path.join(out, base + ".json"), "w", encoding="utf-8") as f:
        json.dump(rows, f, indent=2, ensure_ascii=False)
    md = scorecard_md(rows, agg)
    with open(os.path.join(out, base + ".md"), "w", encoding="utf-8") as f:
        f.write(md)

    print("\n" + md)
    print(f"\nwrote results/{base}.json and results/{base}.md")


if __name__ == "__main__":
    main()
