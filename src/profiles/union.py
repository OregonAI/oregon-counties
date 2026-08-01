"""Union County — Municode, but only a ZONING product, not a full code.

26,058 people, 24th largest, general law, Board of Commissioners.

THE MUNICODE ENTRY IS REAL AND PARTIAL. Union's client record (17704) is live and current —
codified through Ord. 2026-01 — but the product it publishes is the "Zoning, Partition and
Subdivision Ordinance" plus an eleven-ordinance appendix. It is NOT a code of ordinances.
Recording it as Union's `code` would describe the county as having a codified code when what
it has is a codified LAND USE ordinance, so it is routed to `land-use`, which is what it is.

`code` is left unclaimed rather than filled with the zoning product. Union may or may not
codify generally; the survey did not establish it either way, so this is neither a
`none-found` nor a fabricated code — it is a gap in what we checked, and it says so.

Verified 2026-08-01: clientId 17704 live; api.municode.com serves the honest agent HTTP 200.
"""
from src.profiles.washington import extract  # noqa: F401 — same Municode payload shape

PROFILE = {
    "slug": "union",
    "name": "Union",
    "discovery": "municode-api",
    "site": "https://unioncountyor.gov",
    "crawl": {
        "decision": "proceed",
        "checked": "2026-08-01",
        "basis": (
            "Same as Washington and Benton: library.municode.com names ClaudeBot and sets "
            "Content-Signal: ai-train=no; under the Phase 12 decision that is not treated as "
            "binding for the text of county law. No evasion — api.municode.com serves the "
            "honest agent HTTP 200, and the JS-shell host carrying the directive is not "
            "fetched."),
        "hosts": [
            {"host": "library.municode.com",
             "robots_url": "https://library.municode.com/robots.txt",
             "ai_block": True, "content_signal": "search=yes, ai-train=no, use=reference",
             "notes": "JS shell carrying the AI block. NOT fetched."},
            {"host": "api.municode.com", "robots_url": None, "ai_block": False,
             "content_signal": None, "notes": "Open JSON API; 200 to the honest agent."},
        ],
    },
    "upstream_signal": "Jobs/latest/<productId> names the current supplement — a real signal.",
    "families": {
        "land-use": {
            "discovery": "municode-api", "client_id": 17704, "format": "json",
            "skip_re": r"SUPPLEMENT HISTORY",
        },
        "code": {
            "skip": (
                "NOT ESTABLISHED EITHER WAY, which is different from both an absence and a "
                "block. Union's Municode product is a Zoning, Partition and Subdivision "
                "Ordinance — a codified LAND USE instrument, routed to `land-use` — and not "
                "a code of ordinances. Whether Union codifies generally was not determined "
                "by the survey, so no claim is made. Filling this with the zoning product "
                "would describe the county as having a codified code it may not have."),
        },
        "orders": {"skip": "Agendas and minutes system (agmin.php), not an index of adopted "
                           "instruments. Deferred."},
        "policies": {"skip": "The survey found a public-records-request page rather than a "
                             "published policy set. Deferred pending a proper look."},
    },
}
