#!/usr/bin/env python3
"""Citation schemes this corpus resolves, registered with the MCP framework.

Loaded via `plugins.citation_module` in _meta/corpus.yml. Importing this module is the whole
contract — `register_scheme` calls happen at import time.

THE HARD PART HERE IS THAT COUNTY CITATION IS NOT UNIFORM, and pretending otherwise would be
a fabrication that looks official. There is no statewide convention, no statutory citation
form, and no shared abbreviation registry.

What the corpus's OWN DOCUMENT IDS show, which is evidence rather than recollection — five
different ways of naming the same thing, one per county:

    lane-code-lc01                                  Lane, chapter as `LCnn`
    lane-land-use-lc16-245-249                      ...split by section range
    multnomah-code-chapter-11-revenue-and-taxation  Multnomah, chapter plus subject
    washington-code-tit1gepr                        Washington, Municode node ids
    jackson-code-ch1020                             Jackson, four-digit chapters

So this module registers ONE PATTERN PER COUNTY rather than a single clever regex that would
match a form no county writes and resolve it confidently to the wrong document.

ABBREVIATED FORMS ARE NOT REGISTERED FOR ANY COUNTY YET, and that is deliberate. "MCC", "WCC"
and "DCC" are plausible and I have not verified that any of these counties uses them, so
writing one in would manufacture a citation form and hand agents a scheme that matches text
no county produces. `code_abbr` is absent from every registry entry until a county's own
documents are seen using it.

WHAT IS DELIBERATELY NOT REGISTERED: a section-level scheme. County codes number sections
inconsistently and most administrative policies are not numbered at all. Building
section-level resolution before a document needs it would produce a scheme that matches
citations and resolves nothing, which reads to an agent as "this county has no such law"
rather than as "we never built this".

REGISTER_SCHEME COMPILES WITH NO FLAGS. `re.IGNORECASE` is not applied, so every pattern
spells out its own case handling — a lesson oregon-records-retention left a note about and
oregon-audits repeated rather than relearned.
"""
import pathlib
import re

import yaml

from corpus_toolkit.mcp.framework import register_scheme

_ROOT = pathlib.Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------- inbound: county code
#
# Abbreviations are read from the registry rather than hardcoded here, so adding county #8
# is a registry line and not an edit to this file. A county with no `code_abbr` simply gets
# no abbreviated scheme, which is correct — 7 of the 36 publish no codified code at all, and
# inventing an abbreviation for them would manufacture a citation form that does not exist.
_registry = yaml.safe_load((_ROOT / "_meta" / "counties.yml").read_text())["counties"]

def _chapter_ids(county: str, num: str, nodes: dict | None, kind: str = ""):
    """Every document in `county` belonging to code chapter/title `num`.

    RESOLVED AGAINST THE GRAPH, NOT A TEMPLATE, and that is not a stylistic choice — a flat
    template cannot express what these ids look like. Counties split a chapter across many
    documents and each names them differently:

        lane-code-lc01                      one file per chapter
        lane-land-use-lc16-245-249          one chapter, 23 files, by section range
        multnomah-code-chapter-11-revenue-and-taxation
        washington-code-tit1gepr            Municode node ids
        jackson-code-ch1020

    So a citation to "Lane Code Chapter 16" must return the 23 documents that make it up, not
    one guessed id that exists in no county. Matching a prefix against the real node set is
    the only thing that works across all six, and it degrades honestly: a chapter this corpus
    does not hold returns nothing rather than a confident dead id.
    """
    if not nodes:
        return []
    n = re.escape((num.lower().lstrip("0") or "0"))
    c = re.escape(county)
    # THE CITATION'S OWN NOUN DISCRIMINATES. Washington's Municode node ids include both
    # `ch01` (the CHARTER) and `tit1gepr` (Title 1), so "Title 1" matching a `ch` prefix
    # returns the charter alongside the title — two different instruments, one of which the
    # reader did not ask for. A corpus of law does not get to be approximately right about
    # which instrument it returns, so the word the citation actually used is honoured.
    kind = kind.lower()
    want_ch = not kind.startswith("tit")
    want_tit = not kind.startswith("ch")

    pats = [
        # An explicit code marker in the id — `lc16`, `ch1020`, `tit1gepr` — may appear in
        # ANY family, because several counties keep land-use chapters inside the county code
        # (Lane's LC10/12/13/16) and a citation to "Lane Code Chapter 16" must still reach
        # them. Municode node ids run letters straight on after the number (`tit1gepr`), so
        # that form allows a trailing alpha run where the others require a boundary.
        *([re.compile(rf"^{c}-(?:code|land-use|orders)-(?:lc|ch)0*{n}(?:[-._]|$)")]
          if want_ch else []),
        *([re.compile(rf"^{c}-(?:code|land-use|orders)-tit0*{n}[a-z]*$")]
          if want_tit else []),
        # A bare `chapter-N` id carries no marker saying which instrument it belongs to, so
        # it is honoured ONLY in the code/orders families. Multnomah has both
        # `multnomah-code-chapter-11-revenue-and-taxation` and
        # `multnomah-land-use-chapter-11-public-facilities`, and a citation to the County
        # Code must not return a chapter of the comprehensive plan.
        re.compile(rf"^{c}-(?:code|orders)-chapter-0*{n}(?:[-._]|$)"),
    ]
    return sorted(i for i in nodes if any(p.match(i) for p in pats))


for _c in _registry:
    _slug = _c["slug"]                              # e.g. lane-county  (registry slug)
    _short = _c["short_name"]                       # e.g. Lane
    _county = _slug[:-len("-county")]               # e.g. lane  (the id prefix documents use)
    _abbr = _c.get("code_abbr")                     # e.g. LC — optional, absent by default

    # Spelled-out form: "Lane County Code Chapter 16", "Lane Code Chapter 16".
    # `County` is optional because several counties drop it in their own text.
    register_scheme(
        f"{_slug}-code-chapter",
        rf"{re.escape(_short)}\s+(?:County\s+)?Code,?\s+(?P<kind>Chapter|Title|Ch\.?)\s*"
        rf"(?P<num>[\dA-Za-z.]+)",
        resolver=(lambda m, nodes=None, c=_county:
                  _chapter_ids(c, m["num"], nodes, m.groupdict().get("kind") or "")),
    )

    if _abbr:
        # Abbreviated form: "LC 4.100", "DCC 8.20". Requires a dot-separated number so a
        # bare "LC 4" does not match a chapter reference the corpus cannot resolve
        # precisely — and so the pattern does not collide with unrelated prose.
        #
        # No county has `code_abbr` set yet, deliberately: writing "MCC" or "WCC" from
        # memory would manufacture a citation form the county may not use, which is the
        # fabricated-citation failure this corpus exists not to commit. Each is added only
        # once its own documents are seen using it.
        register_scheme(
            f"{_slug}-code-cite",
            rf"\b{re.escape(_abbr)}\s+(?P<num>\d+[A-Za-z]?)\.(?P<sec>[\d.]+)",
            resolver=(lambda m, nodes=None, c=_county: _chapter_ids(c, m["num"], nodes)),
        )

# ---------------------------------------------------------------- inbound: orders
#
# ORDER vs RESOLUTION vs COURT ORDER is a real distinction, not a synonym set. Six of the 36
# counties are governed by a County Court rather than a Board of Commissioners, and their
# enactments are court orders and journal entries. The pattern accepts all three nouns
# because a citing document will use whichever its own county uses, and the corpus should not
# require the reader to know the county's governance form to look something up.
register_scheme(
    "county-order",
    r"(?:Board\s+)?(?:Court\s+)?(?:Order|Resolution|Ordinance)\s+"
    r"(?:No\.?\s*)?(?P<num>\d{2,4}-\d{1,4})",
    resolver=lambda m, nodes=None: (
        [n for n in (nodes or {}) if n.endswith(f"-{m['num'].lower()}")]
        or [f"order-{m['num'].lower()}"]),
)

# ---------------------------------------------------------------- outbound: state law
#
# THE EDGE THAT MAKES THIS CORPUS MORE THAN A DOCUMENT DUMP. A county ordinance should walk
# up to the state law it implements, and land use is the densest case: ORS 197 and the
# OAR 660 statewide planning goals bind county comprehensive plans directly, so there the
# state -> county relationship is a legal requirement rather than a theme.
#
# Registered together with the `siblings:` entry in _meta/corpus.yml, because the two must
# land together — a `corpus=` scheme with no matching sibling matches a citation and then
# resolves nothing, which reads as a genuine "not found" rather than as missing config.
#
# The >= 3 digit section requirement is carried over from oregon-audits for the same reason:
# PDF extraction splits long numbers across line breaks, and a looser pattern resolves a
# truncated "ORS 197.2" confidently to a section that does not exist.
register_scheme("ors-section", r"ORS\s+(?P<num>\d+[A-Z]?\.\d{3,})",
                "ors-{num}", corpus="executive-regulatory-frameworks")
register_scheme("oar-rule", r"OAR\s+(?P<num>\d{3}-\d{3}-\d{4})",
                "oar-{num}", corpus="executive-regulatory-frameworks")
register_scheme("oar-division", r"OAR\s+(?P<div>\d{3}-\d{3})(?!-\d)",
                resolver=lambda m: ([], f"OAR division {m['div']} — cite a specific rule "
                                         f"(OAR {m['div']}-NNNN) to resolve it"),
                corpus="executive-regulatory-frameworks")
