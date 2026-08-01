"""Polk County — CivicPlus, and the county that needed the two-level index walk.

90,549 people, 12th largest, general law, Board of Commissioners.

THE SHAPE THAT FORCED A DRIVER CHANGE. Polk's Code of Ordinances page (/540) is not a list of
documents — it is a list of NINE TITLE PAGES (`/751/Code-of-Ordinances-Title-VIII` and
siblings), and the actual PDFs hang off those. Pointing `link_re` at /540 finds exactly one
document, the single PDF that happens to be linked from the index itself, and reports
success.

That is the silent under-collection this pipeline keeps having to defend against, so it was
fixed in the driver rather than worked around here: `index_url` + `index_re` discovers the
listing pages, then `link_re` runs against each. `_listing_urls` raises if `index_re` matches
nothing, because scraping zero pages would otherwise look exactly like a county that
publishes nothing.

Verified 2026-07-31: 9 Title pages under /540; DocumentCenter PDFs beneath them. Honest
User-Agent, HTTP 200.
"""

_DC = r'href="(/DocumentCenter/View/\d+/[^"]*)"'

PROFILE = {
    "slug": "polk",
    "name": "Polk",
    "discovery": "link-list",
    "site": "https://www.polkcountyor.gov",
    "crawl": {
        "decision": "proceed",
        "checked": "2026-07-31",
        "basis": (
            "No AI-agent directive on the county host, and nothing restricting "
            "/DocumentCenter. Nothing to decide; fetched politely, one request at a time."),
        "hosts": [
            {"host": "www.polkcountyor.gov",
             "robots_url": "https://www.polkcountyor.gov/robots.txt",
             "ai_block": False, "content_signal": None,
             "notes": "No named AI agents. DocumentCenter open."},
            {"host": "apps2.co.polk.or.us", "robots_url": None, "ai_block": False,
             "content_signal": None,
             "notes": "Commissioners' Journal search application — the board-orders source, "
                      "a query interface rather than a document index. Not fetched."},
        ],
    },
    "upstream_signal": (
        "No feed. A new Title page appears in the /540 index; a replaced chapter gets a new "
        "DocumentCenter id, so diffing the id set across the nine Title pages catches both."),
    "families": {
        "code": {
            "index_url": "https://www.polkcountyor.gov/540/Code-of-Ordinances",
            "index_re": r'href="(/\d+/Code-of-Ordinances-Title-[IVX]+)"',
            "link_re": _DC,
            "format": "pdf",
        },
        "land-use": {
            "listing_url": "https://www.polkcountyor.gov/651/Zoning-Ordinance",
            "link_re": _DC,
            "format": "pdf",
        },
        # Declared, not discovered. The page links it as `/DocumentCenter/View/3546` with
        # no name segment, so discovery would title the county's records policy "3546".
        "policies": {
            "explicit": [{
                "url": "https://www.polkcountyor.gov/DocumentCenter/View/3546",
                "name": "public-records-management-and-disclosure-policy",
                "id": "polk-policies-public-records-management-and-disclosure",
                "title": "Polk County Public Records Management and Disclosure Policy",
            }],
            "format": "pdf",
        },
        "orders": {
            "skip": (
                "Board orders are behind the Commissioners' Journal search application at "
                "apps2.co.polk.or.us, which is a query form rather than an index — there is "
                "no listing to enumerate, only searches to run. Real work, deferred."),
        },
    },
}
