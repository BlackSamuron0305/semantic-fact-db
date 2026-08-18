"""Tests for the Wikidata real-world case-study loader.

Uses a small hand-written fixture rather than the live cached snapshot
(data/wikidata_case_study_raw.json), so these tests do not depend on
scripts/fetch_wikidata_case_study.py having been run and never touch
the network.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from sfdb.datasets.wikidata_case_study import HELD_POSITION_PREDICATE, load_facts

FIXTURE = {
    "source": "test fixture",
    "license": "CC0",
    "num_positions": 2,
    "num_facts": 3,
    "facts": [
        {
            "person": "http://www.wikidata.org/entity/Q1",
            "position_qid": "Q100",
            "position_label": "President of Testland",
            "country": "Testland",
            "start": "1990-01-01T00:00:00Z",
            "end": "1998-01-01T00:00:00Z",
        },
        {
            "person": "http://www.wikidata.org/entity/Q2",
            "position_qid": "Q100",
            "position_label": "President of Testland",
            "country": "Testland",
            "start": "1998-01-01T00:00:00Z",
            "end": None,
        },
        {
            # No start date: cannot validly carry the end date either
            # (SemanticFact rejects "end without start"), so this fact
            # must load with temporal=None despite having an end value.
            "person": "http://www.wikidata.org/entity/Q3",
            "position_qid": "Q200",
            "position_label": "Prime Minister of Otherland",
            "country": "Otherland",
            "start": None,
            "end": "1975-01-01T00:00:00Z",
        },
    ],
}


@pytest.fixture
def fixture_path(tmp_path: Path) -> Path:
    path = tmp_path / "wikidata_case_study_raw.json"
    path.write_text(json.dumps(FIXTURE))
    return path


def test_load_facts_count(fixture_path: Path) -> None:
    facts = load_facts(fixture_path)
    assert len(facts) == 3


def test_relation_is_real_wikidata_predicate(fixture_path: Path) -> None:
    facts = load_facts(fixture_path)
    assert all(f.relation.value == HELD_POSITION_PREDICATE for f in facts)


def test_temporal_envelope_parsed(fixture_path: Path) -> None:
    facts = load_facts(fixture_path)
    dated = next(f for f in facts if f.subject.value.endswith("Q1"))
    assert dated.temporal is not None
    assert dated.temporal.start is not None
    assert dated.temporal.end is not None
    assert dated.temporal.start.year == 1990
    assert dated.temporal.end.year == 1998


def test_open_ended_temporal_envelope(fixture_path: Path) -> None:
    facts = load_facts(fixture_path)
    ongoing = next(f for f in facts if f.subject.value.endswith("Q2"))
    assert ongoing.temporal is not None
    assert ongoing.temporal.start is not None
    assert ongoing.temporal.end is None


def test_end_without_start_is_dropped_not_fabricated(fixture_path: Path) -> None:
    facts = load_facts(fixture_path)
    undated = next(f for f in facts if f.subject.value.endswith("Q3"))
    assert undated.temporal is None


def test_context_reflects_country(fixture_path: Path) -> None:
    facts = load_facts(fixture_path)
    testland_facts = [f for f in facts if f.subject.value.endswith(("Q1", "Q2"))]
    assert all(str(f.context) == "world.Testland" for f in testland_facts)


def test_missing_snapshot_raises_with_instructions(tmp_path: Path) -> None:
    missing = tmp_path / "does_not_exist.json"
    with pytest.raises(FileNotFoundError, match="fetch_wikidata_case_study"):
        load_facts(missing)
