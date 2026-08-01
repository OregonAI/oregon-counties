"""Clackamas County — the only county in this build that publishes its law as HTML pages
rather than PDFs.

425,857 people, 3rd largest, Portland metro, home rule charter, Board of Commissioners.

Both the County Code and the Zoning and Development Ordinance are served as one HTML page
per title/section — `/code/title3`, `/planning/zdo101` — with no PDF anywhere. That makes
Clackamas the cheapest county here to keep current and the one most exposed to template
churn: the law and the site navigation arrive in the same document, so the extractor is
carrying the county's menu into every page. `corpus_toolkit.html_to_text` is used rather
than a bespoke stripper, because `corpus-detect-changes` hashes with that same converter and
a different one here would make every source read as CHANGED forever.

THE DRAFT TRAP, AND IT IS ONE LINK. The ZDO index carries `/planning/zdoproposed.html`
alongside the adopted sections — proposed amendments, published in the same list, with a URL
that differs from an adopted section only by the word "proposed". `fetch.looks_like_draft()`
already covers `proposed`, and `exclude_re` names it again explicitly rather than relying on
the shared heuristic: publishing a proposed zoning amendment as adopted law is the worst
single error this corpus can make, and one filter guarding it is not enough.

Verified 2026-07-31: 12 code links, 100+ ZDO section links, one proposed-amendments link
correctly excluded. Honest User-Agent, HTTP 200.
"""

PROFILE = {
    "slug": "clackamas",
    "name": "Clackamas",
    "discovery": "link-list",
    "site": "https://www.clackamas.us",
    "crawl": {
        "decision": "proceed",
        "checked": "2026-07-31",
        "basis": (
            "No AI-agent directive. Nothing on the county site names an AI crawler or "
            "restricts the /code or /planning trees, so there is no determination to make "
            "beyond fetching politely — one request at a time, cached once."),
        "hosts": [
            {"host": "www.clackamas.us", "robots_url": "https://www.clackamas.us/robots.txt",
             "ai_block": False, "content_signal": None,
             "notes": "No named AI agents. /code and /planning are open."},
        ],
    },
    "upstream_signal": (
        "No feed. Sections are edited in place, so content drift is caught only by "
        "re-hashing each page; a new or repealed section shows up as a link appearing or "
        "disappearing from the index."),
    "families": {
        # `/code/title2` ... `/code/title11`, plus `foreward` and `appendixb`. Anchored on
        # the /code/ prefix with a required trailing segment so the index page itself
        # (`/code`) does not enumerate as one of its own children.
        "code": {
            "listing_url": "https://www.clackamas.us/code",
            "link_re": r'href="(/code/[a-z0-9][a-z0-9-]*)"',
            "format": "html",
        },
        # ZDO sections are `/planning/zdo101`, `/planning/zdo1001`, ... The trailing `\d`
        # requirement is what keeps `/planning/zdoproposed.html` out structurally, before
        # exclude_re even runs — two independent guards on the same failure, deliberately.
        "land-use": {
            "listing_url": "https://www.clackamas.us/planning/zdo.html",
            "link_re": r'href="(/planning/zdo\d+)"',
            "exclude_re": r"proposed|draft",
            "format": "html",
        },
        "orders": {
            "skip": (
                "Board business meeting records are at /meetings/bcc/business, a per-meeting "
                "agenda system rather than an index of adopted instruments. Extracting the "
                "ORDERS from it means walking each meeting, which is real work and is "
                "deferred — not blocked."),
        },
        "policies": {
            "skip": (
                "Employment policies and procedures are at /des/epp as a departmental hub "
                "rather than a single document index; reaching the individual policies "
                "requires walking sub-pages. Deferred, not blocked."),
        },
    },
}
