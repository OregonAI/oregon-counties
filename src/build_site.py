#!/usr/bin/env python3
"""Build the GitHub Pages site into ./site/ (gitignored; produced at deploy time).

    python3 src/build_site.py

Chrome, CSS and the cross-corpus contracts live in `corpus_toolkit.site` — see that module
for why they are shared rather than copied per corpus. This file owns only what is specific
to this corpus: its numbers and what they mean.

THIS REPLACES the reusable publish-index workflow. That workflow publishes
corpus-index.json and nothing else, which is why this corpus's site root 404'd while its
index served fine. The two must never both exist here — they fight over the `pages`
concurrency group — and `corpus_toolkit.site.build` keeps emitting corpus-index.json at the
same URL, which is load-bearing outside this repository.
"""
import collections
import json
import pathlib
import re
import sys

import yaml

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from corpus_toolkit import config as config_mod                       # noqa: E402
from corpus_toolkit.site import Page, Section, Tile, build            # noqa: E402

REPO = pathlib.Path(__file__).resolve().parent.parent


def stats() -> dict:
    counties = yaml.safe_load((REPO / "_meta/counties.yml").read_text())["counties"]
    built = [c for c in counties if c.get("built")]
    total_pop = sum(c["population"] for c in counties)
    graph = json.loads((REPO / "_meta/graph.json").read_text())

    disp = yaml.safe_load((REPO / "_meta/ors-dispositions.yml").read_text())
    ocr = sum(1 for p in (REPO / "counties").rglob("*.md")
              if re.search(r"^text_source:\s*ocr", p.read_text(errors="replace"), re.M))
    return {
        "documents": graph["n_nodes"],
        "edges": graph["n_edges"],
        "built": len(built),
        "counties": len(counties),
        "pop_pct": round(sum(c["population"] for c in built) / total_pop * 100),
        "ocr": ocr,
        "renumbered": disp["n_renumbered"],
        "repealed": disp["n_repealed"],
    }


def main() -> int:
    s = stats()
    cfg = config_mod.load(REPO / "_meta/corpus.yml")

    out = build(Page(
        config=cfg,
        repo="oregon-counties",
        title="Oregon County Code, Ordinances & Policy",
        description=("A non-authoritative, machine-readable mirror of county code, "
                     "ordinances, board orders and administrative policy for Oregon "
                     "counties, with citations resolved into state law."),
        eyebrow="Oregon · county government",
        headline="The law your county actually applies to you",
        lede_html=(
            f"<b>{s['documents']:,} documents</b> from <b>{s['built']} of Oregon's "
            f"{s['counties']} counties</b> — {s['pop_pct']}% of the state's population. "
            "Land use, procurement, public records: the end of the authority chain that "
            "reaches people, and the one nobody publishes in a single place."),
        disclaimer=("NON-AUTHORITATIVE reference — not the official county code. Always "
                    "verify against the county's own published text."),
        tiles=[
            Tile("Documents", f"{s['documents']:,}",
                 "county code, ordinances, board orders and administrative policy"),
            Tile("Counties", f"{s['built']} of {s['counties']}",
                 f"{s['pop_pct']}% of Oregon's population; the rest are in progress"),
            Tile("Citations into state law", f"{s['edges']:,}",
                 "every ORS and OAR reference the text actually makes"),
            Tile("Recovered by OCR", f"{s['ocr']:,}",
                 "scans with no text layer, read by two independent engines that agreed"),
        ],
        sections=[
            Section("Why this corpus is hard", """
    <ul class="plain">
      <li><b>Thirty-six counties, no common platform.</b> Municode, CivicPlus, Granicus,
        American Legal, Laserfiche, plain PDF directories, and several sites that are
        simply one person's HTML. Each was surveyed before anything was ingested.</li>
      <li><b>Publication is not uniform and the gaps are recorded as gaps.</b> A county
        that publishes only part of its code is marked as such rather than presented as
        complete, and nine counties are deferred rather than half-ingested.</li>
      <li><b>Scanned paper is common.</b> Documents with no text layer are recovered by
        two OCR engines reading independently, and promoted only where they agree — never
        by one engine's confident guess.</li>
    </ul>"""),
            Section("Citations resolve into state law", f"""
    <ul class="plain">
      <li>A county ordinance citing <code>ORS 215.203</code> resolves into
        <a href="https://oregonai.github.io/executive-regulatory-frameworks/">Executive
        Regulatory Frameworks</a> and returns the statute's title and URL — one copy of the
        law, cited from wherever it is needed.</li>
      <li><b>A citation that resolves to nothing is not automatically a gap.</b>
        {s['renumbered']:,} of the sections cited here were <b>renumbered</b> — the text
        still exists, under a new number — and {s['repealed']:,} were <b>repealed</b>, which
        is a complete answer rather than a missing document. Both are reported as what they
        are.</li>
      <li>These are recorded as <code>references_external</code>, not as
        <code>implements</code>. A county ordinance citing a statute usually is implementing
        it. <b>Usually is not a basis for asserting it as fact</b>, so the stronger claim
        stays empty until something measures it.</li>
    </ul>"""),
            Section("For agents", """
    <ul class="plain">
      <li><b>MCP server</b> — tools: <code>search_corpus</code>, <code>get_document</code>,
        <code>resolve_citation</code>, <code>corpus_overview</code>,
        <code>graph_neighbors</code>, <code>authority_chain</code>,
        <code>issuing_body_profile</code>.</li>
      <li><b>Every document carries provenance</b> — source URL, retrieval date and a
        content hash — and its full text is verified line by line against the snapshot it
        was extracted from.</li>
      <li><b>County law binds real decisions.</b> These are mirrors, not the official
        record; verify against the cited source before acting on one.</li>
    </ul>"""),
        ],
        footer_note=("Unofficial and non-authoritative; not affiliated with any Oregon "
                     "county or with the State of Oregon."),
    ))
    print(f"built site/ — {s['documents']:,} documents, {s['built']} counties")
    print(f"  corpus-index.json: {out['index']}")
    print(f"  copied: {', '.join(out['copied']) or 'nothing'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
