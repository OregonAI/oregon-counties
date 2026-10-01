"""Clatsop County — eCode360 (General Code), plus self-hosted policies and land use.

41,043 people, 19th largest, general law, Board of Commissioners.

FIRST eCODE360 COUNTY, and the reason `discover_ecode360` exists. General Code is the
largest commercial code vendor among Oregon counties — four of 36, ahead of Municode's
three — so the mode pays for itself here and again at Crook, and again at Lake later.

The survey recorded this county's code as HTTP 403. On 2026-08-01 it was not: `ecode360.com`
served the honest, self-identifying agent HTTP 200. The survey's 403 came from a thinner
request, which is the same trap `src/fetch.py`'s Accept headers exist to avoid — worth
stating, because a recorded 403 that is really a header problem would have written this
county off as blocked when it is simply published.

Verified 2026-08-01: 18 TOC nodes at ecode360.com/CL4917, one of which is "(Reserved)" and
carries no law. Honest User-Agent, HTTP 200.

AS OF 2026-09-12, that 200 finding no longer holds (OregonAI/oregon-counties#84): every
ecode360.com title, the August-seeded ones and the three that never seeded alike, now returns
a Cloudflare managed challenge (HTTP 403) to the same honestly-identified fetcher. The block
tightened after this profile was written; it is evidence about the vendor, not about us.
Operator decision 2026-09-12 (route 3): no further automated attempt (Verified Bots is closed
off permanently, #116) — instead an ORS 192.311-192.478 records request to the county for the
code text, since the county publishes it and does not operate the block. See `_meta/sources/
clatsop.yml` for the per-source could-not-verify notes this rediscovery must not drop.
"""

_DC = r'href="(/DocumentCenter/View/\d+/[^"]*)"'

PROFILE = {
    "slug": "clatsop",
    "name": "Clatsop",
    "discovery": "ecode360",
    "site": "https://clatsopcounty.gov",
    "crawl": {
        "decision": "proceed",
        "checked": "2026-09-12",
        "basis": (
            "ecode360.com served HTTP 200 to the honest agent on 2026-08-01 when this group "
            "was built, with no AI-agent directive of its own; the survey's recorded 403 was "
            "a thin-request artefact, not a refusal, confirmed before building. That is no "
            "longer the current state. Re-tested 2026-09-12 against both the August-seeded "
            "titles and the three that never seeded: all 14 ecode360.com sources now return "
            "a Cloudflare managed challenge (HTTP 403) to the same honestly-identified "
            "fetcher (OregonAI/oregon-counties#84) — the block tightened after this group "
            "was built, which is evidence about the host, not about us. Decision stays "
            "'proceed': clatsopcounty.gov is unaffected and still serves the other 18 "
            "sources in this group, and a group-level 'unavailable' would wrongly stop "
            "those too (src/ingest_counties.py). Operator decision 2026-09-12 (route 3): no "
            "further automated attempt — Verified Bots is closed off permanently (home "
            "network, #116) — instead an ORS 192.311-192.478 records request to Clatsop "
            "County for the code text, since the county publishes it and does not operate "
            "the block."),
        "hosts": [
            {"host": "ecode360.com", "robots_url": "https://ecode360.com/robots.txt",
             "ai_block": False, "content_signal": None,
             "notes": "General Code storefront. Robots.txt declares no AI-agent directive "
                      "of its own — ai_block above reflects that, not the Cloudflare layer "
                      "in front of it. Served HTTP 200 to the honest agent through "
                      "2026-08-01; as of 2026-09-12 returns a Cloudflare managed challenge "
                      "(HTTP 403) on every title (OregonAI/oregon-counties#84). See "
                      "crawl.basis and each source's notes."},
            {"host": "clatsopcounty.gov", "robots_url": "https://clatsopcounty.gov/robots.txt",
             "ai_block": False, "content_signal": None,
             "notes": "County's own site; policies and land use. No named AI agents."},
        ],
    },
    "upstream_signal": (
        "No feed. eCode360 guids are stable across amendments, so content drift is caught by "
        "re-hashing each Title; a new Title appears as a new TOC node."),
    "families": {
        # `--discover` rewrites _meta/sources/clatsop.yml's whole `sources` list
        # (src/ingest_counties.py:run_discovery) and carries no per-source `notes` forward.
        # Rediscovery drops the 2026-09-12 could-not-verify notes (OregonAI/oregon-
        # counties#84) on every ecode360 source; they must be put back by hand afterwards,
        # or tests/test_ecode360_notes.py fails.
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
