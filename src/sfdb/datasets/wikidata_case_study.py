"""Real-world case study: Wikidata national leadership office-holders.

Loads the cached snapshot at data/wikidata_case_study_raw.json (built by
scripts/fetch_wikidata_case_study.py from Wikidata's public SPARQL
endpoint) as SemanticFact instances, for use as an organic alternative
to this project's own synthetic generator (sfdb.datasets.synthetic) in
the benchmark suite -- see scripts/wikidata_case_study_benchmark.py and
paper/sections/evaluation.tex's real-world case study section.

Each fact is one P39 ("position held") statement: a person, the
national office they held, and the P580/P582 start/end date qualifiers
Wikidata records where present. This is a genuine instance of the
reification problem the paper opens with -- WHO held WHAT office WHEN,
in WHICH country -- rather than a reducible binary relation, so it
exercises the same n-ary, context-scoped, temporally-qualified shape
the synthetic generator was built to imitate, on data this project did
not construct.

This loader never queries Wikidata live; it only reads the cached
snapshot, so benchmark results are reproducible independent of
Wikidata's live data changing after the snapshot was taken.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from common.schema import SemanticFact
from common.types import Context, Identifier, Provenance, TemporalInfo, Value

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
RAW_DATA_PATH = REPO_ROOT / "data" / "wikidata_case_study_raw.json"

# The real Wikidata "position held" direct-value property, matching how
# Wikidata's own RDF export names it -- not a project-invented predicate.
HELD_POSITION_PREDICATE = "http://www.wikidata.org/prop/direct/P39"


def _parse_wikidata_datetime(value: str | None) -> datetime | None:
    """Parse a Wikidata SPARQL xsd:dateTime literal.

    Returns None for BCE dates (a leading '-' year, e.g.
    "-0160-01-01T00:00:00Z") since Python's datetime cannot represent
    years before 1 CE -- rather than crash or silently clamp to a wrong
    date, those facts simply get no temporal envelope.
    """
    if value is None:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def load_facts(path: Path = RAW_DATA_PATH) -> list[SemanticFact]:
    """Load the cached Wikidata snapshot as a list of SemanticFact.

    Raises FileNotFoundError with instructions if the snapshot has not
    been fetched yet.
    """
    if not path.exists():
        raise FileNotFoundError(
            f"{path} not found. Run `uv run python "
            "scripts/fetch_wikidata_case_study.py` first to build the "
            "cached snapshot."
        )
    raw = json.loads(path.read_text())
    facts: list[SemanticFact] = []
    for i, row in enumerate(raw["facts"]):
        start = _parse_wikidata_datetime(row.get("start"))
        end = _parse_wikidata_datetime(row.get("end"))
        # A record with an end date but no start date cannot become a
        # valid TemporalInfo (SemanticFact validation rejects "end
        # without start"); it is dropped rather than fabricating a
        # start, matching real-world data that is sometimes only
        # partially qualified.
        temporal = TemporalInfo(start=start, end=end) if start is not None else None
        country_ctx = row["country"].replace(" ", "_")
        fact = SemanticFact(
            id=Identifier(f"wd_fact_{i}"),
            subject=Identifier(row["person"]),
            relation=Identifier(HELD_POSITION_PREDICATE),
            objects=(
                Value.reference(
                    Identifier(f"http://www.wikidata.org/entity/{row['position_qid']}")
                ),
            ),
            attributes={"positionLabel": Value.literal(row["position_label"])},
            context=Context(f"world.{country_ctx}"),
            provenance=Provenance(source="wikidata", method="sparql_snapshot"),
            temporal=temporal,
        )
        facts.append(fact)
    return facts
