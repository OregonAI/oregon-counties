"""Yamhill County — CivicPlus DocumentCenter, all four families published.

110,886 people, 10th largest, general law, Board of Commissioners.

The friendliest county of tranche 2: every family is an HTML index of
`/DocumentCenter/View/<id>/<NAME>` links, and the names carry the citation
(`YCC-1005-YAMHILL-COUNTY-BUILDING-CODE-PDF`), so ids come out meaningful without a custom
resolver.

THE AI BLOCK IS ON THE COUNTY'S OWN SITE HERE, not a vendor's. yamhillcounty.gov carries the
Cloudflare-managed AI list naming ClaudeBot with `Disallow: /`. That is a different case from
Municode: the county is the author of this law, so the reasoning that a vendor is only a host
does not apply — the publisher itself is the one stating a preference.

It is still ingested, under the same operator decision (PLAN.md Phase 12), because the
decision was about the text of county law rather than about who happens to host it, and a
county's own published law is the plainest case of a public record. But the distinction is
recorded rather than glossed: `ai_block: true` with a note saying whose block it is, so a
reviewer sees that this one is the county's own directive and can overrule it if they read it
differently. The honest User-Agent is served HTTP 200 either way; nothing is disguised.

THE MIRROR TRAP. `or-yamhillcounty.civicplus.com` serves identical pages under a blanket
`Disallow: /`. Ingest must use the `.gov` host — pulling the mirror would be taking the same
documents from a host that refuses everyone, which is a real distinction and not a formality.

Verified 2026-07-31: 88 code documents on the code index, honest User-Agent, HTTP 200.
"""

_DC = r'href="(/DocumentCenter/View/\d+/[^"]*)"'

PROFILE = {
    "slug": "yamhill",
    "name": "Yamhill",
    "discovery": "link-list",
    "site": "https://www.yamhillcounty.gov",
    "crawl": {
        "decision": "proceed",
        "checked": "2026-07-31",
        "basis": (
            "yamhillcounty.gov names ClaudeBot and disallows it — and unlike Municode or "
            "General Code, the publisher here IS the county, so the 'vendor is only a host' "
            "reasoning does not apply. Ingested anyway under the Phase 12 decision, which "
            "was about the text of county law rather than about who hosts it, and a "
            "county's own published law is the plainest public record there is. Flagged "
            "rather than glossed, because a reviewer may read this one differently. Served "
            "HTTP 200 to the honest agent; nothing disguised. The civicplus.com mirror, "
            "which disallows everyone, is deliberately NOT used."),
        "hosts": [
            {"host": "www.yamhillcounty.gov",
             "robots_url": "https://www.yamhillcounty.gov/robots.txt",
             "ai_block": True,
             "content_signal": None,
             "notes": "Cloudflare-managed AI list: ClaudeBot, CCBot, GPTBot, Amazonbot, "
                      "Applebot-Extended, Bytespider, Google-Extended, each Disallow: /. "
                      "THE COUNTY'S OWN DIRECTIVE, not a vendor's — see basis."},
            {"host": "or-yamhillcounty.civicplus.com", "robots_url": None, "ai_block": False,
             "content_signal": None,
             "notes": "Mirror serving identical pages under a blanket Disallow: /. NOT used."},
        ],
    },
    "upstream_signal": (
        "No feed. DocumentCenter ids are stable and a replaced document gets a new id, so "
        "diffing the id set on each index detects both additions and replacements."),
    "families": {
        "code": {"listing_url": "https://www.yamhillcounty.gov/1127/Yamhill-County-Code",
                 "link_re": _DC, "format": "pdf"},
        # MEASURED AND SKIPPED. Yamhill publishes its adopted ordinances as SCANNED IMAGES:
        # 338 of 360 (94%) extract to zero characters, confirmed by sampling four at random
        # — 7 to 12 pages each, application/pdf, no text layer at all. They are photographs
        # of signed instruments.
        #
        # Ingesting the 6% that happen to carry text would publish an arbitrary slice of the
        # county's ordinance record while STATUS.md reported a healthy-looking count, which
        # is worse than holding none: a reader asking what Yamhill has adopted would get a
        # sample shaped by which documents were typed rather than scanned.
        #
        # This is not an absence at Yamhill and must never be reported as one. It is an OCR
        # problem, and OCR is a deliberate capability decision for this corpus rather than
        # something to bolt onto one county.
        "orders": {
            "skip": (
                "94% of Yamhill's 360 adopted ordinances are scanned images with no text "
                "layer (338 of 360 extract to 0 characters; sampled and confirmed). "
                "Ingesting the remainder would publish an arbitrary slice of the ordinance "
                "record under a healthy-looking count. Needs OCR, which is a corpus-wide "
                "capability decision — NOT an absence at Yamhill County."),
        },
        "policies": {"listing_url":
                     "https://www.yamhillcounty.gov/1528/County-Wide-Policies-and-Procedures",
                     "link_re": _DC, "format": "pdf"},
        "land-use": {"listing_url": "https://www.yamhillcounty.gov/297/Planning-Ordinances",
                     "link_re": _DC, "format": "pdf"},
    },
}
