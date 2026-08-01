"""Lincoln County — CivicPlus DocumentCenter, self-hosted.

51,212 people, 18th largest, general law, Board of Commissioners.

THE MUNICODE TRAP THIS COUNTY IS THE EXAMPLE OF. Lincoln has a live Municode client record
(ClientID 16263) listing a "Code of Ordinances" product — and it is an EMPTY SHELL:
`latestUpdatedDate: null`, `hasOrdbank: false`, `publicationId: null`, content endpoints
returning 204/404. The survey checked it against genuinely live Oregon clients before
concluding that. Recording Municode as Lincoln's code source would have been a fabricated
source that resolved to nothing while looking authoritative.

The real code is self-hosted PDFs on the county's own DocumentCenter, which is what this
profile reads.

Verified 2026-08-01: 12 code chapters, 20 land-use documents, 1 personnel rules PDF.
Honest User-Agent, HTTP 200.
"""

_DC = r'href="(/DocumentCenter/View/\d+/[^"]*)"'

PROFILE = {
    "slug": "lincoln",
    "name": "Lincoln",
    "discovery": "link-list",
    "site": "https://www.co.lincoln.or.us",
    "crawl": {
        "decision": "proceed",
        "checked": "2026-08-01",
        "basis": "No AI-agent directive; DocumentCenter open. Nothing to decide.",
        "hosts": [
            {"host": "www.co.lincoln.or.us",
             "robots_url": "https://www.co.lincoln.or.us/robots.txt",
             "ai_block": False, "content_signal": None,
             "notes": "No named AI agents. NOTE: Lincoln's Municode client 16263 is an "
                      "empty shell and is deliberately NOT used as a source."},
        ],
    },
    "upstream_signal": (
        "No feed. A replaced chapter gets a new DocumentCenter id, so diffing the id set "
        "detects both additions and replacements."),
    "families": {
        "code": {"listing_url": "https://www.co.lincoln.or.us/182/Lincoln-County-Code",
                 "link_re": _DC, "format": "pdf", "dedupe": "name-highest-id"},
        "land-use": {"listing_url":
                     "https://www.co.lincoln.or.us/1273/Zoning-Code-and-Comprehensive-Plan",
                     "link_re": _DC, "format": "pdf", "dedupe": "name-highest-id"},
        "policies": {"listing_url":
                     "https://www.co.lincoln.or.us/987/Lincoln-County-Personnel-Rules-PDF",
                     "link_re": _DC, "format": "pdf", "dedupe": "name-highest-id"},
        "orders": {
            "skip": (
                "The board-orders page the survey found is a historical library rather than "
                "an index of adopted instruments. Deferred, not blocked."),
        },
    },
}
