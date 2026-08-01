#!/usr/bin/env python3
"""Mirror the ORS dispositions this corpus actually needs from executive-regulatory-frameworks.

    python3 src/sync_dispositions.py            # fetch, prune, write
    python3 src/sync_dispositions.py --check    # CI: fail if the mirror is stale

WHAT THIS IS FOR. 856 ORS citations in this corpus resolve to no document in ERF, and 699 of
them are not gaps at all:

    430   the section was RENUMBERED — the text still exists, under a new number, and for
          362 of them ERF holds the target right now
    269   the section was REPEALED — there is no text to hold, which is a complete answer
    157   no disposition recorded anywhere

Without this, `resolve_citation("ORS 197.296")` answers "holds no document with id
ors-197.296" for a section whose text is sitting in ERF as 197A.350. That sentence is true and
reads as "the corpus is incomplete" — the same misleading shape that produced two false
coverage-gap issues against ERF (#81, #90). The corpus is not incomplete. County comprehensive
plans adopted before 2019 cite the numbers that were correct when they were adopted.

WHY A COMMITTED MIRROR RATHER THAN A LIVE FETCH. `resolve_citation` runs inside an MCP server
answering a user's question; reaching across the network mid-answer buys staleness protection
at the cost of latency and a new failure mode on every call. The sibling INDEX is fetched live
because it is the corpus's own contents and changes with every ingest. Dispositions change
when the legislature renumbers something, which is not a per-query concern.

WHY raw.githubusercontent AND NOT THE PAGES SITE, which is what corpus.yml's `siblings:` block
otherwise recommends. That advice exists because a committed index can fall behind the corpus
it describes. It cannot happen here: ERF gates `build_ors_disposition.py --check` in CI, so the
committed file provably matches the snapshots it was mined from. ERF does not publish the
disposition to Pages at all, so raw main is both the source of truth and the only URL.

PRUNED TO WHAT THIS CORPUS CITES. Upstream carries 29,215 rows; this corpus cites a few
hundred of them. Mirroring all of it would put 29,000 lines of another repo's data in this one
for no gain, and would bury the rows a reviewer might actually want to check.
"""
from __future__ import annotations

import argparse
import collections
import pathlib
import re
import sys
import urllib.request

import yaml

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from corpus_toolkit import config as config_mod          # noqa: E402
from corpus_toolkit.repo import content_files            # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "_meta" / "ors-dispositions.yml"

SOURCE = ("https://raw.githubusercontent.com/OregonAI/executive-regulatory-frameworks/"
          "main/_meta/catalog/ors-disposition.yml")

ORS = re.compile(r"\bORS\s+(\d+[A-Z]?\.\d{3,})")
FULLTEXT = re.compile(r"^## Full text\s*$(.*)", re.M | re.S)

UA = ("OregonAI-CivicCorpus/1.0 (+https://github.com/OregonAI/oregon-counties; "
      "public-records archival)")


def cited_sections() -> set[str]:
    """Every ORS section this corpus cites, lowercased, read from `## Full text` only.

    Same source as `link_citations.py` and for the same reason: a citation in a
    curator-written summary is one we invented.
    """
    config = config_mod.load(ROOT / "_meta" / "corpus.yml")
    out: set[str] = set()
    for path in content_files(config):
        m = FULLTEXT.search(path.read_text(encoding="utf-8", errors="replace"))
        if m:
            out |= {n.lower() for n in ORS.findall(m.group(1))}
    return out


def fetch_upstream() -> dict:
    req = urllib.request.Request(SOURCE, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:      # noqa: S310 — pinned https URL
        return yaml.safe_load(r.read().decode("utf-8"))


def build() -> str:
    cited = cited_sections()
    up = fetch_upstream()
    rows = []
    for r in up.get("sections") or []:
        if r["section"] not in cited:
            continue
        row = {"section": r["section"], "status": r["status"]}
        if r.get("year") is not None:
            row["year"] = r["year"]
        if r.get("targets"):
            row["targets"] = r["targets"]
        if r.get("partial"):
            row["partial"] = True
        # Carried through verbatim. It is the evidence, and a reader checking a redirect
        # should not have to open another repository to see what the statute book printed.
        if r.get("source_phrase"):
            row["source_phrase"] = r["source_phrase"]
        rows.append(row)
    rows.sort(key=lambda r: r["section"])
    by = collections.Counter(r["status"] for r in rows)

    doc = {
        "note": ("MIRRORED, NOT AUTHORED HERE. Pruned from "
                 "executive-regulatory-frameworks' _meta/catalog/ors-disposition.yml to the "
                 "ORS sections this corpus actually cites. Regenerate with "
                 "`python3 src/sync_dispositions.py`; CI gates it with --check. "
                 "'renumbered' means the text still exists under `targets`; 'repealed' means "
                 "there is no text. Each row carries the verbatim `source_phrase` it was "
                 "mined from, so a redirect can be checked against the statute book without "
                 "opening another repository. Non-authoritative — verify at "
                 "oregonlegislature.gov."),
        "source": SOURCE,
        "n_renumbered": by.get("renumbered", 0),
        "n_repealed": by.get("repealed", 0),
        "sections": rows,
    }
    return yaml.safe_dump(doc, sort_keys=False, allow_unicode=True, width=100)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()

    text = build()
    if a.check:
        if not OUT.is_file() or OUT.read_text(encoding="utf-8") != text:
            print(f"FAIL — {OUT.relative_to(ROOT)} is stale. "
                  f"Re-run: python3 src/sync_dispositions.py", file=sys.stderr)
            return 1
        print(f"OK — {OUT.relative_to(ROOT)} matches upstream.")
        return 0

    OUT.write_text(text, encoding="utf-8")
    d = yaml.safe_load(text)
    print(f"wrote {OUT.relative_to(ROOT)}: {d['n_renumbered']} renumbered, "
          f"{d['n_repealed']} repealed (pruned to sections this corpus cites)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
