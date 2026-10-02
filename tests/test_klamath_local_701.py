"""OregonAI/oregon-counties#120: Local 701 CBA 2023-2026 source returns 404.

Klamath's DocumentCenter id 35590 for `Local-701---Collective-Bargaining-Agreement-2023-2026`
404s. The county's own Policies & Union Contracts listing (/279/Policies-Union-Contracts-
Compensation-Ta, confirmed 2026-10-01) no longer carries that 2023-2026 term at all; it now
lists a successor, `701-CBA-2026-2029` (DocumentCenter id 63817), confirmed `application/pdf`.

This is the successor case, not a relocation: the term the old document covered has ended and
a new agreement covers 2026-2029. Per the issue, a successor is a NEW document recording
`supersedes`; the old one stays, `status: superseded`. Nothing is deleted.

This test is the mechanical half of that: the new source is in the manifest with the fetched
baseline, the new document exists and names the old one in `relationships.supersedes`, and the
old document survives with `status: superseded` and an unchanged baseline (it was never
re-fetched -- the county stopped publishing it, it did not change).
"""
from __future__ import annotations

import pathlib

import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
SOURCES = ROOT / "_meta" / "sources"
DOCS = ROOT / "counties" / "klamath-county" / "policies"

OLD_ID = "klamath-policies-local-701-collective-bargaining-agreement-2023-2026"
NEW_ID = "klamath-policies-701-cba-2026-2029"
NEW_URL = "https://www.klamathcounty.org/DocumentCenter/View/63817/701-CBA-2026-2029"
OLD_MANIFEST_SHA256 = "e80d6c7b055b117b8fffef45c2c4b41850839d2d455b94fc3517e33ef053ce7d"
OLD_DOC_SHA256 = "d33564c194e72374be44de157efb1abe2e6ef061c1e5c2d9bb4c50508609dcd8"


def _frontmatter(doc_id: str) -> dict:
    text = (DOCS / f"{doc_id}.md").read_text(encoding="utf-8")
    assert text.startswith("---\n"), doc_id
    end = text.index("\n---", 4)
    return yaml.safe_load(text[4:end])


def _manifest() -> dict:
    return yaml.safe_load((SOURCES / "klamath.yml").read_text(encoding="utf-8"))


def _manifest_source(doc_id: str) -> dict:
    for src in _manifest()["sources"]:
        if src["id"] == doc_id:
            return src
    raise AssertionError(f"{doc_id} not in _meta/sources/klamath.yml")


def test_successor_source_is_in_the_manifest_with_a_real_baseline() -> None:
    src = _manifest_source(NEW_ID)
    assert src["url"] == NEW_URL
    assert src["format"] == "pdf"
    assert len(src["sha256"]) == 64


def test_old_source_entry_still_present_url_untouched() -> None:
    # The old id's manifest entry is not deleted and its recorded URL is not silently
    # rewritten over a dead link -- it 404s, and that fact belongs to the old baseline, not
    # to a URL now edited to something else.
    src = _manifest_source(OLD_ID)
    assert "35590" in src["url"]
    assert src["sha256"] == OLD_MANIFEST_SHA256


def test_new_document_exists_and_supersedes_the_old_one() -> None:
    fm = _frontmatter(NEW_ID)
    assert fm["source_url"] == NEW_URL
    assert fm["status"] == "current"
    assert OLD_ID in fm["relationships"]["supersedes"]


def test_old_document_marked_superseded_not_deleted() -> None:
    fm = _frontmatter(OLD_ID)
    assert fm["status"] == "superseded"
    # Content is untouched -- the county stopped publishing it, the text did not change.
    assert fm["source_sha256"] == OLD_DOC_SHA256
