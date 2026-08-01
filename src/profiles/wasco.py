"""Wasco County — self-hosted PDFs under a document-centre tree, 188 of them.

26,507 people, 23rd largest, general law, Board of Commissioners.

TWO PARALLEL LAND-USE REGIMES, and this is the county the survey flagged for it. Wasco
maintains a SEPARATE 23-chapter National Scenic Area Land Use and Development Ordinance
alongside its general LUDO, because part of the county lies in the Columbia River Gorge
National Scenic Area (16 U.S.C. 544). A pipeline that ingests "the land use ordinance" per
county holds the wrong law for part of Wasco. Both are taken from the planning index.

Compare Hood River, which folds the same federal regime INTO its ordinary zoning ordinance as
Article 75 — same statute, opposite structural choice, and no way to know which without
looking.

CASE MATTERS IN ITS ROBOTS FILE. Wasco's Allow list covers lowercase `.pdf` while the server
serves uppercase `.PDF` files. Recorded because it is the kind of mismatch that makes a
compliance check pass while describing something other than what is being fetched.

EXTRACTION RATE: 43 OF 191 (23%). The rest are scanned images with no text layer — this is
a decades-deep archive and the older signed instruments are photographs.

That number is stated here because it must not be inferred from a document count. The
judgement differs from Yamhill's, where the `orders` family was skipped entirely: Yamhill
publishes a WELL-DEFINED SET of 360 adopted ordinances of which 6% survived extraction, so
ingesting them would have shown an arbitrary era-shaped slice of a known whole. Wasco's index
is a mixed archive — ordinances, policies, plans, across decades, with no defined
denominator — so the 43 that extract are genuinely useful documents rather than a
misleading sample of something countable.

Neither is a statement about what Wasco County publishes. The scanned 148 are held back by
OCR, which is a corpus-wide capability decision.

Verified 2026-08-01: 191 PDFs discovered, 43 extractable. Honest User-Agent, HTTP 200.
Returns a real 404 on a bogus path — no soft-404, unlike the Gilliam Revize instance.
"""

_PDF = r'href="([^"]*\.pdf[^"]*)"'

PROFILE = {
    "slug": "wasco",
    "name": "Wasco",
    "discovery": "link-list",
    "site": "https://www.wascocountyor.gov",
    "crawl": {
        "decision": "proceed",
        "checked": "2026-08-01",
        "basis": (
            "No AI-agent directive. The robots Allow list names lowercase .pdf while the "
            "server serves uppercase .PDF — recorded because a rule that does not match the "
            "files it governs is worth knowing about, not because it blocks anything here."),
        "hosts": [
            {"host": "www.wascocountyor.gov",
             "robots_url": "https://www.wascocountyor.gov/robots.txt",
             "ai_block": False, "content_signal": None,
             "notes": "Revize origin cms5. Allows PDFs; case mismatch noted above. Real 404 "
                      "on a nonexistent path."},
        ],
    },
    "upstream_signal": (
        "No feed. Documents are filed by year under BOCC Archives, so a new year's directory "
        "appearing in the index is the signal for new instruments."),
    "families": {
        "code": {"listing_url":
                 "https://www.wascocountyor.gov/departments/board_of_county_commissioners/policies_and_ordinances.php",
                 "link_re": _PDF, "format": "pdf"},
        "land-use": {"listing_url":
                     "https://www.wascocountyor.gov/departments/planning/plans___ordinances/index.php",
                     "link_re": _PDF, "format": "pdf"},
        "policies": {
            "skip": (
                "Administrative policy is filed in the same BOCC Archives tree as the "
                "ordinances and is captured under `code`; separating the two needs a "
                "per-document judgement about which instrument is which, and guessing would "
                "mislabel county law as internal policy or the reverse. Deferred."),
        },
        "orders": {
            "skip": (
                "Board orders share the policies-and-ordinances index with the code and are "
                "captured there. Splitting them needs the same per-document judgement."),
        },
    },
}
