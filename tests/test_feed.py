"""Tests for the FEED library: build → render → parse round-trip, validation,
and the verification ("teeth") path. Pure Python, no network."""

import pytest

from feed import FeedDocument, validate, verify


def make_doc(grounding="strict"):
    doc = FeedDocument(
        title="Q2 Pump Health Assessment",
        author="RotorIQ / N. Gul",
        grounding=grounding,
        created="2026-06-20",
        summary="XYZ-003 needs bearing replacement within 2 weeks.",
    )
    doc.add_evidence(
        "E001",
        type="data",
        confidence="high",
        asset="XYZ-003",
        metric="vibration_rms",
        value="12.4 mm/s",
        previous="7.8 mm/s (2026-05-15)",
        threshold="11.2 mm/s (ISO 10816-3 Zone C)",
        trend="+59% over 30 days",
    )
    doc.add_evidence(
        "E002",
        type="observation",
        confidence="medium",
        asset="XYZ-003",
        finding="audible bearing noise on inspection",
        date="2026-06-15",
    )
    doc.add_claim(
        "C1",
        "XYZ-003 is deteriorating and requires intervention.",
        evidence=["E001", "E002"],
        decision="Approve bearing replacement work order",
    )
    doc.add_finding(
        "Vibration on XYZ-003 has crossed the ISO 10816-3 Zone C threshold [E001], "
        "corroborated by audible bearing noise on inspection [E002]."
    )
    return doc


def test_build_and_validate():
    doc = make_doc()
    report = validate(doc)
    assert report.ok, report
    assert len(doc.evidence) == 2
    assert len(doc.claims) == 1


def test_add_claim_rejects_unknown_evidence():
    doc = FeedDocument("t")
    with pytest.raises(ValueError):
        doc.add_claim("C1", "x", evidence=["E999"])


def test_duplicate_evidence_id_rejected():
    doc = FeedDocument("t")
    doc.add_evidence("E001", value="1")
    with pytest.raises(ValueError):
        doc.add_evidence("E001", value="2")


def test_evidence_requires_fields():
    doc = FeedDocument("t")
    with pytest.raises(ValueError):
        doc.add_evidence("E001")


def test_malformed_ids_rejected():
    doc = FeedDocument("t")
    with pytest.raises(ValueError):
        doc.add_evidence("X1", value="1")
    doc.add_evidence("E001", value="1")
    with pytest.raises(ValueError):
        doc.add_claim("claim1", "x", evidence=["E001"])


def test_markdown_roundtrip():
    doc = make_doc()
    md = doc.to_markdown()
    assert "<!-- FEED:DOC" in md
    assert "AI INGESTION NOTICE" in md
    assert "[E001]" in md

    reparsed = FeedDocument.from_markdown(md)
    assert reparsed.title == doc.title
    assert reparsed.grounding == "strict"
    assert {e.id for e in reparsed.evidence} == {"E001", "E002"}
    e1 = next(e for e in reparsed.evidence if e.id == "E001")
    assert e1.fields["value"] == "12.4 mm/s"
    assert e1.confidence == "high"
    assert len(reparsed.claims) == 1
    assert reparsed.claims[0].evidence == ["E001", "E002"]
    assert reparsed.claims[0].decision == "Approve bearing replacement work order"
    assert reparsed.validate().ok
    assert reparsed.findings  # narrative preserved


def test_html_render_hides_markers_but_keeps_them():
    doc = make_doc()
    html = doc.to_html()
    assert "<!-- FEED:EVIDENCE" in html  # present in raw source for an AI
    assert "<table" in html              # rendered for a human
    assert "AI INGESTION NOTICE" in html


def test_verify_passes_for_grounded_answer():
    doc = make_doc()
    answer = (
        "The pump XYZ-003 is deteriorating: vibration reached 12.4 mm/s, above the "
        "11.2 mm/s threshold [E001], with audible noise on inspection [E002]."
    )
    report = verify(answer, doc)
    assert report.passed, report
    assert set(report.valid) == {"E001", "E002"}
    assert not report.invalid
    assert "E001" in report.corroborated  # the figure 12.4 appears


def test_verify_fails_on_invented_citation():
    doc = make_doc()
    report = verify("It is fine, trust me [E404].", doc)
    assert not report.passed
    assert report.invalid == ["E404"]


def test_verify_strict_requires_citation():
    doc = make_doc("strict")
    report = verify("The pump seems fine to me.", doc)
    assert not report.passed


def test_verify_open_allows_no_citation():
    doc = make_doc("open")
    report = verify("The pump seems fine to me.", doc)
    assert report.passed


def test_priority_ordering_front_loads_core():
    doc = make_doc()
    md = doc.to_markdown()
    claims_pos = md.index("Claims & Decisions")
    evidence_pos = md.index("## Evidence")
    # Tier 0 (claims) must come before Tier 2 (full evidence): truncation-safe.
    assert claims_pos < evidence_pos
