"""Build the worked-example FEED document (a pump condition report).

Run from the repo root:
    python3 examples/build_pump_report.py

It writes examples/pump-condition-report.md and .html — the canonical demo for
"build a report, tag the evidence, paste it into Copilot, get grounded answers".
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from feed import FeedDocument  # noqa: E402


def build() -> FeedDocument:
    doc = FeedDocument(
        title="Q2 Condition Assessment — Pumping Station 14",
        author="RotorIQ Pipeline / N. Gul",
        grounding="strict",
        created="2026-06-20",
        summary=(
            "Two assets need action: XYZ-003 bearing replacement within 2 weeks, "
            "and ABC-007 alignment check at next planned stop. The station is "
            "otherwise within ISO limits."
        ),
    )

    # --- Evidence (tier 2) ---
    doc.add_evidence(
        "E001", type="data", confidence="high",
        asset="XYZ-003", metric="vibration_rms", value="12.4 mm/s",
        previous="7.8 mm/s (2026-05-15)",
        threshold="11.2 mm/s (ISO 10816-3 Zone C upper bound)",
        trend="+59% over 30 days",
    )
    doc.add_evidence(
        "E002", type="observation", confidence="medium",
        asset="XYZ-003", finding="audible bearing noise on walkdown",
        inspector="J. Powell", date="2026-06-15",
    )
    doc.add_evidence(
        "E003", type="data", confidence="high",
        asset="XYZ-003", metric="bearing_temp", value="71 C",
        baseline="48 C", ambient="22 C", date="2026-06-18",
    )
    doc.add_evidence(
        "E004", type="data", confidence="high",
        asset="ABC-007", metric="vibration_rms", value="6.1 mm/s",
        previous="5.9 mm/s (2026-05-15)",
        threshold="11.2 mm/s (ISO 10816-3 Zone C upper bound)",
        trend="+3% over 30 days",
    )
    doc.add_evidence(
        "E005", type="calc", confidence="medium",
        asset="ABC-007", metric="2x_running_speed_component",
        value="2.4 mm/s", interpretation="possible shaft misalignment",
        method="FFT, 1.5 kHz span", date="2026-06-18",
    )
    doc.add_evidence(
        "E006", type="data", confidence="high",
        asset="station_14", metric="assets_within_iso_limits",
        value="9 of 11", date="2026-06-18",
    )

    # --- Claims & decisions (tier 0) ---
    doc.add_claim(
        "C1",
        "XYZ-003 is in advanced bearing degradation and is the station's priority risk.",
        evidence=["E001", "E002", "E003"],
        decision="Raise priority work order for bearing replacement within 2 weeks",
    )
    doc.add_claim(
        "C2",
        "ABC-007 shows early signs of shaft misalignment but remains within ISO limits.",
        evidence=["E004", "E005"],
        decision="Schedule alignment check at next planned stop; no immediate action",
    )
    doc.add_claim(
        "C3",
        "The remainder of Station 14 is healthy and needs no intervention this quarter.",
        evidence=["E006"],
    )

    # --- Findings (tier 1) ---
    doc.add_finding(
        "XYZ-003 vibration has crossed the ISO 10816-3 Zone C upper bound [E001], with a "
        "23 C rise in bearing temperature above baseline [E003] and audible noise confirmed "
        "on the walkdown [E002]. The three signals agree: this is bearing-end-of-life, not a "
        "sensor artefact."
    )
    doc.add_finding(
        "ABC-007 vibration is well within limits [E004], but a 2x-running-speed component in "
        "the spectrum [E005] is the classic signature of shaft misalignment. It is worth "
        "watching, not acting on yet."
    )
    doc.add_finding(
        "Nine of eleven assets at Station 14 are inside ISO limits [E006]; no other asset "
        "warrants intervention this quarter."
    )
    return doc


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    doc = build()
    report = doc.validate()
    print(report)
    doc.write(os.path.join(here, "pump-condition-report.md"))
    doc.write(os.path.join(here, "pump-condition-report.html"))
    print("wrote pump-condition-report.md and .html")
