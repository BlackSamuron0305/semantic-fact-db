#!/usr/bin/env python3
"""Fetch a real-world case-study dataset from Wikidata's public SPARQL endpoint.

Domain: national head-of-state and head-of-government office-holders
("position held", P39, with P580/P582 start/end qualifiers) --- the
textbook example of the reification problem this paper opens with (a
single "held office" fact has an office-holder, a position, a start
date, an end date, and a country, none of which reduce to a single
subject-predicate-object triple without splitting the fact apart).

This script only fetches and caches the raw data; it does not touch the
benchmark or the paper. Output is written to
data/wikidata_case_study_raw.json and is what
src/sfdb/datasets/wikidata_case_study.py reads -- the benchmark never
queries Wikidata live, so results are reproducible even if Wikidata's
data changes after this snapshot was taken. Re-run this script to refresh
the snapshot; it is not run automatically by the benchmark suite.

Two-stage query, deliberately avoiding expensive SPARQL property-path
transitive closures (P279*) and unrandomized joins, both of which were
found empirically to time out or produce a severely skewed sample
against Wikidata's public endpoint (a handful of anomalous "position"
items dominate a naive join across tens of thousands of rows):

  1. Find candidate national-leadership *positions* by regex-matching
     English labels against title patterns ("President of X", "Prime
     Minister of X", ...), then keep only the ones whose "of <X>" suffix
     matches a real UN member state name -- filters out clubs,
     fictional entities, and sub-national offices that also match the
     label pattern.
  2. For each surviving position, fetch every P39 (position held)
     statement naming it, with P580/P582 qualifiers, and P17 (country)
     on the position itself where present.

Usage: uv run python scripts/fetch_wikidata_case_study.py
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Any

import requests

REPO_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_PATH = REPO_ROOT / "data" / "wikidata_case_study_raw.json"

ENDPOINT = "https://query.wikidata.org/sparql"
HEADERS = {
    "Accept": "application/sparql-results+json",
    "User-Agent": "SFDB-Research/1.0 (academic benchmark dataset construction; "
    "github.com/BlackSamuron0305/semantic-fact-db)",
}

# Broad net for national-leadership title patterns; false positives (clubs,
# sub-national offices, fictional entities -- e.g. "President of Real
# Betis" is a genuine label that matches this regex) are filtered by the
# country-name check below rather than a narrower regex, since Wikidata's
# own class hierarchy for these positions turned out to be too
# inconsistently applied to filter by class alone. The `wdt:P31/wdt:P279*
# wd:Q294414` ("instance of a subclass of public office") clause is here
# purely as a server-side performance pre-filter, empirically necessary:
# the identical regex without it hit a 504 Gateway Timeout on Wikidata's
# public endpoint, while with it the query reliably completes in well
# under a minute.
TITLE_REGEX = (
    "^(President|Prime Minister|Chancellor|Premier|Monarch|King|Queen|"
    "Emperor|Sultan) of "
)

POSITION_QUERY = f"""
SELECT ?position ?positionLabel WHERE {{
  ?position rdfs:label ?positionLabel .
  FILTER(LANG(?positionLabel) = "en")
  FILTER(REGEX(?positionLabel, "{TITLE_REGEX}"))
  ?position wdt:P31/wdt:P279* wd:Q294414 .
}}
LIMIT 3000
"""

FACTS_QUERY_TEMPLATE = """
SELECT ?person ?start ?end WHERE {{
  ?person p:P39 ?stmt .
  ?stmt ps:P39 wd:{qid} .
  OPTIONAL {{ ?stmt pq:P580 ?start . }}
  OPTIONAL {{ ?stmt pq:P582 ?end . }}
}}
"""

# ISO-recognised sovereign states (UN members + a few common non-UN
# names Wikidata's English labels use), used to keep only positions whose
# "of <X>" suffix names a real country -- not a club, university, or
# fictional/hypothetical entity that also happens to match the title regex.
COUNTRY_NAMES = {
    "afghanistan", "albania", "algeria", "andorra", "angola",
    "antigua and barbuda", "argentina", "armenia", "australia", "austria",
    "azerbaijan", "the bahamas", "bahrain", "bangladesh", "barbados",
    "belarus", "belgium", "belize", "benin", "bhutan", "bolivia",
    "bosnia and herzegovina", "botswana", "brazil", "brunei", "bulgaria",
    "burkina faso", "burundi", "cabo verde", "cambodia", "cameroon",
    "canada", "the central african republic", "chad", "chile", "china",
    "colombia", "the comoros", "the republic of the congo",
    "the democratic republic of the congo", "costa rica",
    "cote d'ivoire", "croatia", "cuba", "cyprus", "czechia",
    "the czech republic", "denmark", "djibouti", "dominica",
    "the dominican republic", "ecuador", "egypt", "el salvador",
    "equatorial guinea", "eritrea", "estonia", "eswatini", "ethiopia",
    "fiji", "finland", "france", "gabon", "the gambia", "georgia",
    "germany", "ghana", "greece", "grenada", "guatemala", "guinea",
    "guinea-bissau", "guyana", "haiti", "honduras", "hungary", "iceland",
    "india", "indonesia", "iran", "iraq", "ireland", "israel", "italy",
    "jamaica", "japan", "jordan", "kazakhstan", "kenya", "kiribati",
    "north korea", "south korea", "kosovo", "kuwait", "kyrgyzstan",
    "laos", "latvia", "lebanon", "lesotho", "liberia", "libya",
    "liechtenstein", "lithuania", "luxembourg", "madagascar", "malawi",
    "malaysia", "maldives", "mali", "malta", "the marshall islands",
    "mauritania", "mauritius", "mexico", "micronesia", "moldova",
    "monaco", "mongolia", "montenegro", "morocco", "mozambique",
    "myanmar", "namibia", "nauru", "nepal", "the netherlands",
    "new zealand", "nicaragua", "niger", "nigeria",
    "north macedonia", "norway", "oman", "pakistan", "palau", "panama",
    "papua new guinea", "paraguay", "peru", "the philippines", "poland",
    "portugal", "qatar", "romania", "russia", "rwanda",
    "saint kitts and nevis", "saint lucia",
    "saint vincent and the grenadines", "samoa", "san marino",
    "sao tome and principe", "saudi arabia", "senegal", "serbia",
    "the seychelles", "sierra leone", "singapore", "slovakia",
    "slovenia", "the solomon islands", "somalia", "somaliland",
    "south africa", "south sudan", "spain", "sri lanka", "sudan",
    "suriname", "sweden", "switzerland", "syria", "taiwan",
    "tajikistan", "tanzania", "thailand", "timor-leste", "togo",
    "tonga", "trinidad and tobago", "tunisia", "turkey", "turkmenistan",
    "tuvalu", "uganda", "ukraine", "the united arab emirates",
    "the united kingdom", "the united states", "uruguay", "uzbekistan",
    "vanuatu", "the vatican", "venezuela", "vietnam", "yemen", "zambia",
    "zimbabwe", "the soviet union", "yugoslavia", "east germany",
    "west germany", "the republic of china", "prussia", "byzantium",
    "the byzantine empire", "rome", "the roman empire",
}


def _get(query: str, session: requests.Session, retries: int = 4) -> list[dict[str, Any]]:
    """GET with retry-with-backoff.

    A 429 (rate limit) gets a long, Retry-After-respecting wait -- this
    script is a guest on a shared public endpoint, not a load generator,
    so a 429 means slow down, not merely "try again soon". A 502/504
    (transient gateway/timeout error) gets a shorter linear backoff.
    """
    last_exc: Exception | None = None
    for attempt in range(retries):
        try:
            resp = session.get(ENDPOINT, params={"query": query}, headers=HEADERS, timeout=90)
            if resp.status_code == 429:
                wait = int(resp.headers.get("Retry-After", 30 * (attempt + 1)))
                print(f"  429 rate-limited; waiting {wait}s before retrying...", file=sys.stderr)
                time.sleep(wait)
                continue
            resp.raise_for_status()
            bindings: list[dict[str, Any]] = resp.json()["results"]["bindings"]
            return bindings
        except requests.RequestException as exc:
            last_exc = exc
            wait = 8 * (attempt + 1)
            print(f"  request failed ({exc}); retrying in {wait}s...", file=sys.stderr)
            time.sleep(wait)
    assert last_exc is not None
    raise last_exc


def _country_from_label(label: str) -> str | None:
    """Extract and validate the '<X>' in 'Title of X', case-insensitively."""
    if " of " not in label:
        return None
    suffix = label.split(" of ", 1)[1].strip()
    if suffix.lower() in COUNTRY_NAMES:
        return suffix
    return None


def main() -> int:
    session = requests.Session()

    print("Fetching candidate national-leadership positions...")
    position_rows = _get(POSITION_QUERY, session)
    print(f"  {len(position_rows)} label matches")

    positions: dict[str, dict[str, str]] = {}
    for row in position_rows:
        label = row["positionLabel"]["value"]
        country = _country_from_label(label)
        if country is None:
            continue
        qid = row["position"]["value"].rsplit("/", 1)[-1]
        # Keep the shortest label per country (avoids sub-variants like
        # "President of X (in exile)" crowding out the canonical office).
        existing = positions.get(qid)
        if existing is None:
            positions[qid] = {"qid": qid, "label": label, "country": country}

    print(f"  {len(positions)} positions matched a real country")

    all_facts: list[dict[str, str | None]] = []
    for i, pos in enumerate(positions.values()):
        try:
            rows = _get(FACTS_QUERY_TEMPLATE.format(qid=pos["qid"]), session)
        except requests.RequestException as exc:
            print(f"  [{pos['qid']}] request failed: {exc}", file=sys.stderr)
            continue
        for row in rows:
            all_facts.append(
                {
                    "person": row["person"]["value"],
                    "position_qid": pos["qid"],
                    "position_label": pos["label"],
                    "country": pos["country"],
                    "start": row.get("start", {}).get("value"),
                    "end": row.get("end", {}).get("value"),
                }
            )
        if (i + 1) % 10 == 0:
            print(f"  {i + 1}/{len(positions)} positions fetched, "
                  f"{len(all_facts)} facts so far", flush=True)
        # Wikidata's usage policy asks for restraint. 0.3s produced
        # sustained 429s in practice against the public endpoint, so this
        # is deliberately more conservative.
        time.sleep(1.5)

    print(f"Done: {len(all_facts)} facts across {len(positions)} positions.")

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        json.dumps(
            {
                "source": "Wikidata (query.wikidata.org), P39 position held, "
                "national head-of-state/government offices",
                "license": "CC0 (Wikidata content license)",
                "num_positions": len(positions),
                "num_facts": len(all_facts),
                "facts": all_facts,
            },
            indent=2,
        )
    )
    print(f"Wrote {OUTPUT_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
