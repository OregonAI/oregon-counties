"""Wheeler County — 1,456 people, the smallest in Oregon, and the corpus's floor case.

Governed by a County Court. **Publishes no codified county code at all** — verified by the
36-county survey, which found no Municode presence, no eCode360, nothing self-hosted, only
topical ordinances. A finding about Wheeler, not about our reach.

WHAT A HEADLESS BROWSER SETTLED, 2026-08-01. Wheeler's resolutions, ordinances, County Court
minutes and records-retention policy are all in Box.com shared folders. Rendered in Chromium
with a 12-second settle and a scroll, both folders produce a body of **zero characters** and
zero row elements — Box's shared-folder app renders nothing at all under headless automation.

So the wall is real and is not a JavaScript problem we can solve by rendering. It is recorded
here rather than left as an assumption, because the earlier note said Box was JS-rendered and
implied that a browser would reach it. A browser does not.

Also unresolved by any amount of tooling: the county states that older minutes and agendas
require a RECORDS REQUEST FORM, so the online set is partial by design; and the only located
copy of Wheeler's comprehensive plan is in the University of Oregon's Scholars' Bank
(handle 1794/4147), not on the county's own site.

Wheeler is worth keeping in the registry precisely because it is the floor: it shows that for
some Oregon counties the correct answer is "this is not published in a form anyone can
retrieve", and a corpus that cannot say that honestly is not much use.
"""

PROFILE = {
    "slug": "wheeler",
    "name": "Wheeler",
    "discovery": "link-list",
    "site": "https://www.wheelercountyoregon.com",
    "crawl": {
        "decision": "unavailable",
        "checked": "2026-08-01",
        "basis": (
            "The county's Wix site serves us fine and states no AI directive. Its DOCUMENTS "
            "are in Box.com shared folders which render zero content under headless "
            "automation — not a refusal, and not something rendering solves. No family is "
            "retrievable, so nothing is claimed."),
        "hosts": [
            {"host": "www.wheelercountyoregon.com",
             "robots_url": "https://www.wheelercountyoregon.com/robots.txt",
             "ai_block": False, "content_signal": None,
             "notes": "Allow: / with crawl-delay 10. Sitemap covers Wix PAGES only and is "
                      "structurally incapable of reaching the Box folders."},
            {"host": "app.box.com", "robots_url": None, "ai_block": False,
             "content_signal": None,
             "notes": "Shared-folder app. Renders 0 characters in headless Chromium after a "
                      "12s settle and a scroll; no directory listing, no per-file URLs."},
        ],
    },
    "upstream_signal": "None. No feed, no listing, and the archive is gated behind a records "
                       "request form by the county's own statement.",
    "families": {
        "code": {"skip": "MEASURED ABSENCE — Wheeler publishes no codified county code. "
                         "Recorded none-found in the 36-county survey."},
        "orders": {"skip": "Box.com shared folder; renders zero content under headless "
                           "automation. Not a refusal and not solvable by rendering."},
        "policies": {"skip": "Box.com shared folder; same as orders. Wheeler also DELEGATES "
                             "its public records policy, linking the Oregon DOJ Attorney "
                             "General's manual rather than publishing its own."},
        "land-use": {"skip": "The zoning ordinance is a single link on the planning page; "
                             "the COMPREHENSIVE PLAN is not on the county site at all — the "
                             "only located copy is in the University of Oregon's Scholars' "
                             "Bank (handle 1794/4147), a third party."},
    },
}
