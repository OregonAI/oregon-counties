"""Lane County — CivicPlus, self-hosted PDFs, and the clearest three-tier separation of law,
policy and procedure in the whole 36-county survey.

382,396 people, 4th largest, home rule charter, Board of Commissioners.

Lane distinguishes three things most counties blur together, and the distinction is worth
preserving because it is exactly what this corpus is trying to capture:

    Lane Code                      law, adopted by ordinance          -> code / land-use
    Lane Manual                    board-adopted policy               -> policies
    Administrative Procedures Mgr  administrative procedure           -> policies

THE REDLINE TRAP, WHICH IS THE SHARPEST IN THE BUILD. Lane publishes renumbering redlines in
the SAME directory as adopted chapters — `LC02 renumber redline w reference 2021_09_17.pdf`
sits beside `LC02.pdf`, and the APM carries `Chapter2Section3bIssue2REDLINE.pdf` beside
`Chapter4Section1CURRENT.pdf`. Publishing a redline as adopted law is the worst single error
this corpus can make.

MEASURED BEFORE FILTERING, because a filter that silently drops a chapter is its own failure:
of 91 PDFs in the Lane Code directory, 69 are clean and 22 are redline/renumber drafts, and
**every chapter 1-21 has a clean file — no chapter exists only as a redline.** So excluding
drafts costs no coverage here. That is a fact about Lane today, not a general guarantee, so
`exclude_re` names the patterns explicitly rather than trusting the shared heuristic alone:
`renumber` in particular is a Lane-specific draft marker that
`fetch.looks_like_draft()` does not know about.

LAND USE IS INSIDE THE CODE, not separate. Chapters 10 (zoning, 25 files), 12 (comprehensive
plan), 13 (land divisions) and 16 (Land Use & Development Code, 23 files) are routed to
`land-use` rather than `code`, because those are the instruments ORS 197 and the OAR 660
statewide planning goals bind — the edge that makes this corpus worth building. `code`'s
pattern excludes exactly those four chapters, so no PDF lands in both families.

Chapters are split across multiple PDFs by section range (LC10.005_020.pdf,
LC10.025_100.pdf), so a "chapter" here is several documents. That is the publisher's own
division and is preserved rather than concatenated.

Verified 2026-07-31: 91 PDFs in the code directory, honest User-Agent, HTTP 200.
"""

_DIR = r"[^\"]*Lane%20Code/|[^\"]*Lane Code/"

PROFILE = {
    "slug": "lane",
    "name": "Lane",
    "discovery": "link-list",
    "site": "https://lanecountyor.gov",
    "crawl": {
        "decision": "proceed",
        "checked": "2026-07-31",
        "basis": (
            "robots.txt names no AI agent. It disallows the site's own API surface "
            "(/Search/, /WebApi/, /WebServices/, /portal/svc/, several .asmx endpoints) and "
            "leaves the PDF tree open. Those disallows are honoured — nothing here touches "
            "them; every document is fetched from the static file tree."),
        "hosts": [
            {"host": "lanecountyor.gov", "robots_url": "https://lanecountyor.gov/robots.txt",
             "ai_block": False, "content_signal": None,
             "notes": "Disallow /Search/ /WebApi/ /WebServices/ /portal/svc/ *.asmx. "
                      "No sitemap declared. PDF tree open."},
            {"host": "cdnsm5-hosted.civiclive.com", "robots_url": None, "ai_block": False,
             "content_signal": None,
             "notes": "CDN origin the PDFs are actually served from; same content, no "
                      "separate directives found."},
        ],
    },
    "upstream_signal": (
        "No feed. Lane Code chapters are re-published as whole PDFs when amended, so a "
        "re-hash of each chapter detects an amendment; a new chapter appears as a new link "
        "in the code index."),
    "families": {
        # Everything in the Lane Code directory EXCEPT the four land-use chapters, which are
        # claimed below. Negative lookahead on the chapter number, so a new non-land-use
        # chapter is picked up automatically.
        "code": {
            "listing_url": "https://lanecountyor.gov/government/county_departments/county_counsel/lane_code",
            "link_re": r'href="([^"]*(?:Lane%20Code|Lane Code)/(?!LC(?:10|12|13|16)\b)[^"]*\.pdf)"',
            "exclude_re": r"redline|renumber",
            "format": "pdf",
        },
        "land-use": {
            "listing_url": "https://lanecountyor.gov/government/county_departments/county_counsel/lane_code",
            "link_re": r'href="([^"]*(?:Lane%20Code|Lane Code)/LC(?:10|12|13|16)[^"]*\.pdf)"',
            "exclude_re": r"redline|renumber",
            "format": "pdf",
        },
        "policies": {
            "skip": (
                "The Lane Manual and the Administrative Procedures Manual are published as "
                "per-chapter and per-section PDFs under separate directory trees rather "
                "than from a single index page, so the generic link-list mode cannot reach "
                "them from one listing URL. They are also where the CURRENT/REDLINE pairs "
                "are densest — `Chapter2Section3bIssue2REDLINE.pdf` beside "
                "`Chapter4Section1CURRENT.pdf` — which argues for a positive `CURRENT`-only "
                "filter written against the real directory listing rather than a negative "
                "one bolted onto this pass. Deliberately deferred, not blocked."),
        },
        "orders": {
            "skip": (
                "Board orders live in a year-directory hierarchy (2011-2026) whose slugs are "
                "IRREGULAR — `2016_orders/`, `2022_1/` — so the year cannot be templated and "
                "each directory must be enumerated. Real work, not blocked; deferred."),
        },
    },
}
