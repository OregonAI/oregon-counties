"""Benton County — Municode, the second county to use that route.

98,899 people, 11th largest, home rule charter, Board of Commissioners.

Reuses `discover_municode` and the Municode JSON extractor written for Washington. That is
the point of the profile-per-county shape: the second Municode county is configuration —
a client id and a product id — rather than code.

ONE CODE BOOK, NOT TWO. Washington publishes its Code of Ordinances and its Community
Development Code as separate Municode products; Benton has a single Code of Ordinances with
land use inside it as a Development Code chapter. So `land-use` is not a separate product
here and is not claimed twice — the land-use text arrives as part of `code`, which is how
Benton itself organises it. Inventing a second family to look symmetrical with Washington
would misdescribe the county.

Verified 2026-07-31: clientId 17689 live, Code of Ordinances updated 2026-07-10 with a
1,552-node table of contents. Honest User-Agent, HTTP 200 on api.municode.com.
"""
from src.profiles.washington import extract  # noqa: F401  — same payload shape, same parser

PROFILE = {
    "slug": "benton",
    "name": "Benton",
    "discovery": "municode-api",
    "site": "https://www.bentoncountyor.gov",
    "crawl": {
        "decision": "proceed",
        "checked": "2026-07-31",
        "basis": (
            "Same determination as Washington County, and for the same reason: "
            "library.municode.com names ClaudeBot and sets Content-Signal: ai-train=no, and "
            "under the Phase 12 decision that directive is not treated as binding for the "
            "text of county law, which Benton authors and Municode hosts. No evasion is "
            "involved — api.municode.com serves HTTP 200 to the honest, self-identifying "
            "agent, and the JS-shell host that carries the directive is not fetched."),
        "hosts": [
            {"host": "library.municode.com",
             "robots_url": "https://library.municode.com/robots.txt",
             "ai_block": True,
             "content_signal": "search=yes, ai-train=no, use=reference",
             "notes": "Human-facing JS shell carrying the AI block. NOT fetched by this "
                      "profile."},
            {"host": "api.municode.com", "robots_url": None, "ai_block": False,
             "content_signal": None,
             "notes": "Open JSON API, no robots.txt served. 200 to the honest agent."},
        ],
    },
    "upstream_signal": (
        "Jobs/latest/<productId> names the current supplement and its publish date, so the "
        "supplement number is a real change signal rather than a re-hash."),
    "families": {
        "code": {
            "discovery": "municode-api",
            "client_id": 17689,
            "format": "json",
            "skip_re": r"SUPPLEMENT HISTORY",
        },
        "land-use": {
            "skip": (
                "Benton publishes ONE code book, with land use inside it as a Development "
                "Code chapter, so its land-use text arrives as part of `code`. Claiming a "
                "separate land-use family here — to look symmetrical with Washington, which "
                "genuinely has two Municode products — would either duplicate documents or "
                "describe a division Benton does not make."),
        },
        "orders": {
            "skip": (
                "Board orders are in a CivicClerk portal (bentoncoor.portal.civicclerk.com), "
                "a per-meeting agenda system rather than an index of adopted instruments. "
                "Reachable, not blocked; deferred."),
        },
        "policies": {
            "skip": (
                "The survey located administrative documents under da.bentoncountyor.gov "
                "(District Attorney), which is one office's document store rather than "
                "county-wide administrative policy. Recording it as the county's policy set "
                "would overstate what it is; a proper look is deferred."),
        },
    },
}
