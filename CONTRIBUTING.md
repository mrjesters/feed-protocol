# Contributing to FEED

FEED aims to be a low-friction, open standard. Contributions — from typo fixes to
protocol proposals — are welcome.

## Ways to contribute

- **Use it and report back.** Real-world friction is the most valuable feedback.
  Open an issue describing what was awkward.
- **Propose a protocol change.** Open an issue tagged `spec` describing the
  problem, the proposed change, and the impact on existing documents. The bar for
  changing the format is high — simplicity and backward-readability are the point.
- **Improve the tooling.** Bug fixes, new renderers/parsers, ports to other
  languages. The reference library is the canonical behaviour; keep it conformant
  to `spec/feed-spec-v0.2.md`.

## Ground rules for the format

The qualities that make FEED worth adopting are non-negotiable:

1. **Self-bootstrapping** — a document/authoring kit must work on any AI with no
   prior knowledge of FEED. Don't add anything that requires a plugin or provider
   support.
2. **Zero-install to read or write** — one plain-text file; markers in HTML
   comments; no required runtime.
3. **Verifiable** — the citation contract must stay mechanically checkable without
   an LLM.
4. **Front-loaded** — order encodes priority so small-context models stay safe.

A change that breaks any of these is unlikely to be accepted, however convenient.

## Development

```bash
pip install -e ".[dev]"   # library + pytest (+ anthropic for the optional tagger)
pytest                    # run the test suite
python3 examples/build_pump_report.py   # regenerate the worked example
```

Keep the core (`feed/` minus `tagger.py`) dependency-free and LLM-free. Only the
optional `tagger` module may call an external API.

## Versioning

The spec is versioned (`v0.2`). Changes that alter document semantics bump the
spec version; the reference library follows in lockstep.

Released under the MIT License — by contributing you agree your contributions are
licensed the same way.
