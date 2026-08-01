"""Jackson County — Revize CMS, self-hosted PDFs, and the largest single code set in this
build at 161 chapter PDFs.

221,331 people, 6th largest, southern Oregon / Medford, general law, Board of Commissioners.

The codified ordinances are organised into ten named sections under one Document Center
directory, and the section name is the routing signal: `12 Planning` is land use, everything
else is code. `Administrative Code` is deliberately left in `code` rather than `policies` —
it is codified county law adopted by ordinance, not internal administrative policy, and the
distinction matters because `policies` in this corpus means the HR/purchasing/records
material a county adopts without an ordinance.

THE REVIZE SOFT-404 CHECK, RUN BECAUSE ANOTHER REVIZE COUNTY FAILS IT. Gilliam County's
Revize instance returns HTTP 200 with a full page for any path that cannot exist, which
makes status codes worthless there — a fabricated URL enumerates as a real document.
**Jackson was tested with a deliberately absurd path and correctly returned 404**, so status
is meaningful here and no content-level validation is needed.

CACHE-BUSTING QUERY STRINGS. Every href carries `?t=<timestamp>` (e.g.
`Ch1020.pdf?t=202406181436560`). These are kept rather than stripped: the timestamp is the
publisher's own statement of when that chapter was last republished, which is the closest
thing to an amendment date this county exposes, and dropping it would discard provenance to
gain a marginally tidier URL.

Verified 2026-07-31: 161 code PDFs across 10 sections, honest User-Agent, HTTP 200, proper
404 on a bogus path.
"""

_DC = r'href="(Document Center/Government/Codified%%20Ordinances/%s[^"]*\.pdf[^"]*)"'
_DC_SPACE = r'href="(Document Center/Government/Codified Ordinances/%s[^"]*\.pdf[^"]*)"'

PROFILE = {
    "slug": "jackson",
    "name": "Jackson",
    "discovery": "link-list",
    "site": "https://jacksoncountyor.gov",
    "crawl": {
        "decision": "proceed",
        "checked": "2026-07-31",
        "basis": (
            "No AI-agent directive on the county host. Revize origins vary between counties "
            "on this point — cms9files (Josephine) blocks generic agents while cms2 "
            "(Jackson) does not — so the origin was checked separately rather than assumed "
            "from the county domain."),
        "hosts": [
            {"host": "jacksoncountyor.gov",
             "robots_url": "https://jacksoncountyor.gov/robots.txt",
             "ai_block": False, "content_signal": None,
             "notes": "PDFs allowed. Returns a real 404 for a nonexistent path, unlike the "
                      "Gilliam Revize instance which soft-404s with HTTP 200."},
        ],
    },
    "upstream_signal": (
        "The `?t=<timestamp>` query on every code link changes when a chapter is "
        "republished, so diffing the link set detects an amendment without fetching a byte "
        "— the only county in this build that exposes such a signal."),
    "families": {
        # Everything except `12 Planning`, which land-use claims below. The negative
        # lookahead means a new section directory is picked up as code automatically.
        "code": {
            "listing_url": "https://jacksoncountyor.gov/government/codified_ordinances.php",
            "link_re": _DC_SPACE % r"(?!12 Planning)",
            "format": "pdf",
        },
        "land-use": {
            "listing_url": "https://jacksoncountyor.gov/government/codified_ordinances.php",
            "link_re": _DC_SPACE % r"12 Planning/",
            "format": "pdf",
        },
        "orders": {
            "skip": (
                "Board orders are published through the meeting agendas and minutes system "
                "rather than as an index of adopted instruments, so reaching them means "
                "walking each meeting. Real work, deferred, not blocked."),
        },
        "policies": {
            "skip": (
                "The survey recorded administrative policies under the same Document Center "
                "tree, but the `Administrative Code` section there is CODIFIED county law "
                "adopted by ordinance and is ingested as `code`. Genuine internal policy "
                "(HR, purchasing, records) was not located as a distinct published set; "
                "recording it as none-found would overstate what was checked, so it is "
                "deferred pending a proper look."),
        },
    },
}
