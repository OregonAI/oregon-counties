"""Hood River County — self-hosted PDFs under a legacy `/vertical/Sites/{GUID}/` tree.

23,764 people, 26th largest, general law, Board of Commissioners.

THE COLUMBIA RIVER GORGE, AND THE OPPOSITE CHOICE FROM WASCO. Part of Hood River lies in the
Columbia River Gorge National Scenic Area, governed by federal law (16 U.S.C. 544). Hood
River folds that regime INTO its ordinary zoning ordinance as **Article 75** rather than
maintaining a separate instrument — where Wasco keeps a wholly separate 23-chapter NSA-LUDO
alongside its general LUDO.

Same federal statute, opposite structural choice, and no way to know which without looking.
A pipeline that assumed one land-use document per county would hold the wrong law for part of
Wasco and the right law for Hood River, with nothing distinguishing the two cases.

The `{GUID}` in the path is literal — a legacy CMS artefact — and must be percent-encoded to
be fetchable, which the shared discoverer does.

Verified 2026-08-01: 11 documents on the charter page; honest User-Agent, HTTP 200.
"""

_V = r'href="([^"]*/vertical/Sites/[^"]*\.pdf)"'

PROFILE = {
    "slug": "hood-river",
    "name": "Hood River",
    "discovery": "link-list",
    "site": "https://www.hoodrivercounty.gov",
    "crawl": {
        "decision": "proceed",
        "checked": "2026-08-01",
        "basis": "No AI-agent directive. Nothing to decide.",
        "hosts": [
            {"host": "www.hoodrivercounty.gov",
             "robots_url": "https://www.hoodrivercounty.gov/robots.txt",
             "ai_block": False, "content_signal": None,
             "notes": "No named AI agents. Legacy /vertical/Sites/{GUID}/ document tree; the "
                      "literal braces need percent-encoding."},
        ],
    },
    "upstream_signal": "No feed; re-hash each PDF. Upload paths are stable.",
    "families": {
        "code": {"listing_url": "https://www.hoodrivercounty.gov/county-charter",
                 "link_re": _V, "format": "pdf"},
        "land-use": {
            "skip": (
                "The land-use index is behind an `index.asp?SEC=<GUID>` query rather than a "
                "path, so it needs a per-page walk the generic mode does not do. Worth "
                "noting what is deferred: Hood River's zoning ordinance carries the Columbia "
                "River Gorge National Scenic Area regime as Article 75, which is the "
                "federal-to-county edge this corpus most wants. Real work, not blocked."),
        },
        "orders": {"skip": "Board records are behind the same index.asp?SEC= query form. "
                           "Deferred."},
        "policies": {"skip": "Administrative policy sits in the same /vertical/Sites/ tree "
                             "as the charter and is captured under `code`; separating them "
                             "needs a per-document judgement rather than a guess."},
    },
}
