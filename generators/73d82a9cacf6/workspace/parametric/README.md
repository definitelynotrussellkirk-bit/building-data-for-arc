# Hole-count packing: native area-order prototype

This opt-in family preserves the canonical object extraction, enclosed-hole
counting, crop preservation and horizontal packing. Its one episode-fixed
parameter changes which painted area comes first inside an equal-hole group.

| Parameter | Allowed values | Canonical default |
| --- | --- | --- |
| `area_order` | `larger_first`, `smaller_first` | `larger_first` |

`program({"area_order": "larger_first"})` returns the exact selected canonical
Racket source, including its color fallback. The alternative changes only the
signed painted-area sort key. The original `generator.py` and selected rule
authority are unchanged. This separate prototype does not close the retained
canonical-sampler query-rotation finding.

## Runnable four-query check

From the packet outer directory, with the supplied runtime configured:

```sh
WORK/.venv/bin/python review.py run python3 \
  generators/73d82a9cacf6/workspace/parametric/audit.py \
  --out ../checks/73d82a9cacf6/audit-new
```

Use a fresh output directory. This command creates complete private episodes
for both settings, two seeds, 2 or 6 demonstrations, and four distinct queries
per episode. It executes the chosen programs and fourteen declared rivals in
protected Racket, checks demonstration-only identification and cached two-demo
rotations, and publishes masked challenges and individual query turns only
after all required checks pass. An optional 12-seed sampler census is explicitly
Python-only; it does not add protected-label evidence.

Native qualification is a separate command, centered on three demonstrations:

```sh
WORK/.venv/bin/python review.py run python3 -m arcpuzzles parametric qualify \
  73d82a9cacf6 --seed 0 --seed 17 --demos 3 --queries 4 \
  --out ../checks/73d82a9cacf6/qualification-new --summary
```

Qualification requires the current task-local `evidence/manifest.json` built
with the native manifest helper. After changing source or inventory evidence,
rebuild the inventory and use fresh qualification and witness outputs.

## Sampling and supported grammar

`generate(seed, settings, demos, queries)` accepts exact integer seeds in
0..2^63-1, 2..6 demonstrations and 1..4 queries. Booleans, fractional counts,
unknown settings and out-of-range requests fail closed. Inputs depend only on
seed and role, so both settings and all supported count prefixes share inputs.
Every output in `generate` is a Python claim until independently replayed.

The extended grammar admits 3..6 monochromatic, 4-connected objects with
distinct colors on a black 1..30 by 1..30 grid. Objects cannot touch even
diagonally, their bounding boxes must be disjoint, and packed crop widths plus
one black column between crops must fit width 30. Bounding-box disjointness
prevents one object's crop from including another object's pixels. The generic
source helpers are reused; the original small-canvas validator is not relabeled
as supporting this extension.

Every demonstration combines five objects with hole counts 0, 1, 1, 2, 2 and
unequal painted areas inside the tied groups. Large thin frames oppose area to
bounding-box area and perimeter; larger, less dense two-hole objects oppose
area to density. Diagonally meeting pockets distinguish 4-connected from
8-connected background regions. Within-group position and color orders are
mixed so neither shortcut explains either area setting. Alternating solid and
open-U zero-hole objects distinguish enclosed holes from empty crop cells.

The query canvases are 10x16, 22x26, 26x28 and 30x30. They are distinct from all
six demonstration canvases. The final query contains six objects, 242 painted
cells and hole counts 0, 1, 1, 2, 2, 3; its output is 13x30. It extends object
count and geometry, rather than only adding an empty border.

## Public projection and causal dependency

`public_turn(episode, query_index)` returns exact JSON bytes containing the
fixed demonstration pairs and only the selected query input. Private settings,
reference programs, query answers, other query inputs, total counts and turn
ordinals are absent. The first-turn bytes are identical for one-query and
four-query requests. Public filenames are hashes of visible bytes. A caller
reveals these turns using the existing consumer; this prototype adds no turn
controller or training loop.

Step A identifies each object and counts its enclosed 4-connected complement
regions. The input-dependent intermediate is the per-object hole-count table.
Step B uses that table as its primary sort key, applies the episode's area tie
break, and assigns each crop a left offset from preceding crop widths. Those
offsets cannot be selected before object ordering is known. The native causal
witness replaces the computed hole-count key with zero while preserving area,
color, crops and packing, then executes both programs to show changed output.
Its intermediate interpretation is reviewer-authored; native replay verifies
the programs and final labels.

## Retained evidence and limits

Current verification is in `checks/73d82a9cacf6/teaching-release/`,
`task-tests-release/`, `qualification/` and `causal/`, relative to `WORK/`.
Earlier `teaching-v001/` and `teaching-final/` are explicitly superseded bounded
audits: the former found a scan-order rotation gap, and independent review then
found the density rival missing from the latter's thirteen-rival set. Their
findings and red/green regressions are retained, rather than recast as current
evidence. Negative verifier probes in `audit-dev/negative-verifier-v001.json`
bind that earlier audit version; its failure/publication code was unchanged.

The fourteen declared rivals cover wrong area direction, ignored holes, blank
counts, bounding-box area, density, perimeter, descending holes, scan/color
ordering with or without hole groups, 8-connected background, missing gaps and
bottom alignment. Passing these finite checks is not uniqueness over arbitrary
programs or untested seeds. Reviewer qualification and a replayed causal witness
prepare an exact-source owner handoff; they do not grant owner acceptance or
training admission.
