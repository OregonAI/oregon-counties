# MCP server for the oregon-counties corpus (HTTP transport).
#
#   docker build -t oregon-counties-mcp .
#   docker run -p 8000:8000 oregon-counties-mcp
#
# The corpus is baked in at build time; rebuild the image to pick up new commits. Mounting it
# instead was tried on executive-regulatory-frameworks and reverted the same day — it never
# shrank the image, and it made the FTS index shared mutable state between the deployer and
# the live container. See platform-deploy's README before repeating it.
#
# BUILD FROM A SHALLOW CLONE, not your working tree. `.git` cannot be excluded — it is a
# RUNTIME dependency, because the FTS cache key is `git rev-parse HEAD` plus a hash of
# `git status --porcelain`, and corpus_overview() shells out to `git log -1`. Without it
# repo_state() collapses to a constant and content changes are never picked up, silently.
#
#   git clone --depth 1 --branch main https://github.com/OregonAI/oregon-counties build/
#   docker build -t oregon-counties-mcp build/
FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends git && \
    rm -rf /var/lib/apt/lists/*
WORKDIR /repo
# Deps BEFORE content, so a content-only change does not re-run pip.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
# Pre-build the FTS index so the first request is instant.
#
# 3,335 documents — between oregon-audits (242, seconds) and ERF (75,829, ~8 minutes), so
# this costs real build time but nothing like ERF's. The step earns its place for the other
# reason anyway: it fails the BUILD if content is missing, rather than shipping an image that
# starts fine, reports healthy, and answers nothing.
RUN python3 -c "\
from corpus_toolkit import config as config_mod; \
from corpus_toolkit.mcp.framework import CorpusFramework; \
CorpusFramework(config_mod.load('_meta/corpus.yml')).ensure_index()"

# WARM THE SIBLING INDEX INTO THE IMAGE. This corpus resolves ORS and OAR citations into
# executive-regulatory-frameworks over the network, and 8,726 of its 9,217 ORS citations
# depend on that index being reachable. `corpus_toolkit.remote` prefers a stale cache over
# nothing, so a container that has NEVER fetched it is the one state with no fallback: the
# first resolve_citation after a cold start either blocks on an 8 MB download or, if the
# fetch fails, reports every citation unresolved — which reads exactly like a corpus with no
# citation edges at all.
#
# Baking a copy means a cold container degrades to "a few hours stale" instead of "empty".
# It refreshes on its own TTL at runtime, so this is a floor, not a pin.
#
# Deliberately NOT fatal: a build should not fail because GitHub Pages had a bad minute, and
# the runtime path already handles an absent cache. The message is what makes it visible.
# Warmed through the FRAMEWORK's own resolve_citation rather than by calling
# load_sibling_index directly. Two reasons, and the second is the one that matters: the
# helper takes a cache_dir, not a config, so a hand-rolled call is easy to get subtly wrong
# — and because this step is deliberately non-fatal, a wrong call would fail into the `||`
# and report a warning that looks like an upstream blip. Going through the framework uses
# the same cache path the server will read at runtime, by construction.
RUN python3 -c "\
from corpus_toolkit import config as config_mod; \
from corpus_toolkit.mcp.framework import CorpusFramework; \
fw = CorpusFramework(config_mod.load('_meta/corpus.yml')); \
r = fw.resolve_citation('ORS 215.203'); \
assert not r.get('unresolved'), r.get('note'); \
print('sibling index warmed:', r['matches'][0]['id'])" \
    || echo "WARNING: sibling index not warmed; cold-start citation resolution will fetch on first use"
EXPOSE 8000

# --path and --public-hostname both matter behind the tunnel and are easy to omit:
#   * A Cloudflare Tunnel matches on path but does NOT strip it. Routing /oregon-counties
#     here forwards the whole path, so the server must mount at that same prefix or every
#     request 404s with nothing in any log explaining why.
#   * Without --public-hostname the SDK's DNS-rebinding guard rejects the forwarded Host
#     header with 421 Invalid Host header.
# Override either at `docker run` for a different hostname or a dedicated-host deployment
# (in which case pass --path /mcp).
CMD ["corpus-mcp-serve", "--config", "_meta/corpus.yml", "--http", \
     "--host", "0.0.0.0", "--port", "8000", \
     "--path", "/oregon-counties/mcp", \
     "--public-hostname", "oregonai.morficflux.com"]
