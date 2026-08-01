"""Malheur County — WordPress uploads, and a COUNTY COURT rather than a Board.

32,315 people, 20th largest, general law. **Governed by a County Court** — a county judge
sitting with two commissioners — which is why its enactments are court orders and journal
entries, and why `check_guardrails` rejects any document here naming a Board of
Commissioners. Six of Oregon's 36 counties work this way.

THE AI-BLOCK CASE THIS COUNTY RAISES. `codelibrary.amlegal.com` — American Legal, where
Malheur's codified code lives — names ClaudeBot AND GPTBot with `Disallow: /` and sets
`Content-Signal: ai-train=no`. It is also the one vendor of the four that does NOT serve our
honest agent: it returns 403.

So the code family is `unavailable` on the same reasoning as Marion: the refusal is at the
HTTP layer, and the only way past is to stop identifying honestly. What Malheur publishes on
its OWN site — land use, employee policy, court agendas — is reachable and is taken. The
county is therefore present in the corpus without its codified code, and the manifest says
exactly that rather than implying Malheur publishes little.

Verified 2026-08-01: malheurco.org serves the honest agent HTTP 200; codelibrary.amlegal.com
returns 403. WordPress uploads under /wp-content/uploads/.
"""

_UP = r'href="([^"]*/wp-content/uploads/[^"]*\.pdf)"'

PROFILE = {
    "slug": "malheur",
    "name": "Malheur",
    "discovery": "link-list",
    "site": "https://www.malheurco.org",
    "crawl": {
        "decision": "proceed",
        "checked": "2026-08-01",
        "basis": (
            "The county's own site states no AI-agent directive and serves the honest agent "
            "HTTP 200; those families are taken. The CODE is a different matter: American "
            "Legal names ClaudeBot and GPTBot with Disallow: / and Content-Signal: "
            "ai-train=no, AND returns 403 to the honest agent — so the block is at the HTTP "
            "layer, not just in a directives file, and getting past it would mean "
            "misrepresenting what we are. Code family recorded unavailable."),
        "hosts": [
            {"host": "www.malheurco.org", "robots_url": "https://www.malheurco.org/robots.txt",
             "ai_block": False, "content_signal": None,
             "notes": "County's own WordPress site. 200 to the honest agent."},
            {"host": "codelibrary.amlegal.com",
             "robots_url": "https://codelibrary.amlegal.com/robots.txt",
             "ai_block": True,
             "content_signal": "ai-train=no",
             "notes": "American Legal. Names ClaudeBot and GPTBot Disallow: /. Returns 403 "
                      "to the honest agent — NOT fetched, and not retried in disguise."},
        ],
    },
    "upstream_signal": (
        "No feed. WordPress upload paths are dated by year/month, so a new document appears "
        "as a new upload path in the relevant department page."),
    "families": {
        "land-use": {"listing_url": "https://www.malheurco.org/planning-department/",
                     "link_re": _UP, "format": "pdf"},
        "policies": {"listing_url":
                     "https://www.malheurco.org/malheur-county-employee-services/",
                     "link_re": _UP, "format": "pdf"},
        "code": {
            "skip": (
                "UNAVAILABLE, not absent. Malheur's codified code is on American Legal "
                "(codelibrary.amlegal.com/codes/malheurcoor), which returns HTTP 403 to an "
                "honestly-identified agent. Malheur publishes its code; we did not take it. "
                "See the module docstring for why we do not step over that."),
        },
        "orders": {
            "skip": (
                "County Court agendas and minutes are published as a per-meeting listing "
                "rather than an index of adopted orders. Note the noun: Malheur is governed "
                "by a County Court, so its enactments are court orders, not board orders. "
                "Deferred."),
        },
    },
}
