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
        # CORRECTED 2026-08-01. This family was previously skipped on the claim that its
        # bare `/DocumentCenter/View/<id>` links "return text/html rather than PDFs — they
        # are viewer pages, not documents". That was WRONG, and the error was in the method:
        # the diagnosis used `curl -I`, and this host answers HEAD with text/html while
        # answering GET with application/pdf. Fourteen real land-use documents were written
        # off on a HEAD response.
        #
        # `resolve_names` asks the server for each nameless link's Content-Disposition
        # filename, so they land as documents with real titles rather than as "2029".
        "land-use": {"listing_url": "https://www.klamathcounty.org/725/Land-Development-Code",
                     "link_re": r'href="(/DocumentCenter/View/\d+(?:/[^"]*)?)"',
                     "format": "pdf", "resolve_names": True,
                     "dedupe": "name-highest-id"},
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
