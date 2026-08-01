"""Multnomah County — Drupal, self-hosted PDFs, and by far the cleanest listing structure of
the seven counties in this build.

795,897 people, 18.6% of Oregon, the largest county in the state and the highest-value single
entry in the corpus. Home rule charter, Board of Commissioners.

Every family publishes an HTML index of `multco.us/file/<slug>/download` links with
human-readable slugs — `chapter_11:_revenue_and_taxation`, `rule_2-45:_sick_leave` — which is
why this county needs no custom discover(): the generic `link-list` mode plus a per-family
`link_re` covers all of it.

TWO THINGS THAT ARE NOT AS CLEAN AS THE LISTINGS SUGGEST.

1. **The published comprehensive plan is a convenience copy, and the county says so.**
   Multnomah states that the OFFICIAL Comprehensive Plan and Zoning Map are not online — they
   must be viewed in person at 1600 SE 190th Ave or requested by email. So the land-use
   documents here are the county's own convenience rendering of an instrument whose official
   version is on paper. That is recorded per document rather than left for a reader to
   discover, because this corpus's whole premise is that a reader can tell what they are
   looking at.

2. **The board record is split across two platforms by era.** 2020-present is the Drupal
   faceted list at /board/documents-view (24 pages of `?page=N`); 1962-2019 is a separate
   Preservica archive at multco.access.preservica.com with different search semantics
   entirely. Only the Drupal era is ingested, and the boundary is stated rather than implied
   — a corpus that silently held 2020+ would answer "what did the Board adopt in 2015" with
   nothing, which reads as "nothing was adopted".

Chapters 38 (Columbia River Gorge National Scenic Area) and 39 (Zoning Code) are routed to
`land-use` rather than `code`, because they are the land-use instruments ORS 197 and the
OAR 660 statewide planning goals actually bind — which is the edge that makes this corpus
worth building. The same PDF never appears in both families; `code`'s link_re excludes them.

Verified 2026-07-31: 21 code chapters plus the charter, 51 personnel-rule PDFs, 32 land-use
PDFs, all reachable with the honest User-Agent, HTTP 200.
"""

# Drupal serves these as `/file/<slug>/download` with the slug carrying the real title.
# Anchored on multco.us so the pattern cannot wander onto an off-site link.
_FILE = r'href="(https://multco\.us/file/%s/download)"'

PROFILE = {
    "slug": "multnomah",
    "name": "Multnomah",
    "discovery": "link-list",
    "site": "https://multco.us",
    "crawl": {
        "decision": "proceed",
        "checked": "2026-07-31",
        "basis": (
            "Stock Drupal robots.txt naming no AI agent and disallowing only framework "
            "paths (/core/, /profiles/, /README.md). Nothing blocks /file/, /board/ or "
            "/info/, which is where every document here lives. No determination to make."),
        "hosts": [
            {"host": "multco.us", "robots_url": "https://multco.us/robots.txt",
             "ai_block": False, "content_signal": None,
             "notes": "Disallow: /core/ /profiles/ /README.md only. Sitemap index at "
                      "/sitemap.xml, 5 sub-sitemaps."},
            {"host": "www.multco.us", "robots_url": "https://www.multco.us/robots.txt",
             "ai_block": False, "content_signal": None,
             "notes": "Same site; www redirects to the bare host, which is canonical."},
        ],
    },
    "upstream_signal": (
        "No feed. The code index page is edited when a chapter is amended, and the chapter "
        "slugs are stable, so re-fetching the index and diffing the link set detects a new "
        "or renamed chapter; content drift is caught by re-hashing each PDF."),
    "families": {
        # Chapters 1-29a. 38 and 39 are deliberately excluded here and claimed by `land-use`
        # below — a document in two families would be two documents claiming to be one law.
        "code": {
            "listing_url": "https://multco.us/info/multnomah-county-code",
            "link_re": _FILE % r"(?:chapter_(?!38|39)[^/\"]+|home_rule_charter[^/\"]*)",
            "format": "pdf",
        },
        "land-use": {
            "listing_url": "https://multco.us/info/comprehensive-plan",
            "link_re": _FILE % r"[^/\"]+",
            "format": "pdf",
        },
        "policies": {
            "listing_url": "https://www.multco.us/employee-labor-relations/personnel-rules",
            # `combined_personnel_rules` is excluded: it is the same rules concatenated, so
            # ingesting it alongside the individual rules would double every provision and
            # make a search hit ambiguous about which document states the rule.
            "link_re": _FILE % r"rule_[^/\"]+",
            "format": "pdf",
        },
        # NOW BUILT, via js-render. The reason this was skipped turned out to be only half
        # right: the list is paginated AND client-side. Plain HTTP returns ZERO file links
        # across pages 0, 1 and 23 — measured — while a rendered page yields 29 on page one.
        # So `listing_urls` alone would have enumerated nothing and looked like an empty
        # family.
        #
        # multco.us serves our honest agent HTTP 200 and states no AI directive; the only
        # obstacle was that the list is built in the browser. Rendering it is being a capable
        # client, not getting past anything.
        #
        # STILL EXCLUDED: the 1962-2019 Preservica archive
        # (multco.access.preservica.com), which is a separate platform with its own search
        # semantics. So this family is the DRUPAL ERA ONLY, and that boundary is stated
        # rather than implied — a corpus silently holding 2020+ would answer "what did the
        # Board adopt in 2015" with nothing, which reads as "nothing was adopted".
        "orders": {
            "discovery": "js-render",
            "url_template": "https://www.multco.us/board/documents-view?page=%d",
            "pages": 24,
            # Hrefs are RELATIVE in the rendered DOM (`/file/2026-031.pdf/download`), not
            # absolute, because getAttribute returns what the markup says rather than the
            # resolved URL. Matching on the path is what works; the driver resolves it.
            "link_re": r"^/file/[^\"]+/download$",
            "format": "pdf",
        },
    },
}
