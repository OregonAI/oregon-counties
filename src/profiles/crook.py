"""Crook County — eCode360 (General Code), reusing the mode written for Clatsop.

27,336 people, 21st largest, general law, Board of Commissioners.

Second eCode360 county, and configuration rather than code: a TOC url and nothing else.

THE STALE LINK THE SURVEY CAUGHT. Crook's own County Code page still links a dead vendor
URL — the county migrated to eCode360 and did not update its own pointer. Ingest goes to
ecode360.com/CR4713 directly, which was verified live, rather than following the county's
link and recording a 404 as provenance.

Verified 2026-08-01: TOC nodes present at ecode360.com/CR4713; honest User-Agent, HTTP 200.
"""

_DC = r'href="(/DocumentCenter/View/\d+/[^"]*)"'

PROFILE = {
    "slug": "crook",
    "name": "Crook",
    "discovery": "ecode360",
    "site": "https://crookcountyor.gov",
    "crawl": {
        "decision": "proceed",
        "checked": "2026-08-01",
        "basis": (
            "Same as Clatsop: ecode360.com serves the honest agent HTTP 200 and states no "
            "AI-agent directive. The survey's 403 was a thin-request artefact."),
        "hosts": [
            {"host": "ecode360.com", "robots_url": "https://ecode360.com/robots.txt",
             "ai_block": False, "content_signal": None,
             "notes": "General Code storefront; 200 to the honest agent."},
            {"host": "crookcountyor.gov", "robots_url": "https://crookcountyor.gov/robots.txt",
             "ai_block": False, "content_signal": None,
             "notes": "County site; handbook and comprehensive plan. Its own County Code "
                      "page still links the DEAD pre-migration vendor URL — not followed."},
        ],
    },
    "upstream_signal": "No feed; re-hash each Title. New Titles appear as new TOC nodes.",
    "families": {
        "code": {"discovery": "ecode360", "toc_url": "https://ecode360.com/CR4713",
                 "format": "html"},
        "policies": {"listing_url": "https://crookcountyor.gov/1420/Handbook",
                     "link_re": _DC, "format": "pdf", "dedupe": "name-highest-id",
                     "discovery": "link-list"},
        "land-use": {"listing_url":
                     "https://crookcountyor.gov/1318/Crook-County-Comprehensive-Plan",
                     "link_re": _DC, "format": "pdf", "dedupe": "name-highest-id",
                     "discovery": "link-list"},
        "orders": {
            "skip": (
                "Board orders are behind a CivicClerk API (crookcoor.api.civicclerk.com/v1/"
                "Events), a meetings service rather than an index of adopted instruments. "
                "Deferred, not blocked."),
        },
    },
}
