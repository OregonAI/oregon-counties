"""Wallowa County — 7,522 people, no codified code, and its orders behind Google Drive.

31st of 36 by population. General law, Board of Commissioners.

**NO CODIFIED COUNTY CODE**, and the county says so itself: the survey recorded Wallowa
stating that "ordinances are the same as orders" — it does not codify at all. Fourth such
finding after Columbia, Grant and Gilliam, and the most explicit, because it is the county's
own characterisation rather than our inference from an absent index.

WHAT IS REACHABLE, AND WHAT IS NOT. The land-use section is on the county's own site and is
taken. The ORDERS — 294 of them per the survey — are in Google Drive folders whose download
host (`drive.usercontent.google.com`) carries a blanket `Disallow: /`, and Drive's folder
view is a client-side app with no per-file URLs. That is the same shape as Wheeler's Box
folders and is not solved by rendering.

The survey's `land-use-and-development/page/ordinances` URL now 404s; the department index at
`/land-use-and-development` resolves and carries the sub-pages, so the index is used instead
of the remembered path — the same link-rot discipline Umatilla forced.

Verified 2026-08-01: /land-use-and-development resolves with 11 sub-pages; /planning 404s;
/administrative-services resolves with no documents.
"""

PROFILE = {
    "slug": "wallowa",
    "name": "Wallowa",
    "discovery": "link-list",
    "site": "https://www.co.wallowa.or.us",
    "crawl": {
        "decision": "proceed",
        "checked": "2026-08-01",
        "basis": (
            "The county's own site states no AI directive and serves us fine. Its ORDERS are "
            "in Google Drive, whose download host disallows everyone — honoured, and it is a "
            "blanket directive rather than one aimed at us."),
        "hosts": [
            {"host": "www.co.wallowa.or.us",
             "robots_url": "https://www.co.wallowa.or.us/robots.txt",
             "ai_block": False, "content_signal": None,
             "notes": "No named AI agents."},
            {"host": "drive.usercontent.google.com", "robots_url": None, "ai_block": False,
             "content_signal": None,
             "notes": "Blanket Disallow: / on the Drive download host. Honoured; the folder "
                      "view is also a client-side app with no per-file URLs."},
        ],
    },
    "upstream_signal": (
        "No feed and no codification, so there is no consolidated text whose hash would "
        "change; freshness means new documents appearing in the land-use section."),
    "families": {
        "land-use": {
            "index_url": "https://www.co.wallowa.or.us/land-use-and-development",
            "index_re": r'href="(/land-use-and-development/page/[a-z0-9-]+)"',
            "link_re": r'href="([^"]*\.pdf[^"]*)"',
            # Off-site state aviation documents linked as references, not county instruments.
            "exclude_re": r"oregon\.gov",
            "format": "pdf",
        },
        "code": {
            "skip": (
                "MEASURED ABSENCE, and stated by the county itself: Wallowa does not codify, "
                "and told the surveyors that 'ordinances are the same as orders'. Recorded "
                "none-found in corpus-seeds/oregon-counties.survey.yml. A fact about Wallowa "
                "County, not about our reach."),
        },
        "orders": {
            "skip": (
                "The 294 orders and resolutions are in Google Drive folders. The download "
                "host drive.usercontent.google.com carries a blanket Disallow: / — honoured "
                "— and the folder view is a client-side app with no per-file URLs, so this "
                "is not a rendering problem either. Same shape as Wheeler's Box folders."),
        },
        "policies": {
            "skip": (
                "/administrative-services resolves and publishes no documents. Recorded as "
                "not-established rather than as an absence: a department page without "
                "attachments does not establish that the county publishes no policy set."),
        },
    },
}
