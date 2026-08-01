"""Gilliam County — 1,971 people, a County Court, and no codified code.

35th of 36 by population. General law, governed by a **County Court** — county judge plus two
commissioners — so its enactments are court orders and journal entries, never board orders.

**NO CODIFIED COUNTY CODE**, measured by the 36-county survey: no Municode presence, no
eCode360, nothing self-hosted. The third such finding in this corpus after Columbia and
Grant.

THIS SITE SOFT-404s, WHICH MAKES STATUS CODES WORTHLESS HERE. Its Revize instance returns
HTTP 200 with a full ~58 KB page for ANY path, including
`/definitely-not-a-real-path-4f9a2b`. A fabricated URL enumerates exactly like a real one, so
every page in this profile was validated by comparing its size against that control — and one
candidate failed: the employment-opportunities page came back within 200 bytes of the control
and does not exist. Its two "PDFs" are site furniture present on every page.

THE COURT PAGE IS A MEETING-PACKET ARCHIVE, NOT AN INDEX OF LAW, and that is why `orders` is
narrow rather than large. Of 905 PDFs linked there:

    555  agenda-packet items   treasurer's reports, bills pending review, grant final
                               reports, letters of appreciation, presentations, agreements
    264  minutes
     83  agendas
      7  ordinances and court orders

Ingesting all 905 as `doc_type: ordinance` would put a letter of appreciation and a
treasurer's report into the corpus as county law — 900 mislabelled documents to gain 7 real
ones. So `orders` matches only instrument-shaped names, and the packet archive is left where
it is. That is a deliberate 98% reduction, not an oversight.

Note also `Economic Enhancement Ordinance REDLINE.pdf` and `... REDLINE DRAFT 06.22.2026.pdf`
sitting in the same list as adopted text — the draft guard excludes both.

Verified 2026-08-01: 4 planning documents; 7 instrument-shaped court documents; soft-404
control 58,836 bytes.
"""

PROFILE = {
    "slug": "gilliam",
    "name": "Gilliam",
    "discovery": "link-list",
    "site": "https://www.gilliamcountyor.gov",
    "crawl": {
        "decision": "proceed",
        "checked": "2026-08-01",
        "basis": "No AI-agent directive. Nothing to decide.",
        "hosts": [
            {"host": "www.gilliamcountyor.gov",
             "robots_url": "https://www.gilliamcountyor.gov/robots.txt",
             "ai_block": False, "content_signal": None,
             "notes": "Revize instance that SOFT-404s: returns HTTP 200 with a full page for "
                      "any path. Status codes carry no information here; pages must be "
                      "validated against a known-absent control."},
        ],
    },
    "upstream_signal": (
        "No feed. Court documents carry `?t=<timestamp>` cache-busters that change on "
        "re-upload, so diffing the link set detects a replacement."),
    "families": {
        # Instrument-shaped names ONLY. See the docstring: the source page is a meeting-packet
        # archive and 898 of its 905 PDFs are not adopted instruments.
        "orders": {
            "listing_url":
                "https://www.gilliamcountyor.gov/government/offices/county_court/agendas_and_minutes.php",
            "link_re": r'href="([^"]*(?:[Oo]rdinance|[Cc]ourt[ _]?[Oo]rder|R\d{4}-\d+)[^"]*\.pdf[^"]*)"',
            "format": "pdf",
        },
        "land-use": {
            "listing_url":
                "https://www.gilliamcountyor.gov/government/offices/planning/index.php",
            "link_re": r'href="([^"]*\.pdf[^"]*)"',
            # Present on every page of this CMS, not a planning instrument.
            "exclude_re": r"Resource%20Directory|Resource Directory|ucohealth",
            "format": "pdf",
        },
        "code": {
            "skip": (
                "MEASURED ABSENCE. Gilliam publishes no codified county code — recorded "
                "none-found in corpus-seeds/oregon-counties.survey.yml after Municode was "
                "ruled out via the client API and no self-hosted code was located. A fact "
                "about Gilliam County, not about our reach."),
        },
        "policies": {
            "skip": (
                "The employment-opportunities page the survey recorded DOES NOT EXIST: it "
                "returns HTTP 200 within 200 bytes of this site's known-absent control page, "
                "which is the soft-404 signature. Its two PDFs are site furniture. Recorded "
                "as not-established rather than as an absence, because a soft-404 means we "
                "never actually looked at anything."),
        },
    },
}
