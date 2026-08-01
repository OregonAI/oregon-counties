"""Josephine County — code unreachable, land use taken from the county's own domain.

88,276 people, 13th largest, general law, Board of Commissioners.

TWO SOURCES, TWO OUTCOMES, and the split is the point.

Its codified code migrated to eCode360 (JO4733) and its own site still links the dead Code
Publishing URL. Both vendor paths return HTTP 403 Cloudflare managed challenge to an
honestly-identified agent, so the code is `unavailable` — a fact about our access, not about
Josephine, which plainly publishes its code.

Its COMPREHENSIVE PLAN is a different matter: `josephinecounty.gov` serves the honest agent
HTTP 200 and publishes the complete plan book, the 2005 Goals & Policies, and the 1985 LCDC
acknowledgement directly. Those are ingested.

This county is the clearest case for a rule the corpus learned late: **check the county's own
domain before recording a county as unreachable.** The vendor being blocked said nothing
about the county, and treating the two as one cost Josephine's land use for three tranches.

The LCDC acknowledgement is worth having on its own terms — it is the state's formal finding
that the plan complies with the statewide planning goals, which is the ORS 197 / OAR 660 edge
this corpus exists to make walkable.

Verified 2026-08-01: comprehensive_plan.php serves the honest agent HTTP 200; three
instruments present.
"""

_PDF = r'href="([^"]*\.pdf[^"]*)"'

PROFILE = {
    "slug": "josephine",
    "name": "Josephine",
    "discovery": "link-list",
    "site": "https://www.josephinecounty.gov",
    "crawl": {
        "decision": "proceed",
        "checked": "2026-08-01",
        "basis": (
            "The county's own site serves the honest agent HTTP 200 and names only GPTBot in "
            "robots — not us — so there is no directive here to weigh. Its VENDOR code hosts "
            "(eCode360 and the stale Code Publishing link) both return HTTP 403 Cloudflare "
            "managed challenge, and getting past that would mean misrepresenting what we "
            "are; the code family is skipped for that reason and no other."),
        "hosts": [
            {"host": "www.josephinecounty.gov",
             "robots_url": "https://www.josephinecounty.gov/robots.txt",
             "ai_block": True, "content_signal": None,
             "notes": "Names GPTBot with Disallow: / — and NOT ClaudeBot or any agent we "
                      "present as. Recorded as an AI block because it is one, but it is not "
                      "a directive addressed to this crawler."},
            {"host": "ecode360.com", "robots_url": "https://ecode360.com/robots.txt",
             "ai_block": False, "content_signal": None,
             "notes": "JO4733. Returns 403 Cloudflare challenge for this county, unlike "
                      "Clatsop and Crook on the same vendor which serve us fine."},
        ],
    },
    "upstream_signal": (
        "The comprehensive plan PDFs carry `?t=<timestamp>` cache-busters that change on "
        "republication, so diffing the link set detects an amendment without a fetch."),
    "families": {
        # REACHABLE BUT NOT EXTRACTABLE, which is a third outcome distinct from both
        # "blocked" and "not published". All three instruments were fetched successfully
        # over HTTPS and all three are image-only scans with no text layer:
        #
        #   Comprehensive Plan - Complete Book      760 pages,  35 MB, 0 characters
        #   JOCO Goals & Policies 2005               35 pages, 2.2 MB, 0 characters
        #   LCDC Acknowledgement 1985                 1 page,  147 KB, 0 characters
        #
        # So Josephine's land use is an OCR problem, not an access problem — and worth
        # separating, because the county was previously written off as Cloudflare-blocked
        # when in fact its own domain serves us fine and the obstacle is a scanner.
        "land-use": {
            "skip": (
                "Reachable but not extractable. The comprehensive plan (760pp, 35MB), the "
                "2005 Goals & Policies and the 1985 LCDC acknowledgement all fetch over "
                "HTTPS from the county's own domain and all three are image-only scans with "
                "zero characters of text. Needs OCR. NOT a Cloudflare block — that applies "
                "only to the vendor-hosted code — and NOT an absence at Josephine County."),
        },
        "code": {
            "skip": (
                "UNAVAILABLE, not absent. Josephine's code migrated to eCode360 (JO4733) and "
                "the county's own page still links the dead Code Publishing URL; both return "
                "HTTP 403 Cloudflare managed challenge to an honestly-identified agent. "
                "Josephine publishes its code; we did not take it."),
        },
        "orders": {"skip": "No index of adopted instruments located on the county site; "
                           "board records are a meetings system. Deferred."},
        "policies": {"skip": "No county-wide administrative policy set located on the "
                             "county's own domain in this pass. Not established either way."},
    },
}
