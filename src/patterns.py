"""Shared text patterns. NO DEPENDENCIES, DELIBERATELY — not even inside this package.

This module exists because of a CI failure worth not repeating. `check_guardrails.py` needs
the draft-detection patterns, and the natural way to guarantee it uses the SAME ones as the
discovery filter was to import them from `src/fetch.py`. That worked locally and broke the
`generated` job the moment `fetch.py` grew an `httpx` import: a gate that reads committed
Markdown was suddenly unable to run without the HTTP stack installed.

The sync guarantee was right; the coupling was wrong. Both sides import from here instead, so
they still cannot drift, and neither one drags the other's dependencies along.

Keep this module free of imports. Anything that needs a third-party package does not belong.
"""
from __future__ import annotations

# Filenames that are DRAFTS sitting beside adopted text in the same directory. Measured in
# five counties: Lane (APM `...Issue2REDLINE.pdf` next to `...CURRENT.pdf`), Clackamas
# (`zdoproposed`), Lincoln, Baker (`-DRAFT`), Gilliam (a redline employee handbook NEWER and
# LARGER than the adopted one, so "take the most recent" is actively wrong there).
#
# `draft`/`proposed` ARE ONLY DRAFT MARKERS IN A VERSION POSITION — leading, trailing, or
# delimited — never mid-sentence. Multnomah adopts resolutions ABOUT proposals: "Resolution
# Referring Charter Review Committee Proposed Amendments To The Voters" and "Resolution
# Adopting ... For Inclusion In The Draft Environmental Impact Statement" are adopted law
# whose SUBJECT is a proposal. A bare \bproposed\b flagged 17 such documents as drafts. The
# word describes what an instrument is about; the position tells you whether it describes the
# instrument.
DRAFT_PATTERNS = (
    r"redline",                      # unambiguous wherever it appears
    r"\bissue\s*\d+\b",              # Lane's APM revision markers
    r"zdoproposed",                  # Clackamas' proposed-amendment pages
    # Trailing version marker. The optional extension group matters: without it
    # `employee-handbook-DRAFT.pdf` slips through, because `.pdf` sits between the marker and
    # the end of the string.
    r"[-_.(\[]\s*(?:draft|proposed)\s*[-_.)\]]*\s*(?:\.[a-z0-9]{2,4})?$",
    r"^\s*(?:draft|proposed)\s*[-_.]",                     # leading version marker
)
