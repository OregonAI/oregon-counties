"""Klamath County — CivicPlus DocumentCenter; the code is ONE master PDF.

70,438 people, 15th largest, general law, Board of Commissioners.

Unlike every other county in this build, Klamath does not publish its code chapter by
chapter. The County Counsel page carries a single `Master-Code` PDF plus an ordinance index,
and that master document IS the code. Splitting it into chapters would be our editorial act,
not the county's, so it is held as the county publishes it — one document — and a chapter-level
citation resolves to the whole code rather than to a chapter this corpus invented.

That is a real limitation and it is stated rather than papered over: an agent asking for
"Klamath County Code Chapter 5" gets the master code and has to read for the chapter.
Splitting it is a legitimate later increment, done deliberately with the split points
recorded, and not a side effect of ingestion.

Verified 2026-07-31: Master-Code and ORDINDEX both present on /161/County-Counsel; land-use
and policies pages each carry their own DocumentCenter sets. Honest User-Agent, HTTP 200.
"""

_DC = r'href="(/DocumentCenter/View/\d+/[^"]*)"'

PROFILE = {
    "slug": "klamath",
    "name": "Klamath",
    "discovery": "link-list",
    "site": "https://www.klamathcounty.org",
    "crawl": {
        "decision": "proceed",
        "checked": "2026-07-31",
        "basis": "No AI-agent directive; DocumentCenter open. Nothing to decide.",
        "hosts": [
            {"host": "www.klamathcounty.org",
             "robots_url": "https://www.klamathcounty.org/robots.txt",
             "ai_block": False, "content_signal": None,
             "notes": "No named AI agents; /DocumentCenter open."},
        ],
    },
    "upstream_signal": (
        "The master code is republished as a new DocumentCenter id on codification, so the "
        "id changing IS the amendment signal — coarse, but exact."),
    "families": {
        "code": {"listing_url": "https://www.klamathcounty.org/161/County-Counsel",
                 "link_re": _DC, "format": "pdf", "dedupe": "name-highest-id"},
        "land-use": {
            "skip": (
                "The Land Development Code page carries 14 `/DocumentCenter/View/<id>` links "
                "with no name segment, and those ids return text/html rather than PDFs — "
                "they are viewer pages, not documents. Enumerating them would fill the "
                "corpus with HTML chrome titled by a number. Reaching the real files needs a "
                "viewer-aware fetch; deferred deliberately, and NOT recorded as an absence "
                "at Klamath County, which plainly publishes a land development code."),
        },
        "policies": {"listing_url":
                     "https://www.klamathcounty.org/279/Policies-Union-Contracts-Compensation-Ta",
                     "link_re": _DC, "format": "pdf", "dedupe": "name-highest-id"},
        "orders": {
            "skip": (
                "Board orders are in AgendaCenter, a per-meeting agenda system rather than "
                "an index of adopted instruments. Reachable, not blocked; deferred."),
        },
    },
}
