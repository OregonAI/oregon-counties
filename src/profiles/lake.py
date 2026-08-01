"""Lake County — General Code's `*.county.codes` product, 8,194 people.

30th of 36 by population. General law, Board of Commissioners.

**THIS IS THE ONE HOST IN THE CORPUS WHOSE robots.txt NAMES US AND SAYS NO**, and it is
ingested anyway on an explicit operator decision. Everything about that is recorded here
rather than softened, because it is the only case where the Phase 12 reasoning is actually
load-bearing — everywhere else the "AI block" turned out to be either aimed at other agents,
absent entirely, or a protocol artefact.

    lake.county.codes/robots.txt names, each with Disallow: /
        claudebot, gptbot, ccbot, amazonbot, applebot-extended,
        bytespider, google-extended, meta-externalagent

The Phase 12 decision (PLAN.md) is that a vendor directive is not treated as binding for the
text of county law, because Lake County authors its law and General Code hosts it. The
operator was asked specifically about this county, knowing it was the one genuine objection,
and directed that it be ingested. That instruction is the whole basis; nothing here argues
the directive away.

WHAT IS *NOT* CLAIMED: no evasion was needed or used. The host serves our unchanged,
self-identifying User-Agent HTTP 200 over HTTP/2 — the earlier 403 was the same
protocol-version artefact that kept Marion out, not a refusal of our identity. So the
directive is a stated preference we are declining to honour, and it is exactly that, not a
control we defeated.

Structure: `lake.county.codes/LCC/<title>` — 14 titles, plain server-rendered HTML.

Verified 2026-08-01: 14 title pages; LCC/18 (Zoning) extracts 3,067 characters.
"""

PROFILE = {
    "slug": "lake",
    "name": "Lake",
    "discovery": "link-list",
    "site": "https://lake.county.codes",
    "crawl": {
        "decision": "proceed",
        "checked": "2026-08-01",
        "basis": (
            "THE ONLY HOST IN THIS CORPUS WHOSE robots.txt NAMES ClaudeBot AND DISALLOWS IT. "
            "Ingested on an explicit operator decision taken with that fact in front of "
            "them, under the Phase 12 reasoning that the county authors its law and the "
            "vendor hosts it. No evasion involved: the site serves our unchanged "
            "self-identifying User-Agent HTTP 200 over HTTP/2, and the earlier 403 was the "
            "same protocol-version artefact that kept Marion out. This is declining to "
            "honour a stated preference — recorded as such, not dressed up as anything else."),
        "hosts": [
            {"host": "lake.county.codes",
             "robots_url": "https://lake.county.codes/robots.txt",
             "ai_block": True,
             "content_signal": None,
             "notes": "Names claudebot, gptbot, ccbot, amazonbot, applebot-extended, "
                      "bytespider, google-extended and meta-externalagent, each Disallow: /. "
                      "The one genuine AI objection among the corpus's blocked hosts."},
        ],
    },
    "upstream_signal": (
        "No feed. Titles are server-rendered at stable /LCC/<n> paths, so re-hashing each "
        "detects an amendment and a new title appears as a new link on the index."),
    "families": {
        "code": {
            "listing_url": "https://lake.county.codes/",
            # Titles 16-18 are the land-use regime and are claimed below.
            "link_re": r'href="(/LCC/(?!1[678]\b)\d+)"',
            "format": "html",
        },
        "land-use": {
            "listing_url": "https://lake.county.codes/",
            "link_re": r'href="(/LCC/1[678])"',
            "format": "html",
        },
        "orders": {"skip": "No index of adopted instruments on the code host; the county's "
                           "own site was not established as publishing one. Deferred."},
        "policies": {"skip": "No county-wide administrative policy set located. Not "
                             "established either way."},
    },
}
