#!/usr/bin/env python3
"""Populate `relationships.references_external` from ORS/OAR citations in each document.

    python3 src/link_citations.py            # write
    python3 src/link_citations.py --check    # CI: fail if any document is out of date

WHY `references_external` AND NOT `implements`. `implements` asserts that this county
instrument implements that state law — a legal characterisation. What is actually measured
here is that the document's text CITES the section. Those are different claims, and the
gap between them is exactly the kind of quiet overstatement this platform keeps getting
caught by: oregon-audits' county edge looked like an authority relationship until it was
measured and turned out to be 70 mentions and zero citations of county law.

A county ordinance citing ORS 215.203 usually IS implementing it. Usually is not a basis for
writing it into the graph as fact. `implements` stays empty until something measures it.

MEASURED BEFORE BUILDING (2026-07-31, 873 documents):
    444 documents (51%) cite ORS or OAR
    1,297 distinct ORS sections, 149 distinct OAR rules
    top ORS: 215.203 (46), 215.503 (33), 215.213 (28), 203.045 (28), 197.732 (22)
    top OAR: 660-012-0060 (25), 660-033-0020 (15), 660-034-0035 (11)

The top of both lists is the land-use regime — exclusive farm use, goal exceptions, the
Transportation Planning Rule, agricultural lands — which is the state->county edge the seed
predicted would be densest. That prediction is now confirmed rather than asserted.

CITATIONS ARE READ FROM `## Full text` ONLY. A citation in `## At a glance` would be
curator-written, and an edge built from our own summary prose is an edge we invented.
"""
from __future__ import annotations

import argparse
import pathlib
import re
import sys

import yaml

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from corpus_toolkit import config as config_mod          # noqa: E402
from corpus_toolkit.repo import content_files            # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent

# >= 3 digits after the dot, deliberately. PDF extraction splits long numbers across line
# breaks, so a looser pattern turns a truncated "ORS 215.2" into a confident reference to a
# section that does not exist. Carried over from oregon-audits, which measured the problem.
ORS = re.compile(r"\bORS\s+(\d+[A-Z]?\.\d{3,})")
OAR = re.compile(r"\bOAR\s+(\d{3}-\d{3}-\d{4})")

# One document can cite a great many sections — a comprehensive plan cites hundreds. Capped
# so the graph stays usable, and the cap is REPORTED rather than silent: a truncation nobody
# is told about reads as completeness.
MAX_REFS = 60

FULLTEXT = re.compile(r"^## Full text\s*$(.*)", re.M | re.S)


# Citations the source PDF's own text layer renders as something that cannot exist, with the
# reading verified off the rendered page by two independent OCR engines. Written by
# `relayer_citations.py`; consulted here so the correction SURVIVES REGENERATION.
#
# This must be data rather than a one-time edit to the documents. `--check` is a CI gate that
# recomputes this list from the verbatim text, so a correction applied by hand would be
# reported as drift on the next run and reverted by the next real one — the fix would quietly
# undo itself and CI would call the undoing correct.
CORRECTIONS = ROOT / "_meta" / "citation-corrections.yml"


def corrections() -> dict[str, dict[str, str]]:
    if not CORRECTIONS.is_file():
        return {}
    data = yaml.safe_load(CORRECTIONS.read_text(encoding="utf-8")) or {}
    return {d["document"]: {c["extracted"]: c["printed"] for c in d.get("citations") or []}
            for d in data.get("documents") or []}


def citations(body: str, fixes: dict[str, str] | None = None) -> list[str]:
    m = FULLTEXT.search(body)
    if not m:
        return []
    text = m.group(1)
    fixes = fixes or {}

    # Substitution, not addition: the impossible citation is not something the document ALSO
    # points at, it is a misreading of the one it does point at. Keeping both would make the
    # corpus assert an edge to a chapter that does not exist.
    #
    # Applied per scheme rather than to one merged list, so a corrected document keeps the
    # same ORS-then-OAR ordering as every other document. Sorting the merged list instead
    # interleaved the two — a diff that looked like citations had moved when only one line
    # had changed.
    ors = sorted({fixes.get(f"ORS {n}", f"ORS {n}") for n in ORS.findall(text)})
    oar = sorted({fixes.get(f"OAR {n}", f"OAR {n}") for n in OAR.findall(text)})
    return ors + oar


def rewrite(path: pathlib.Path, refs: list[str]) -> bool:
    """Replace the references_external list in place. Returns True if the file changed.

    Edited as TEXT rather than by round-tripping the YAML, because a dump would reflow every
    frontmatter block in the corpus and bury the one line that actually changed.
    """
    original = path.read_text(encoding="utf-8")
    block = ("  references_external: []" if not refs else
             "  references_external:\n" + "\n".join(f"    - {r}" for r in refs))
    new = re.sub(r"^  references_external:(?: \[\])?(?:\n    - .*)*$",
                 lambda _: block, original, count=1, flags=re.M)
    if new == original:
        return False
    path.write_text(new, encoding="utf-8")
    return True


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()

    config = config_mod.load(ROOT / "_meta" / "corpus.yml")
    fixes = corrections()
    changed, linked, total_refs, capped = [], 0, 0, []

    for path in content_files(config):
        body = path.read_text(encoding="utf-8")
        refs = citations(body, fixes.get(path.stem))
        if len(refs) > MAX_REFS:
            capped.append((path.name, len(refs)))
            refs = refs[:MAX_REFS]
        if refs:
            linked += 1
            total_refs += len(refs)
        if args.check:
            block = ("  references_external: []" if not refs else
                     "  references_external:\n" + "\n".join(f"    - {r}" for r in refs))
            if block not in body:
                changed.append(path.relative_to(ROOT))
        elif rewrite(path, refs):
            changed.append(path.relative_to(ROOT))

    if args.check:
        if changed:
            print(f"FAIL — {len(changed)} document(s) have stale references_external. "
                  f"Re-run: python3 src/link_citations.py", file=sys.stderr)
            for c in changed[:10]:
                print(f"  {c}", file=sys.stderr)
            return 1
        print(f"OK — references_external current on all documents ({linked} cite state law).")
        return 0

    print(f"{linked} document(s) cite ORS/OAR; {total_refs} references written; "
          f"{len(changed)} file(s) changed.")
    if capped:
        # Named, not summarised away. These are the documents whose citation lists are
        # incomplete in the graph, and a reader asking "what does this plan cite" gets a
        # truncated answer for exactly these.
        print(f"{len(capped)} document(s) hit the {MAX_REFS}-reference cap and are "
              f"TRUNCATED in the graph:")
        for name, n in sorted(capped, key=lambda kv: -kv[1])[:8]:
            print(f"    {n:>4} refs  {name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
