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
        # RE-ENABLED 2026-08-01, for the same reason as Yamhill's orders.
        #
        # Curry's county code is a well-defined set of 65 documents of which only 5 extract
        # (8%); the rest are scanned images. Publishing the 8% would have shown an arbitrary
        # slice of a countable whole. With `ocr_recover.py` in place that trade-off is gone —
        # the scans get a real attempt, and the two-engine gates decide per document.
        #
        # Curry is the county whose malformed hrefs (`href= "..."` with a space, plus a root
        # <base> tag) would silently drop every document under a strict regex, so the loose
        # pattern below is load-bearing rather than defensive.
        "code": {"listing_url": "https://www.currycountyor.gov/government/county_code.php",
                 "link_re": _PDF, "format": "pdf"},
        "land-use": {"listing_url":
                     "https://www.currycountyor.gov/departments/community_development_department/index.php",
                     "link_re": _PDF, "format": "pdf"},
        "orders": {"skip": "Board records are a meeting listing rather than an index of "
                           "adopted instruments. Deferred."},
        "policies": {"skip": "The survey's admin-policy page is a jobs and RFP index, not a "
                             "policy set. Deferred rather than mislabelled."},
    },
}
