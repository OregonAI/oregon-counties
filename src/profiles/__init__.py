"""One profile module per county, auto-discovered.

WHY ONE FILE PER COUNTY rather than a single COUNTY_PROFILES dict (the shape
oregon-policy-repo used for 10 agencies):

  - 36 counties on a dozen unrelated platforms is a different order of magnitude than 10
    agencies on six. A single dict becomes a thousand-line file that every county edit
    touches, and every merge conflicts on.
  - Counties are built CONCURRENTLY, one worker per county. Separate modules mean no shared
    file and therefore no serialization point in the build.
  - Adding county #8 is a new file, not an edit to a growing central registry. Nothing that
    already works gets touched to add something new.

Each module defines a module-level `PROFILE` dict:

    PROFILE = {
      "slug": "deschutes",              # matches _meta/counties.yml minus the -county suffix
      "discovery": "mco-s3",            # a key in ingest_counties.DISCOVERY
      "site": "https://www.deschutescounty.gov",
      "crawl": {                        # the robots determination, recorded per county
          "robots_url": "...", "decision": "proceed" | "excluded",
          "basis": "...", "checked": "YYYY-MM-DD",
      },
      "families": {                     # any subset of code/orders/policies/land-use
          "code": {...},                # discovery-mode-specific keys
      },
    }

and may define `discover(profile, family, cfg) -> list[dict]` to override the generic
discovery mode entirely, for a county whose site fits nothing.
"""
from __future__ import annotations

import importlib
import pkgutil


def load_profiles() -> dict[str, dict]:
    """Import every sibling module and collect its PROFILE, keyed by slug.

    A module without a PROFILE is a hard error rather than a skip: a county file that exists
    but exports nothing is a half-finished profile, and silently ignoring it would report
    that county as unbuilt while its file sits in the tree looking done.
    """
    out: dict[str, dict] = {}
    for mod in pkgutil.iter_modules(__path__):
        if mod.name.startswith("_"):
            continue
        module = importlib.import_module(f"{__name__}.{mod.name}")
        profile = getattr(module, "PROFILE", None)
        if profile is None:
            raise ImportError(f"src/profiles/{mod.name}.py defines no PROFILE")
        slug = profile.get("slug")
        if slug != mod.name.replace("_", "-"):
            raise ValueError(f"src/profiles/{mod.name}.py: PROFILE['slug']={slug!r} "
                             f"does not match its filename")
        profile["_module"] = module
        out[slug] = profile
    return out
