# Parametric halo selection — native qualification candidate

`selection=all` returns the exact canonical-ledger Racket bytes retained in
`canonical.rkt`. `largest` and `smallest` first form the clipped union of all
radius-one blue halos, then recompute four-connected blue components and keep
**every** component tied for the selected extreme area. The output keeps its
input dimensions. This separate family extends the input grammar to isolated
gray seeds on 7..30 by 7..30 black canvases; the canonical production generator,
its 7..15 size distribution, authority, and approval are untouched.

## Native contract and useful evidence

`adapter.py` implements `program(settings)` and
`generate(seed, settings, demos=3, queries=4)`. Counts are independent: 2..6 demos,
1..4 queries, default 3/4. Seeds are exact integers in 0..2**63-1. Unsupported
settings, booleans, out-of-range counts and malformed inputs fail explicitly.
A hidden setting is fixed for the whole episode. Matched seeds/counts yield the
same inputs for all three settings, using independent per-split/per-index RNG
streams. Queries are novel and pairwise distinct. Sampling uses at most sixteen
attempts per pair and raises instead of silently shortening a request.

Two constructive demonstrations distinguish the settings and the declared
shortcuts. The first has component areas 24,24,25: the two irregular 24-cell
regions touch only diagonally and have bbox areas 30, whereas the 25-cell square
has bbox area 25. All three have 21 newly painted cells, rejecting that ranking
shortcut too. The second has areas 8,8,9,16,24,24 and combines clipped/overlapping
tied winners with seed-count reversals. Their orientation, placement and canvas
sizes vary. A normal third demo is a 9x9 source-scale anchor with 3 or 4 seeds.

Four queries cover small transfer, rectangles, larger interactions, and a dense
30x30 scene with 55..75 isolated seeds. The first query must contain competing
component sizes, preserving an informative single-query evaluation. Later
queries may legitimately have ties or a single merged region. This is not a
measured model-difficulty or learning-benefit claim.

## Reproduce from the outer packet directory

Use a **new** output path when rerunning the audit:

```bash
WORK/.venv/bin/python review.py run python3 -m pytest -q generators/f7c20cfd443f/tests/test_parametric.py
WORK/.venv/bin/python review.py run python3 generators/f7c20cfd443f/workspace/parametric/audit_family.py --out ../checks/f7c20cfd443f/fresh-audit
WORK/.venv/bin/python review.py run python3 -m arcpuzzles parametric qualify f7c20cfd443f --seed 0 --seed 17 --demos 3 --queries 4 --out ../checks/f7c20cfd443f/fresh-qualification --summary
```

`audit_family.py` is the reusable task-local tool. It checks bounded generation,
matched inputs, first-turn parity, finite demo-only rival elimination and dense
stress, then executes every retained label and rival through protected Racket.
It fails if a rival survives, a Python claim differs from Racket, or output
already exists. The current evidence is `evidence/bound/audit.json`; native
qualification and its sibling execution record are under the packet's
`WORK/checks/f7c20cfd443f/qualification/`. The native source inventory is
`evidence/manifest.json`. Evidence covers sampled seeds and finite rivals only.

## Public/private separation

`public_turn(episode, index)` exposes only demonstrations and one query input.
Its first turn equals the corresponding one-query request, including its public
bytes and identifier. The writer uses existing `reviewer_support` public-byte
helpers and names each public JSON by the SHA-256 of exactly those bytes.
Settings, seed, programs, query answers, query ordering and later inputs stay in
`examples/private.json`. A consumer reveals one chosen public file at a time;
this package does not implement a turn controller. Do not hand the private
manifest or all future-query files to the model. The regression mutates hidden
metadata and future inputs and confirms that the current public turn is stable.

## Sequential dependency and status

A is clipped dilation and recomputation of four-connected regions; its
input-dependent intermediate contains newly merged regions and their areas.
B chooses the extreme-area regions. Selecting the original input objects first
instead sees only tied singletons, and produces a different final grid. The
source-bound protected-Racket witness is in `checks/f7c20cfd443f/causal/` in WORK.

This is a **reviewer-ready, proposed** family. Native qualification is evidence;
only the owner's integration, qualification and fresh exact-source acceptance
make it accepted. Training admission remains false. Canonical production tests
and broader batteries are outside this prototype-only change.
