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

**MARION IS UNAVAILABLE, AND THIS IS THE HONEST OUTCOME RATHER THAN A FAILURE TO TRY.**

codepublishing.com sits behind a Cloudflare managed challenge that answers
**HTTP 403 with `cf-mitigated: challenge`** to `src/fetch.py`'s honest, self-identifying
User-Agent. A plain `curl` with a browser User-Agent gets 200 and the full index — so the
content is public, and the only thing standing between this corpus and 17 code chapters is
that we say who we are.

We do not step over that. The operator's decision (PLAN.md Phase 12) is that vendor
*robots directives* are not treated as binding for the text of county law, on the reasoning
that the county authors its law and the vendor hosts it. A WAF challenge is a different
thing: it is a technical access control, and the only way past it is to misrepresent what we
are. Declining to honour a stated preference is not the same act as disguising identity to
defeat a control, and this corpus does the first and not the second.

So `crawl.decision` is `unavailable` and every family is skipped with that reason. This is
recorded as a fact about OUR ACCESS, never as a fact about Marion County — the same
`none-found` versus `could-not-verify` distinction the 36-county survey turns on. Marion
publishes its code; we did not take it.

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
        "decision": "unavailable",
        "checked": "2026-07-31",
        "basis": (
            "Cloudflare managed challenge: HTTP 403 with cf-mitigated: challenge to an "
            "honest, self-identifying User-Agent. A browser-identified curl gets 200, so "
            "the content is public and only our truthful identification is refused. Getting "
            "past it would require misrepresenting what we are, which is a different act "
            "from declining to honour a robots directive, and one this corpus does not "
            "take. Recorded as a fact about OUR ACCESS, never about Marion County: Marion "
            "publishes its code; we did not take it. robots.txt separately names no AI "
            "agent, so the corpus-wide vendor-directive decision is not engaged here."),
        "hosts": [
            {"host": "www.codepublishing.com",
             "robots_url": "https://www.codepublishing.com/robots.txt",
             "ai_block": False, "content_signal": None,
             "notes": "robots.txt disallows /cgi-bin/ /CPC/ /dtSearch/ /errors/ /search/ "
                      "/Search_forms/ and *.pl *.pm *.js *.pdf *.rtf *nt.html — no AI agent "
                      "named, and none of it covers the HTML code tree. The block is not "
                      "robots.txt at all: a Cloudflare managed challenge returns 403 to the "
                      "honest agent while a browser-identified curl gets 200."},
        ],
    },
    "upstream_signal": (
        "No feed. Code Publishing republishes the whole static site on codification, so "
        "re-hashing each chapter page detects an amendment. Chapter paths are stable across "
        "republications."),
    "families": {
                "code": {
            "skip": ("Unavailable: codepublishing.com answers HTTP 403 (Cloudflare managed challenge) to an honestly-identified agent. See the module docstring — this is an access failure on our side, not an absence at Marion County."),
        },
                "land-use": {
            "skip": ("Unavailable: codepublishing.com answers HTTP 403 (Cloudflare managed challenge) to an honestly-identified agent. See the module docstring — this is an access failure on our side, not an absence at Marion County."),
        },
                "orders": {
            "skip": ("Unavailable: codepublishing.com answers HTTP 403 (Cloudflare managed challenge) to an honestly-identified agent. See the module docstring — this is an access failure on our side, not an absence at Marion County."),
        },
                "policies": {
            "skip": ("Unavailable: codepublishing.com answers HTTP 403 (Cloudflare managed challenge) to an honestly-identified agent. See the module docstring — this is an access failure on our side, not an absence at Marion County."),
        },
    },
}
