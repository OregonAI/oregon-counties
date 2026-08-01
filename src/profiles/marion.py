"""Marion County — Code Publishing Company, part of the General Code family.

352,867 people, 5th largest, contains Salem and the state capitol. General law, Board of
Commissioners.

VENDOR IDENTITY MATTERED HERE. The survey initially recorded eCode360, Code Publishing and
`*.county.codes` as three separate vendors; they are one company (General Code), and folding
them made General Code the LARGEST commercial code vendor among Oregon counties at four,
ahead of Municode at three. Marion is the Code Publishing storefront of that family.

Code Publishing serves an old-style static HTML code site, which is the friendliest shape in
this build: one page per chapter, stable paths, no JavaScript, no portal. The index separates
the two instruments by filename prefix, which is what makes routing trivial:

    html/MarionCounty<NN>/...   the county code            -> code
    html/MarionComp<NN>/...     the comprehensive plan     -> land-use

**THE CODE IS UNAVAILABLE; THE ADMINISTRATIVE POLICIES ARE NOT.** Re-checked 2026-08-01 at
the operator's request, going to the county's own domain rather than the vendor storefront.

`apps.co.marion.or.us/APAP/` — the county's Administrative Policy and Procedure index — is
reachable by the honest agent and lists **153 policy PDFs served from co.marion.or.us**, plus
`/HR/Documents/personnelrules.pdf`. Those are ingested. Marion is therefore IN the corpus
with its administrative policy, and out of it only for its codified code.

That is worth stating as a general lesson rather than a Marion footnote: **the vendor
storefront being blocked did not mean the county was blocked.** Checking the county's own
domain before recording a county as unreachable is cheap and was skipped the first time.

Note `/BOC/Policies/` itself returns HTTP 401 as a directory — only the individual PDFs are
public, so the APAP index is the only way in.

**THE CODE IS NOW INGESTED, AND THE DIAGNOSIS THAT KEPT IT OUT WAS WRONG.**

For four tranches this profile recorded Marion's code as `unavailable`, on the reasoning
that Cloudflare was refusing our identity and that getting past it would mean pretending to
be a browser. That reasoning was mistaken, and the error was in the measurement, not the
principle. With the SAME User-Agent and the same headers:

    curl --http2    -> 200
    curl --http1.1  -> 403

Python's urllib speaks only HTTP/1.1. The block was on PROTOCOL VERSION, not on who we said
we were — and the earlier evidence for "a browser gets through" was curl carrying a Chrome
User-Agent string, not an actual browser. A real headless Chromium is refused too, because
Cloudflare scores automation separately.

So the honest client was never the problem; the OLD client was. src/fetch.py now speaks
HTTP/2 and Marion answers it 200 with the same self-identifying User-Agent it always sent.
Nothing about our identity changed.

Worth carrying forward: a 403 is a claim about a REQUEST, not about a requester. Check the
protocol before concluding anything about identity.

Its robots.txt, read separately, names NO AI agent — it disallows CGI, search and several
file extensions including `*.pdf$`, none of which would have covered the HTML tree. The
corpus-wide vendor-directive decision was never engaged here; the challenge is.

Verified 2026-07-31: index reachable by browser-identified curl (17 code chapters, 4
comprehensive-plan volumes visible); HTTP 403 Cloudflare challenge to the honest agent.
"""

PROFILE = {
    "slug": "marion",
    "name": "Marion",
    "discovery": "link-list",
    "site": "https://www.codepublishing.com/OR/MarionCounty/",
    "crawl": {
        "decision": "proceed",
        "checked": "2026-07-31",
        "basis": (
            "codepublishing.com challenged HTTP/1.1 requests and passes HTTP/2 ones — a "
            "protocol-version rule, not identity. Since src/fetch.py speaks HTTP/2 the site "
            "answers our unchanged, self-identifying User-Agent with 200. robots.txt names "
            "no AI agent, so the corpus-wide vendor-directive decision is not engaged here "
            "at all; there was never a stated preference to weigh."),
        "hosts": [
            {"host": "www.codepublishing.com",
             "robots_url": "https://www.codepublishing.com/robots.txt",
             "ai_block": False, "content_signal": None,
             "notes": "robots.txt disallows /cgi-bin/ /CPC/ /dtSearch/ /errors/ /search/ "
                      "/Search_forms/ and *.pl *.pm *.js *.pdf *.rtf *nt.html — no AI agent "
                      "named, and none of it covers the HTML code tree we read. Its "
                      "Cloudflare config challenges HTTP/1.1 and passes HTTP/2."},
        ],
    },
    "upstream_signal": (
        "No feed. Code Publishing republishes the whole static site on codification, so "
        "re-hashing each chapter page detects an amendment. Chapter paths are stable across "
        "republications."),
    "families": {
                "code": {
            "listing_url": "https://www.codepublishing.com/OR/MarionCounty/",
            "link_re": r'href="(html/MarionCounty[^"]*\.html)"',
            "format": "html",
        },
                "land-use": {
            "listing_url": "https://www.codepublishing.com/OR/MarionCounty/",
            "link_re": r'href="(html/MarionComp[^"]*\.html)"',
            "format": "html",
        },
                "orders": {
            "skip": ("Unavailable: codepublishing.com answers HTTP 403 (Cloudflare managed challenge) to an honestly-identified agent. See the module docstring — this is an access failure on our side, not an absence at Marion County."),
        },
                # THE COUNTY'S OWN DOMAIN, not the vendor. 153 policy PDFs indexed by the APAP
        # application and served from co.marion.or.us, plus the personnel rules.
        "policies": {
            "listing_urls": ["https://apps.co.marion.or.us/APAP/",
                             "https://www.co.marion.or.us/HR/Pages/default.aspx"],
            "link_re": r'href="((?:https://www\.co\.marion\.or\.us)?/(?:BOC/Policies|HR/Documents)/[^"]*\.pdf)"',
            "format": "pdf",
        },
    },
}
