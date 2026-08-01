#!/usr/bin/env python3
"""Citation schemes this corpus resolves, registered with the MCP framework.

Loaded via `plugins.citation_module` in _meta/corpus.yml. Importing this module is the whole
contract — `register_scheme` calls happen at import time.

THE HARD PART HERE IS THAT COUNTY CITATION IS NOT UNIFORM, and pretending otherwise would be
a fabrication that looks official. Real forms measured across the 36-county survey include:

    LC 4.100                Lane Code, abbreviated
    Lane Code Chapter 4     the same instrument, spelled out
    DCC 8.20                Deschutes County Code
    MCC 5.100               Multnomah County Code

There is no statewide convention, no statutory citation form, and no shared abbreviation
registry. So this module registers ONE PATTERN PER COUNTY, built from the abbreviations that
county actually uses, rather than a single clever regex that would match a form no county
writes and resolve it confidently to the wrong document.

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

for _c in _registry:
    _slug = _c["slug"]                              # e.g. lane-county
    _short = _c["short_name"]                       # e.g. Lane
    _abbr = _c.get("code_abbr")                     # e.g. LC — optional

    # Spelled-out form: "Lane County Code Chapter 16", "Lane Code Chapter 16".
    # `County` is optional because several counties drop it in their own text.
    register_scheme(
        f"{_slug}-code-chapter",
        rf"{re.escape(_short)}\s+(?:County\s+)?Code,?\s+(?:Chapter|Ch\.?)\s*(?P<num>[\dA-Za-z.-]+)",
        resolver=(lambda m, s=_slug: [f"{s}-code-chapter-{m['num'].lower()}",
                                      f"{s}-code-{m['num'].lower()}"]),
    )

    if _abbr:
        # Abbreviated form: "LC 4.100", "DCC 8.20". Requires a dot-separated number so a
        # bare "LC 4" does not match a chapter reference the corpus cannot resolve
        # precisely — and so the pattern does not collide with unrelated prose.
        register_scheme(
            f"{_slug}-code-cite",
            rf"\b{re.escape(_abbr)}\s+(?P<chap>\d+[A-Za-z]?)\.(?P<sec>[\d.]+)",
            resolver=(lambda m, s=_slug: [f"{s}-code-chapter-{m['chap'].lower()}",
                                          f"{s}-code-{m['chap'].lower()}"]),
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
