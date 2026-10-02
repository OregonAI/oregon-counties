"""Crook County — eCode360 (General Code), reusing the mode written for Clatsop.

27,336 people, 21st largest, general law, Board of Commissioners.

Second eCode360 county, and configuration rather than code: a TOC url and nothing else.

THE STALE LINK THE SURVEY CAUGHT. Crook's own County Code page still links a dead vendor
URL — the county migrated to eCode360 and did not update its own pointer. Ingest goes to
ecode360.com/CR4713 directly, which was verified live, rather than following the county's
link and recording a 404 as provenance.

Verified 2026-08-01: TOC nodes present at ecode360.com/CR4713; honest User-Agent, HTTP 200.

AS OF 2026-09-12, that 200 finding no longer holds (OregonAI/oregon-counties#84): every
ecode360.com title, the August-seeded ones and the four that never seeded alike, now returns
a Cloudflare managed challenge (HTTP 403) to the same honestly-identified fetcher. The block
tightened after this profile was written; it is evidence about the vendor, not about us.
Operator decision 2026-09-12 (route 3): no further automated attempt (Verified Bots is closed
off permanently, #116) — instead an ORS 192.311-192.478 records request to the county for the
code text, since the county publishes it and does not operate the block. See `_meta/sources/
crook.yml` for the per-source could-not-verify notes this rediscovery must not drop.
"""

_DC = r'href="(/DocumentCenter/View/\d+/[^"]*)"'

PROFILE = {
    "slug": "crook",
    "name": "Crook",
    "discovery": "ecode360",
    "site": "https://crookcountyor.gov",
    "crawl": {
        "decision": "proceed",
        "checked": "2026-09-12",
        "basis": (
            "Same as Clatsop: ecode360.com served the honest agent HTTP 200 on 2026-08-01, "
            "with no AI-agent directive of its own, and the survey's 403 was a thin-request "
            "artefact. That is no longer the current state. Re-tested 2026-09-12 against "
            "both the August-seeded titles and the four that never seeded: all 15 "
            "ecode360.com sources now return a Cloudflare managed challenge (HTTP 403) to "
            "the same honestly-identified fetcher (OregonAI/oregon-counties#84) — the block "
            "tightened after this group was built, which is evidence about the host, not "
            "about us. Decision stays 'proceed': crookcountyor.gov is unaffected and still "
            "serves the other 3 sources in this group, and a group-level 'unavailable' "
            "would wrongly stop those too (src/ingest_counties.py). Operator decision "
            "2026-09-12 (route 3): no further automated attempt — Verified Bots is closed "
            "off permanently (home network, #116) — instead an ORS 192.311-192.478 records "
            "request to Crook County for the code text, since the county publishes it and "
            "does not operate the block."),
        "hosts": [
            {"host": "ecode360.com", "robots_url": "https://ecode360.com/robots.txt",
             "ai_block": False, "content_signal": None,
             "notes": "General Code storefront. Robots.txt declares no AI-agent directive "
                      "of its own — ai_block above reflects that, not the Cloudflare layer "
                      "in front of it. Served HTTP 200 to the honest agent through "
                      "2026-08-01; as of 2026-09-12 returns a Cloudflare managed challenge "
                      "(HTTP 403) on every title (OregonAI/oregon-counties#84). See "
                      "crawl.basis and each source's notes."},
            {"host": "crookcountyor.gov", "robots_url": "https://crookcountyor.gov/robots.txt",
             "ai_block": False, "content_signal": None,
             "notes": "County site; handbook and comprehensive plan. Its own County Code "
                      "page still links the DEAD pre-migration vendor URL — not followed."},
        ],
    },
    "upstream_signal": "No feed; re-hash each Title. New Titles appear as new TOC nodes.",
    "families": {
        # `--discover` rewrites _meta/sources/crook.yml's whole `sources` list
        # (src/ingest_counties.py:run_discovery) and carries no per-source `notes` forward.
        # Rediscovery drops the 2026-09-12 could-not-verify notes (OregonAI/oregon-
        # counties#84) on every ecode360 source; they must be put back by hand afterwards,
        # or tests/test_ecode360_notes.py fails.
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
