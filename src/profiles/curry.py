"""Curry County — self-hosted PDFs, and the county whose HTML broke a naive link regex.

22,774 people, 27th largest, general law, Board of Commissioners.

THE MALFORMED-HREF CASE the shared discoverer was written to survive. Curry writes
`href= "..."` with a space after the equals sign, and resolves bare filenames against a root
`<base>` tag. A strict regex silently drops every document here and produces a false
`none-found` — a county reported as publishing nothing when it publishes a full code. That
is why `discover_link_list` resolves against `<base>` and tolerates loose quoting rather than
string-joining paths.

Verified 2026-08-01: county_code.php serves the honest agent HTTP 200.
"""

# Deliberately loose on the space after `=`, which is what Curry actually emits.
_PDF = r'href=\s*"([^"]*\.pdf[^"]*)"'

PROFILE = {
    "slug": "curry",
    "name": "Curry",
    "discovery": "link-list",
    "site": "https://www.currycountyor.gov",
    "crawl": {
        "decision": "proceed",
        "checked": "2026-08-01",
        "basis": "No AI-agent directive. Nothing to decide.",
        "hosts": [
            {"host": "www.currycountyor.gov",
             "robots_url": "https://www.currycountyor.gov/robots.txt",
             "ai_block": False, "content_signal": None,
             "notes": "No named AI agents. Writes href with a space and uses a <base> tag — "
                      "handled by the shared discoverer, not by a Curry-specific hack."},
        ],
    },
    "upstream_signal": "No feed; re-hash each PDF. New documents appear in the index.",
    "families": {
        # MEASURED AND SKIPPED, on the same rule as Yamhill's ordinances. Curry's county
        # code is a WELL-DEFINED SET of 65 documents, of which 5 extract (8%) — the rest are
        # scanned images with no text layer. Ingesting the 8% would show an arbitrary slice
        # of a countable whole under a healthy-looking document count, shaped by which
        # chapters happened to be typed rather than photographed.
        #
        # Compare Wasco, which IS kept at 23%: that index is a mixed decades-deep archive
        # with no defined denominator, so what extracts is useful rather than a misleading
        # sample. The distinction is whether the corpus can be read as claiming coverage of
        # a set it only partly holds.
        #
        # NOT an absence at Curry County, which plainly publishes a full code. This is OCR.
        "code": {
            "skip": (
                "92% of Curry's 65 county code documents are scanned images with no text "
                "layer (only 5 extract). Ingesting the remainder would present an arbitrary "
                "slice of a well-defined set under a healthy count. Needs OCR — a "
                "corpus-wide capability decision — and is NOT an absence at Curry County."),
        },
        "land-use": {"listing_url":
                     "https://www.currycountyor.gov/departments/community_development_department/index.php",
                     "link_re": _PDF, "format": "pdf"},
        "orders": {"skip": "Board records are a meeting listing rather than an index of "
                           "adopted instruments. Deferred."},
        "policies": {"skip": "The survey's admin-policy page is a jobs and RFP index, not a "
                             "policy set. Deferred rather than mislabelled."},
    },
}
