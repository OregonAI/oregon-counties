"""Columbia County — THE FIRST COUNTY IN THIS CORPUS WITH NO CODIFIED CODE.

54,063 people, 17th largest, general law, Board of Commissioners.

Columbia does not codify. The 36-county survey checked and recorded `county_code:
none-found` — Municode ruled out via the client API, no eCode360 presence, nothing
self-hosted — and its body of law is instead a subject-filed series of ordinance PDFs. That
is a FINDING ABOUT COLUMBIA COUNTY, not a gap in our collection, and it is the first live
test of the guardrail that forbids asserting an absence without a measured `none-found`
behind it.

Seven of Oregon's 36 counties are in this position. The corpus must be able to say "this
county publishes no codified code" and have that be true and sourced, which is exactly what
`check_guardrails` enforces against the survey.

The ordinances themselves are under /media/Board/BOC/Ordinances/ and are taken as `orders`,
which is what they are — enactments, not a code.

Verified 2026-08-01: honest User-Agent, HTTP 200 on columbiacountyor.gov.
"""

_PDF = r'href="([^"]*\.pdf[^"]*)"'

PROFILE = {
    "slug": "columbia",
    "name": "Columbia",
    "discovery": "link-list",
    "site": "https://www.columbiacountyor.gov",
    "crawl": {
        "decision": "proceed",
        "checked": "2026-08-01",
        "basis": "No AI-agent directive; media tree open. Nothing to decide.",
        "hosts": [
            {"host": "www.columbiacountyor.gov",
             "robots_url": "https://www.columbiacountyor.gov/robots.txt",
             "ai_block": False, "content_signal": None,
             "notes": "No named AI agents."},
        ],
    },
    "upstream_signal": (
        "No feed and no codification, so there is no consolidated text whose hash would "
        "change — freshness here means new ordinance PDFs appearing in the index."),
    "families": {
        "orders": {"listing_url": "https://www.columbiacountyor.gov/ordinances",
                   "link_re": _PDF, "format": "pdf"},
        "land-use": {"listing_url":
                     "https://www.columbiacountyor.gov/departments/LandDevelopment/Planningcodes",
                     "link_re": _PDF, "format": "pdf"},
        "code": {
            "skip": (
                "MEASURED ABSENCE, and the first in this corpus. Columbia County publishes "
                "NO CODIFIED CODE — recorded as `none-found` in "
                "corpus-seeds/oregon-counties.survey.yml after Municode was ruled out via "
                "the client API, no eCode360 presence was found, and nothing self-hosted "
                "was located. Its body of law is the subject-filed ordinance series, taken "
                "as `orders`. This is a fact about Columbia County, not about our reach, and "
                "is the case check_guardrails' absence rule exists to keep honest."),
        },
        "policies": {
            "skip": (
                "The survey verified a single public records policy PDF on the legacy "
                "co.columbia.or.us host. One document does not characterise the county's "
                "administrative policy set, and claiming it as that family would overstate "
                "what was found. Deferred pending a proper look."),
        },
    },
}
