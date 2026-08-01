"""Clatsop County — eCode360 (General Code), plus self-hosted policies and land use.

41,043 people, 19th largest, general law, Board of Commissioners.

FIRST eCODE360 COUNTY, and the reason `discover_ecode360` exists. General Code is the
largest commercial code vendor among Oregon counties — four of 36, ahead of Municode's
three — so the mode pays for itself here and again at Crook, and again at Lake later.

The survey recorded this county's code as HTTP 403. It is not: `ecode360.com` serves the
honest, self-identifying agent HTTP 200. The survey's 403 came from a thinner request, which
is the same trap `src/fetch.py`'s Accept headers exist to avoid — worth stating, because a
recorded 403 that is really a header problem would have written this county off as blocked
when it is simply published.

Verified 2026-08-01: 18 TOC nodes at ecode360.com/CL4917, one of which is "(Reserved)" and
carries no law. Honest User-Agent, HTTP 200.
"""

_DC = r'href="(/DocumentCenter/View/\d+/[^"]*)"'

PROFILE = {
    "slug": "clatsop",
    "name": "Clatsop",
    "discovery": "ecode360",
    "site": "https://clatsopcounty.gov",
    "crawl": {
        "decision": "proceed",
        "checked": "2026-08-01",
        "basis": (
            "ecode360.com serves HTTP 200 to the honest agent and states no AI-agent "
            "directive of its own. The survey's recorded 403 for this county was a thin "
            "request without Accept headers, not a refusal — re-checked before building."),
        "hosts": [
            {"host": "ecode360.com", "robots_url": "https://ecode360.com/robots.txt",
             "ai_block": False, "content_signal": None,
             "notes": "General Code storefront. 200 to the honest agent; the survey's 403 "
                      "was a header artefact."},
            {"host": "clatsopcounty.gov", "robots_url": "https://clatsopcounty.gov/robots.txt",
             "ai_block": False, "content_signal": None,
             "notes": "County's own site; policies and land use. No named AI agents."},
        ],
    },
    "upstream_signal": (
        "No feed. eCode360 guids are stable across amendments, so content drift is caught by "
        "re-hashing each Title; a new Title appears as a new TOC node."),
    "families": {
        "code": {"discovery": "ecode360", "toc_url": "https://ecode360.com/CL4917",
                 "format": "html"},
        "policies": {"listing_url": "https://clatsopcounty.gov/229/County-Policies",
                     "link_re": _DC, "format": "pdf", "dedupe": "name-highest-id",
                     "discovery": "link-list"},
        "land-use": {"listing_url":
                     "https://clatsopcounty.gov/329/Zoning-Land-Use-Regulations",
                     "link_re": _DC, "format": "pdf", "dedupe": "name-highest-id",
                     "discovery": "link-list"},
        "orders": {
            "skip": (
                "Board records are in a CivicPlus WebOpen meetings portal "
                "(clatsopcountyor.civicpluswebopen.com), a per-meeting agenda system rather "
                "than an index of adopted instruments. Deferred, not blocked."),
        },
    },
}
