"""Grant County — CivicPlus DocumentCenter, and a COUNTY COURT county with no codified code.

7,093 people, 33rd largest. General law, governed by a **County Court** — a county judge
sitting with two commissioners — so its enactments are court orders and journal entries.
`check_guardrails` rejects any document here naming a Board of Commissioners.

NO CODIFIED CODE, MEASURED. The survey ruled Grant out of Municode via the client API, found
no eCode360 presence, and located nothing self-hosted: its law is a paper series held at the
courthouse. That is a fact about Grant County — the second such in this corpus after Columbia
— and not a gap in our reach.

Verified 2026-08-01: 4 policy documents, 20 documents on the general index. Honest
User-Agent, HTTP 200.
"""

_DC = r'href="(/DocumentCenter/View/\d+/[^"]*)"'

PROFILE = {
    "slug": "grant",
    "name": "Grant",
    "discovery": "link-list",
    "site": "https://grantcountyoregon.net",
    "crawl": {
        "decision": "proceed",
        "checked": "2026-08-01",
        "basis": "No AI-agent directive; DocumentCenter open. Nothing to decide.",
        "hosts": [
            {"host": "grantcountyoregon.net",
             "robots_url": "https://grantcountyoregon.net/robots.txt",
             "ai_block": False, "content_signal": None, "notes": "No named AI agents."},
        ],
    },
    "upstream_signal": "No feed; a replaced document gets a new DocumentCenter id.",
    "families": {
        "policies": {"listing_url": "https://grantcountyoregon.net/540/Policies",
                     "link_re": _DC, "format": "pdf", "dedupe": "name-highest-id"},
        "land-use": {"listing_url": "https://grantcountyoregon.net/252/Documents",
                     "link_re": _DC, "format": "pdf", "dedupe": "name-highest-id"},
        "code": {
            "skip": (
                "MEASURED ABSENCE. Grant County publishes no codified code — Municode ruled "
                "out via the client API, no eCode360 presence, nothing self-hosted; its law "
                "is a paper series at the courthouse. Recorded `none-found` in "
                "corpus-seeds/oregon-counties.survey.yml. A fact about Grant County, not "
                "about our reach."),
        },
        "orders": {
            "skip": (
                "County Court orders are in AgendaCenter, a per-meeting system rather than "
                "an index of adopted instruments. Note the noun: Grant is governed by a "
                "County Court, so these are court orders. Deferred."),
        },
    },
}
