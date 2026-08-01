"""Sherman County — 2,002 people, a County Court, and CivicPlus DocumentCenter.

35th of 36 by population. General law, governed by a **County Court**.

The survey recorded Sherman's code platform as CivicPlus Municipal Code Online, and the
smallest-county wall it expected — a Box or Drive container — did not materialise: what is
here is a plain DocumentCenter, reachable and enumerable.

A useful counterexample to the assumption that small counties are hard. Sherman is 700 times
smaller than Multnomah and no harder to ingest; the difficulty in this corpus tracks
PLATFORM, not population.

Verified 2026-08-01: 12 planning documents; honest User-Agent, HTTP 200.
"""

_DC = r'href="(/DocumentCenter/View/\d+/[^"]*)"'

PROFILE = {
    "slug": "sherman",
    "name": "Sherman",
    "discovery": "link-list",
    "site": "https://www.shermancountyor.gov",
    "crawl": {
        "decision": "proceed",
        "checked": "2026-08-01",
        "basis": "No AI-agent directive; DocumentCenter open. Nothing to decide.",
        "hosts": [
            {"host": "www.shermancountyor.gov",
             "robots_url": "https://www.shermancountyor.gov/robots.txt",
             "ai_block": False, "content_signal": None, "notes": "No named AI agents."},
        ],
    },
    "upstream_signal": "No feed; a replaced document gets a new DocumentCenter id.",
    "families": {
        "land-use": {"listing_url": "https://www.shermancountyor.gov/233/Planning-Department",
                     "link_re": _DC, "format": "pdf", "dedupe": "name-highest-id"},
        "code": {
            "skip": (
                "The survey recorded a CivicPlus Municipal Code Online platform for Sherman, "
                "but no MCO S3 prefix was located for this county and the DocumentCenter "
                "index does not carry a codified code. Not established either way — which is "
                "neither a measured absence nor a block, and is recorded as the open "
                "question it is."),
        },
        "orders": {"skip": "County Court records are in AgendaCenter (County-Court-3), a "
                           "per-meeting system rather than an index of adopted orders."},
        "policies": {"skip": "The survey's admin-policy pointer is a single DocumentCenter "
                             "id rather than a policy index; one document does not "
                             "characterise the family. Deferred."},
    },
}
