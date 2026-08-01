"""Deschutes County — CivicPlus Municipal Code Online, and the best machine-readable source
in the whole 36-county survey.

The public code portal is an AngularJS SPA with no server-rendered HTML: fetching
deschutescounty.municipalcodeonline.com returns a shell full of `{{BookDTO...}}` bindings and
no law. Scraping it is pointless.

Its backing S3 bucket, however, answers unauthenticated ListObjectsV2, and that is where the
county's enactments actually live: **896 ordinance PDFs going back to 1970**, with recording
dates in the filenames. The bucket is SHARED across CivicPlus MCO clients nationally (462
client prefixes at its top level), so this route generalizes to any other MCO county.

WHAT THE BUCKET DOES *NOT* HOLD, and this is the finding that shaped the profile: the
CODIFIED code. Of 932 objects under `deschutescounty/`, 896 are ordinances and the remaining
36 are ADC images, a logo and two stray files. The codified rendering exists only inside the
SPA. So `code` is skipped with a reason rather than faked.

That is a smaller loss than it looks. The ordinances ARE the enactments — the codified code
is a derived, editorially-arranged rendering of them — so what this profile captures is the
primary instrument, with recording dates, rather than a secondary presentation of it.

DUPLICATE UPLOADS. The same ordinance appears more than once under different upload epochs
(e.g. Ordinance No. 2026-006 at both 1783608453_ and 1783608618_). Deduplicated on the
ordinance number, keeping the highest upload epoch, or the corpus would hold two documents
claiming to be the same law.

Verified 2026-07-31: 932 objects, 896 ordinance PDFs, one page, honest User-Agent, HTTP 200.
"""
from __future__ import annotations

import re
import urllib.parse

# FOUR naming conventions, and missing the fourth would have silently dropped the NEWEST law.
#
#   Ordinance No. 80-201       the dominant form, 835 of 896
#   Ordinance 2021-002         same thing, no "No."
#   Ordinance No. PL-17 / CG 3 the pre-1980 planning and county-government series
#   Ord 2023-003               the abbreviated form the county switched to
#
# The abbreviation is the one that matters. Every file using it is from 2023-2026, so a
# pattern requiring the word "Ordinance" in full drops eleven of the county's most recent
# ordinances while reporting 816 sources and looking complete. Caught only because discover()
# prints what it cannot parse instead of skipping quietly — which is the entire argument for
# reporting gaps rather than filtering them away.
#
# Resolutions and Orders are kept too: they are enactments of the same body, they sit in the
# same directory, and the county cites them the same way.
ORD_NO = re.compile(
    r"\b(?:Ordinance|Ord|Resolution|Res|Order)\b\.?\s*(?:No\.?\s*)?"
    r"([A-Z]{0,3}[\s-]?\d[\d-]*)", re.I)
UPLOAD_EPOCH = re.compile(r"^(\d{9,})_")

# Not enactments. A voters' pamphlet and an appendix to an agreement are real documents but
# they are not county law, and typing them as `ordinance` would misstate what they are.
NOT_LAW = re.compile(r"voters?\s+pamphlet|^appendix\b", re.I)

PROFILE = {
    "slug": "deschutes",
    "name": "Deschutes",
    "discovery": "mco-s3",
    "site": "https://www.deschutescounty.gov",
    "crawl": {
        "decision": "proceed",
        "checked": "2026-07-31",
        "basis": (
            "No AI-agent directive on any host used here. The S3 bucket serves no "
            "robots.txt at all and the MCO subdomain returns 404 for robots.txt and "
            "sitemap.xml, so there is nothing to honour or decline. The county's own "
            "Laserfiche system DOES disallow the paths its documents live behind, and that "
            "family is skipped for exactly that reason — see families.policies."),
        "hosts": [
            {"host": "s3-us-west-2.amazonaws.com", "robots_url": None, "ai_block": False,
             "content_signal": None,
             "notes": "ListObjectsV2 answers unauthenticated; no robots.txt served"},
            {"host": "deschutescounty.municipalcodeonline.com",
             "robots_url": "https://deschutescounty.municipalcodeonline.com/robots.txt",
             "ai_block": False, "content_signal": None,
             "notes": "robots.txt and sitemap.xml both 404 — no directives exist"},
            {"host": "weblink.deschutes.org",
             "robots_url": "https://weblink.deschutes.org/robots.txt",
             "ai_block": False, "content_signal": None,
             "notes": "Disallows /DocView.aspx and /Search.aspx — the county's own document "
                      "system refusing the exact retrieval path. Path-specific, not an "
                      "AI-agent block, and it is the county speaking about its own site "
                      "rather than a vendor speaking about the county's law. Honoured."},
        ],
    },
    "upstream_signal": (
        "No feed. New ordinances appear as new S3 keys with a fresh upload epoch, so a "
        "re-list and diff of the key set is the freshness check — cheap, and exact."),
    "families": {
        "orders": {
            "discovery": "mco-s3",
            "prefix": "deschutescounty/ordinances/documents/",
            "format": "pdf",
            "key_re": r"Ordinance",
        },
        "code": {
            "skip": (
                "The codified Deschutes County Code exists only inside the AngularJS SPA at "
                "deschutescounty.municipalcodeonline.com, which renders no server-side HTML. "
                "The S3 bucket that backs it holds the ORDINANCES (896, captured above) and "
                "not the codified rendering — verified by listing all 932 objects. Ingesting "
                "the enactments and honestly recording the absence of the codified text is "
                "better than scraping a rendering we cannot verify.")},
        "land-use": {
            "skip": (
                "Deschutes County Code Titles 18-23 (zoning, comprehensive plan) live in the "
                "same SPA as the rest of the code, so the same limitation applies. The "
                "land-use ORDINANCES are present in `orders`.")},
        # CORRECTED 2026-08-01, after actually browsing the repository instead of
        # inferring from the robots file. The earlier reason said the disallow blocks this
        # family. That was too broad and it hid the more useful finding.
        #
        # weblink.deschutes.org/robots.txt disallows exactly four paths:
        #     /MyWebLink.aspx  /Login.aspx  /Search.aspx  /DocView.aspx
        # `/Browse.aspx` is NOT among them, so browsing the repository is permitted. Browsed
        # it (the listing is client-side, so rendered): PUBLIC-Administration holds Audit
        # Committee Minutes, BOCC Meetings, Internal Audit Reports and one code-information
        # document. THE PUBLIC RECORDS POLICY IS NOT IN THE PUBLIC REPOSITORY AT ALL.
        #
        # Two separate facts, and conflating them was the error:
        #   1. The policy is not published here — a finding about what Deschutes posts.
        #   2. The documents that ARE here require /DocView.aspx, the one retrieval path
        #      the county disallowed — a rule we honour.
        #
        # The county's own site compounds this: /292/Public-Records-Requests refers
        # repeatedly to "the County's policy relating to submittal" and links no document.
        # So Deschutes plainly HAS a public records policy — its website enforces it — and
        # has not posted it. That is neither an absence at the county nor a wall we could
        # pass, and PLAN.md's Phase 12 Done-when named this exact document before anyone
        # checked whether it existed.
        "policies": {
            "skip": (
                "NOT PUBLISHED, and separately NOT RETRIEVABLE. Browsing Laserfiche is "
                "permitted (/Browse.aspx is not in the four-path disallow list) and shows "
                "the public records policy is not in the public repository — only audit "
                "minutes, BOCC meetings and audit reports. Those documents in turn require "
                "/DocView.aspx, which the county DOES disallow and which is honoured. The "
                "county's own site cites the policy without linking it. Deschutes has this "
                "policy; it has not posted it. Procurement solicitations are on BidLocker, "
                "a third party, and are not policy.")},
    },
}


def _instrument(name: str) -> tuple[str, str] | None:
    """(kind, number) from a filename, or None if it is not an enactment."""
    stem = re.sub(r"^\d{9,}_(?:[\d-]+-)?", "", name)
    if NOT_LAW.search(stem):
        return None
    m = ORD_NO.search(stem)
    if not m:
        return None
    word = m.group(0).split()[0].rstrip(".").lower()
    kind = {"ord": "Ordinance", "ordinance": "Ordinance", "res": "Resolution",
            "resolution": "Resolution", "order": "Order"}.get(word, "Ordinance")
    return kind, re.sub(r"[\s-]+", "-", m.group(1).strip().lower())


def discover(profile: dict, family: str, cfg: dict) -> list[dict]:
    """S3 enumeration, then dedupe on the ordinance number.

    THE DEDUPE IS NOT COSMETIC. The bucket holds the same ordinance under multiple upload
    epochs, and without this the corpus would carry two documents both claiming to be
    Ordinance No. 2026-006 — with no way for a reader to tell which is the law.
    """
    from src.ingest_counties import discover_mco_s3

    best: dict[str, tuple[int, dict]] = {}
    unparsed: list[dict] = []
    for item in discover_mco_s3(profile, family, cfg):
        name = item["name"]
        parsed = _instrument(name)
        epoch_m = UPLOAD_EPOCH.match(name)
        epoch = int(epoch_m.group(1)) if epoch_m else 0
        if parsed is None:
            unparsed.append(item)
            continue
        kind, num = parsed
        key = f"{kind.lower()}-{num}"
        item = {**item, "ord_no": num, "kind": kind,
                "title": f"{kind} No. {num.upper()}",
                "id": f"deschutes-orders-{key}"}
        # Highest upload epoch wins. The bucket carries the same enactment under several
        # epochs, and without this the corpus holds two documents each claiming to be
        # Ordinance No. 2026-006 with nothing telling a reader which is the law.
        if key not in best or epoch > best[key][0]:
            best[key] = (epoch, item)

    out = sorted((v[1] for v in best.values()), key=lambda d: d["id"])
    if unparsed:
        # Reported, never dropped silently. A gap nobody is told about reads as completeness,
        # and this print is what caught the abbreviated `Ord 2023-003` form that was
        # discarding eleven of the county's most recent ordinances.
        print(f"  deschutes: {len(unparsed)} object(s) held no enactment number and were "
              f"skipped: {', '.join(i['name'][:44] for i in unparsed[:3])}")
    return out
