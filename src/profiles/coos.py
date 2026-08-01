"""Coos County — self-hosted PDFs behind content-hashed paths.

64,326 people, 16th largest, general law, Board of Commissioners.

All four families publish as `/files/<hash>/<name>.pdf` — the path carries an opaque content
hash and the filename carries the real identity (`article_8_-_elections_and_districts.pdf`).
Ids come from the filename, which is why `_name_from_url` matters here: taking the last path
segment blindly would be fine, but taking the hash would produce ids nobody can cite.

THE HASH IN THE PATH IS A FRESHNESS SIGNAL AND A LINK-ROT RISK AT ONCE. A re-uploaded
article gets a new hash, so the old URL presumably stops resolving — which means a recorded
`source_url` here is more perishable than most, and the scheduled drift job matters more for
Coos than for a county serving stable paths.

Verified 2026-07-31: 16 code PDFs, honest User-Agent, HTTP 200.
"""

_F = r'href="([^"]*/files/[0-9a-f]+/[^"]*\.pdf)"'

PROFILE = {
    "slug": "coos",
    "name": "Coos",
    "discovery": "link-list",
    "site": "https://co.coos.or.us",
    "crawl": {
        "decision": "proceed",
        "checked": "2026-07-31",
        "basis": "No AI-agent directive and no restriction on /files/. Nothing to decide.",
        "hosts": [
            {"host": "co.coos.or.us", "robots_url": "https://co.coos.or.us/robots.txt",
             "ai_block": False, "content_signal": None,
             "notes": "No named AI agents; /files/ open."},
        ],
    },
    "upstream_signal": (
        "Content-hashed paths: a re-uploaded document gets a new /files/<hash>/ URL, so "
        "diffing the link set detects a replacement exactly — and means recorded URLs go "
        "stale faster here than elsewhere."),
    "families": {
        "code": {"listing_url": "https://co.coos.or.us/county-codes",
                 "link_re": _F, "format": "pdf"},
        "land-use": {"listing_url":
                     "https://co.coos.or.us/coos-county-zoning-and-land-development-ordinances",
                     "link_re": _F, "format": "pdf"},
        "policies": {"listing_url": "https://co.coos.or.us/employee-information",
                     "link_re": _F, "format": "pdf"},
        "orders": {"listing_url": "https://co.coos.or.us/board-meetings",
                   "link_re": _F, "format": "pdf"},
    },
}
