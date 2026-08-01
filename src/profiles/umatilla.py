"""Umatilla County — TYPO3, and the most templatable code set in the corpus.

80,491 people, 14th largest, general law, Board of Commissioners.

Every ordinance is `/fileadmin/user_upload/BCC/Ordinances/<chapter>_<Title_With_Underscores>.pdf`
— 37 of them, chapters 36 through 153, with the chapter number and the subject both in the
filename. Nothing else in this build is this regular.

THE MIGRATION HAZARD, AND IT IS THE REASON THIS PROFILE PINS ONE HOST. Three domains resolve:
`umatillacounty.gov` (canonical), `www.co.umatilla.or.us`, and `umatillacounty.net`. A path
migration has already happened — `/departments/bcc/codes`, the URL search engines still
surface, now 404s, and several cached URLs for this county are dead. Ingest pins
umatillacounty.gov and re-crawls rather than trusting any remembered path, because a dead
`source_url` recorded as provenance is worse than no document: it points a reader at nothing
while looking authoritative.

The land-use documents are the exception and are deliberately taken from `co.umatilla.or.us`,
because that is where they were verified answering. Same property, different host, recorded
as such rather than rewritten to look tidy.

ADMINISTRATIVE POLICY IS A MEASURED ABSENCE. The survey reached the HR department page and
found no personnel manual, purchasing policy, records policy or IT policy published anywhere.
That is `none-found` — a finding about Umatilla — and NOT `could-not-verify`. It is recorded
as a skip citing the survey, so the guardrail that forbids asserting an absence has something
measured to rest on.

Verified 2026-08-01: 37 ordinance PDFs live. The Development Code PDF resolves; the
Comprehensive Plan URL recorded by the survey on 2026-07-31 now returns 404, as does the
planning-documents index — the migration hazard this docstring warns about, observed within a
day. The comp plan is therefore NOT held, and its absence here is an access failure on our
side rather than a finding that Umatilla publishes none.

No robots.txt exists on any of the three domains — each returns the TYPO3 not-found page.
"""

PROFILE = {
    "slug": "umatilla",
    "name": "Umatilla",
    "discovery": "link-list",
    "site": "https://umatillacounty.gov",
    "crawl": {
        "decision": "proceed",
        "checked": "2026-07-31",
        "basis": (
            "No robots.txt exists on any Umatilla domain — each returns the TYPO3 "
            "'Page Not Found' page rather than a directives file, so there is nothing "
            "stated to honour or decline. Absence of a robots.txt is not permission in "
            "itself, so fetching stays polite: one request at a time, cached once."),
        "hosts": [
            {"host": "umatillacounty.gov", "robots_url": "https://umatillacounty.gov/robots.txt",
             "ai_block": False, "content_signal": None,
             "notes": "No robots.txt (TYPO3 404 page). Canonical host; pinned for ingest "
                      "because a completed path migration left cached URLs 404ing."},
            {"host": "www.co.umatilla.or.us", "robots_url": None, "ai_block": False,
             "content_signal": None,
             "notes": "Same property. Used for land-use, where the documents were verified."},
        ],
    },
    "upstream_signal": (
        "No feed. Filenames encode the chapter number, so a new chapter appears as a new "
        "link in the ordinances index; amendments replace the PDF in place and are caught "
        "by re-hashing."),
    "families": {
        "code": {
            "listing_url":
                "https://umatillacounty.gov/departments/board-of-commissioners/code-of-ordinances",
            "link_re": r'href="(/fileadmin/user_upload/BCC/[^"]*\.pdf)"',
            "format": "pdf",
        },
        # DECLARED, because the listing page 404s and one of the two documents the survey
        # recorded has already rotted. The Development Code was re-verified live today; the
        # Comprehensive Plan URL the survey captured on 2026-07-31 now 404s, and so does the
        # planning-documents index. That is this county's stated hazard arriving inside a
        # day, and the honest response is to hold what resolves and say what does not.
        "land-use": {
            "explicit": [{
                "url": "https://www.co.umatilla.or.us/fileadmin/user_upload/Community_Development/Planning/Umatilla_County_Development_Code_2025.pdf",
                "name": "umatilla-county-development-code-2025",
                "id": "umatilla-land-use-development-code-2025",
                "title": "Umatilla County Development Code (rev. 2025-06-18)",
            }],
            "format": "pdf",
        },
        "policies": {
            "skip": (
                "MEASURED ABSENCE, not an access failure. The 36-county survey reached the "
                "HR department page (umatillacounty.gov/departments/hr) successfully and "
                "found no personnel manual, purchasing policy, public records policy or IT "
                "policy published. Recorded as `none-found` in "
                "corpus-seeds/oregon-counties.survey.yml, which is what any statement about "
                "this absence must rest on — the corpus is not entitled to infer it from "
                "holding no file."),
        },
        "orders": {
            "skip": (
                "Agendas and minutes are published as a per-meeting listing rather than an "
                "index of adopted instruments; the ordinances themselves are captured in "
                "`code`. Deferred."),
        },
    },
}
