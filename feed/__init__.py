"""FEED — Format for Enforced Evidence-based Digestion.

A self-bootstrapping document protocol that makes downstream LLMs ground their
answers in cited evidence — and lets you mechanically verify they did.

    from feed import FeedDocument

    doc = FeedDocument("Q2 Pump Health Assessment", grounding="strict")
    doc.add_evidence("E001", asset="XYZ-003", metric="vibration_rms",
                     value="12.4 mm/s", threshold="11.2 mm/s (ISO 10816-3 Zone C)",
                     confidence="high")
    doc.add_claim("C1", "XYZ-003 needs intervention", evidence=["E001"],
                  decision="Approve bearing replacement work order")
    print(doc.render("md"))
"""

from .authoring import AUTHORING_PROMPT, FEED_JSON_SCHEMA, build
from .constants import GROUNDING_MODES, VERSION
from .document import Claim, Evidence, FeedDocument
from .validate import ValidationReport, validate
from .verify import VerificationReport, verify

# Package version. The FEED *protocol* version is `VERSION` ("0.2") and is the
# one embedded in documents; this package version moves independently.
__version__ = "0.2.1"

__all__ = [
    "FeedDocument",
    "Evidence",
    "Claim",
    "build",
    "AUTHORING_PROMPT",
    "FEED_JSON_SCHEMA",
    "validate",
    "ValidationReport",
    "verify",
    "VerificationReport",
    "GROUNDING_MODES",
    "VERSION",
]
