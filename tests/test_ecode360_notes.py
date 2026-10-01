"""OregonAI/oregon-counties#84: ecode360.com refuses the honestly-identified fetcher.

29 sources across clatsop.yml and crook.yml live on ecode360.com and, as of 2026-09-12, every
one of them returns a Cloudflare managed challenge to an honest agent. The operator decided
(2026-09-12, route 3) that this is recorded on each source as could-not-verify — never as
`unavailable` or withdrawn, since the block belongs to the vendor, not the county, and a
group-level `unavailable` would wrongly stop the non-ecode360 sources that still work — while
the agent drafts ORS 192.311-192.478 records requests for the operator to send.

This test is the mechanical half of that: every ecode360 source in an affected county carries
a dated could-not-verify note, no sha256 baseline is lost, and the group-level `crawl.basis`
no longer claims a 200 that is no longer true.
"""
from __future__ import annotations

import pathlib

import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
SOURCES = ROOT / "_meta" / "sources"

# group -> (total ecode360 sources, sources that carry a sha256 baseline)
AFFECTED = {"clatsop": (14, 11), "crook": (15, 11)}


def _load(group: str) -> dict:
    return yaml.safe_load((SOURCES / f"{group}.yml").read_text(encoding="utf-8"))


def _ecode360_sources(doc: dict) -> list[dict]:
    return [s for s in doc["sources"] if "ecode360.com" in s["url"]]


def test_ecode360_source_counts_match_the_2026_09_12_survey() -> None:
    # The issue's title said 7; the 2026-09-12 retriage found 29. If a manifest changes shape
    # again, this is the tripwire that says "re-measure before trusting the old count."
    for group, (total, _) in AFFECTED.items():
        assert len(_ecode360_sources(_load(group))) == total, group


def test_every_ecode360_source_records_could_not_verify() -> None:
    for group in AFFECTED:
        doc = _load(group)
        for src in _ecode360_sources(doc):
            notes = src.get("notes", "")
            assert notes, f"{group}:{src['id']} has no could-not-verify note"
            low = notes.lower()
            assert "could not verify" in low, src["id"]
            assert "2026-09-12" in notes, src["id"]
            assert "cloudflare" in low and "managed challenge" in low, src["id"]
            assert "#84" in notes, src["id"]
            # The whole point of this issue: never let this read as a withdrawal or an
            # outright absence.
            assert "unavailable" not in low, src["id"]
            assert "withdrawn" not in low, src["id"]


def test_no_sha256_baseline_was_lost() -> None:
    for group, (_, with_baseline) in AFFECTED.items():
        doc = _load(group)
        non_empty = [s for s in _ecode360_sources(doc) if s.get("sha256")]
        assert len(non_empty) == with_baseline, group


def test_group_decision_stays_proceed_not_unavailable() -> None:
    # `unavailable` is a group-wide decision (src/ingest_counties.py) and would also stop
    # clatsop's 18 and crook's 3 non-ecode360 sources, which this block does not touch.
    for group in AFFECTED:
        assert _load(group)["crawl"]["decision"] == "proceed", group


def test_crawl_basis_no_longer_claims_a_200_that_is_not_true() -> None:
    for group in AFFECTED:
        basis = _load(group)["crawl"]["basis"]
        low = basis.lower()
        # The present-tense claim this issue found false must be gone, not just dated.
        assert "serves http 200" not in low, group
        assert "serves the honest agent http 200" not in low, group
        assert "cloudflare managed challenge" in low, group
        assert "2026-09-12" in basis, group
