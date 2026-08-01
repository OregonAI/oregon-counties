#!/usr/bin/env python3
"""Corpus-specific CI gate: the seed's guardrails, made mechanical.

`oregon-audits` set the precedent that a corpus's stated guardrails are enforced in CI rather
than left to honour, because a guardrail in a README is a hope. This checks the five things
the toolkit's generic validators structurally cannot see — they check schema, provenance and
placement, and every rule below is about MEANING.

    1  governing body      6 of 36 counties are governed by a County Court, not a Board.
    2  authority basis     8 are home-rule charter; 28 are general law.
    3  absence claims      "this county publishes none" must be backed by the survey.
    4  heading truncation  a `## ` at column zero silently eats the rest of a document.
    5  draft text          a redline published as adopted law is the worst error here.

Run: python3 src/check_guardrails.py [--verbose]
"""
from __future__ import annotations

import argparse
import pathlib
import re
import sys

import yaml

from corpus_toolkit import config as config_mod
from corpus_toolkit.repo import content_files, parse_frontmatter

ROOT = pathlib.Path(__file__).resolve().parent.parent
SURVEY = pathlib.Path("/home/dzinck/corpus-seeds/oregon-counties.survey.yml")

BOARD_RE = re.compile(r"Board\s+of\s+(County\s+)?Commissioners", re.I)
COURT_RE = re.compile(r"County\s+Court", re.I)

# Phrases that assert a county publishes nothing of some kind. Absence is the claim this
# corpus is least entitled to make from its own contents: a county with no document here may
# have none, may not publish it, may have moved it, or may sit behind a wall. Every one of
# these must be backed by a `none-found` in the survey — which is a measurement — rather than
# by the corpus noticing it holds no file.
ABSENCE_RE = re.compile(
    r"\b(?:does not (?:publish|have|maintain)|publishes no|has no|no such|none (?:is |are )?"
    r"published|not published|no (?:published )?(?:code|policy|ordinance|plan))\b", re.I)

DRAFT_RE = re.compile(r"redline|\bissue\s*\d+\b|zdoproposed|-draft\b|\bproposed\b", re.I)

# The survey family whose absence a claim in each subdirectory would be about.
DIR_FAMILY = {"code": "county_code", "orders": "board_orders",
              "policies": "admin_policies", "land-use": "land_use"}


def load_registry() -> dict[str, dict]:
    data = yaml.safe_load((ROOT / "_meta" / "counties.yml").read_text())
    return {c["slug"]: c for c in data["counties"]}


def load_survey() -> dict[str, dict]:
    if not SURVEY.is_file():
        return {}
    data = yaml.safe_load(SURVEY.read_text())
    return {f"{r['county']}-county": r for r in data.get("records", [])}


def glance_of(body: str) -> str:
    m = re.search(r"^## At a glance\s*$(.*?)(?=^## |\Z)", body, re.M | re.S)
    return m.group(1) if m else ""


def fulltext_of(body: str) -> str:
    """The Full text section AS THE TOOLKIT SEES IT — deliberately the same regex."""
    m = re.search(r"^## Full text\s*$(.*?)(?=^## |\Z)", body, re.M | re.S)
    return m.group(1) if m else ""


# Headings a document is allowed to carry after `## Full text`. Anything else starting `## `
# at column zero is source text that escaped the ingester's guard.
LEGIT_TRAILING = ("## Curator notes", "## Cross-references", "## Sources", "## Notes")


def stray_headings(body: str) -> list[str]:
    """Lines starting `## ` after the Full text marker that are not legitimate sections.

    THIS CANNOT USE fulltext_of(), AND THAT IS THE WHOLE POINT. The failure being detected is
    that a stray `## ` TERMINATES the Full text capture — so anything this check is looking
    for has already fallen outside the section by the time the regex is done. Written against
    fulltext_of() first, it passed on a document with an injected heading and reported the
    corpus clean, which is precisely the silent-truncation bug it exists to catch, reproduced
    inside its own detector.

    Scanning raw from the marker to the end of the document is the only way to see it.
    """
    start = body.find("## Full text")
    if start < 0:
        return []
    return [ln for ln in body[start:].splitlines()[1:]
            if re.match(r"^## \S", ln) and not ln.startswith(LEGIT_TRAILING)]


def check(verbose: bool = False) -> list[str]:
    config = config_mod.load(ROOT / "_meta" / "corpus.yml")
    registry, survey = load_registry(), load_survey()
    problems: list[str] = []
    n = 0

    for path in content_files(config):
        n += 1
        rel = path.relative_to(ROOT)
        parts = rel.parts
        if len(parts) < 3:
            continue
        slug, family = parts[1], parts[2]
        county = registry.get(slug)
        if county is None:
            problems.append(f"{rel}: '{slug}' is not in _meta/counties.yml")
            continue

        fm, body = parse_frontmatter(path)
        fm = fm or {}
        issuing = str(fm.get("issuing_body", ""))

        # 1 — governing body. A county court county has no Board of Commissioners, and
        # naming one attributes the document to a body that does not exist there.
        if county["governing_body"] == "county-court" and BOARD_RE.search(issuing):
            problems.append(
                f"{rel}: issuing_body names a Board of Commissioners, but {county['name']} "
                f"is governed by a County Court")
        if county["governing_body"] == "board" and COURT_RE.search(issuing) \
                and not BOARD_RE.search(issuing):
            problems.append(
                f"{rel}: issuing_body names a County Court, but {county['name']} "
                f"is governed by a Board of Commissioners")

        # 2 — authority basis. A general-law county has no charter to derive authority from,
        # so a document claiming charter authority there overstates what it rests on.
        level = str(fm.get("authority_level", ""))
        if level == "county_charter" and county["home_rule"] != "charter":
            problems.append(
                f"{rel}: claims authority_level county_charter, but {county['name']} "
                f"operates under general law, not a charter")

        # 3 — absence claims must be measured, not inferred from an empty directory.
        glance = glance_of(body)
        if ABSENCE_RE.search(glance):
            fam_key = DIR_FAMILY.get(family)
            rec = survey.get(slug, {}).get("families", {}).get(fam_key, {})
            if rec.get("platform") != "none-found":
                problems.append(
                    f"{rel}: '## At a glance' asserts an absence, but the survey records "
                    f"{fam_key}={rec.get('platform', '<no record>')!r} for {slug} — an "
                    f"absence claim must rest on a measured none-found, not on us holding "
                    f"no file")

        # 4 — heading truncation. Checked on the COMMITTED text, not on the extractor, so a
        # hand edit cannot reintroduce it. Silent by construction: coverage thresholds are
        # 0.70/0.90, so a stray '## ' late in a long document truncates the tail and still
        # scores above 90%, and the in-order line check passes because the surviving lines
        # are all still present and still in order.
        stray = stray_headings(body)
        if stray:
            problems.append(
                f"{rel}: {len(stray)} line(s) start with '## ' at column zero inside "
                f"'## Full text' — everything after the first is silently truncated from "
                f"provenance, search and extract_fulltext. First: {stray[0][:60]!r}")

        # 5 — draft text published as adopted law.
        src = str(fm.get("source_url", ""))
        if DRAFT_RE.search(path.name) or DRAFT_RE.search(src):
            problems.append(
                f"{rel}: filename or source_url looks like a draft/redline, but this is "
                f"published as adopted law (status={fm.get('status')!r})")

    if verbose:
        print(f"checked {n} documents across {len({p.parts[1] for p in [q.relative_to(ROOT) for q in content_files(config)] if len(p.parts) > 1})} counties")
    return problems


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()
    problems = check(args.verbose)
    if problems:
        print(f"FAIL — {len(problems)} guardrail violation(s):\n", file=sys.stderr)
        for p in problems:
            print(f"  {p}", file=sys.stderr)
        return 1
    print("OK — guardrails clean.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
