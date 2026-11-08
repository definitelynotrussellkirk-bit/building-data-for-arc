# Synchronous rectangle completion

This candidate extends `d89b3f447c00` with episode-fixed `completion_rounds=1|2`.
Production version 3.1.0 and its selected canonical rule remain unchanged.
At one round, `program()` returns the exact 743-byte selected source in
`canonical.rkt`. At two rounds, the same body is applied to its own output.
Native qualification is reviewer evidence; owner acceptance of integrated source
and downstream training admission remain separate.

## Rule and genuine intermediate

For each nonzero color, find all axis-aligned rectangles with exactly three
same-color corners. Add the missing corner in that color and preserve other
cells. Every decision in a round uses that round's **frozen input**. Newly added
corners become eligible clues only in the next round.

| Private setting | Executed behavior |
| --- | --- |
| `{"completion_rounds": 1}` | One exact canonical synchronous completion. |
| `{"completion_rounds": 2}` | Complete once, then repeat using the updated grid. |

A is the first completion. Its input-dependent intermediate is the updated grid.
B searches that grid for newly induced three-corner rectangles. Skipping A means
B sees only the original clues and returns the one-round answer. The protected
causal witness retains both complete programs and their different final outputs.

A small three-row chain has 5 original cells, 8 after one round and 9 after two.
A six-row chain is a stronger teaching case: 11 original cells become 20 after
one round, 35 after two, and 36 at the fixed point. Thus two rounds are distinct
from both one round and completing to closure. Gapped and permuted coordinates
preserve the rectangle rule while breaking filled-bounding-box shortcuts.

## Constructive sampling and supported requests

- Exact integer seed `0..2**63-1`; booleans and scalar coercions are rejected.
- Exactly one setting key, `completion_rounds`, with integer value 1 or 2.
- **2–6 demonstrations**, independently of **1–4 queries**; defaults are 3 and 4.
- Exact-integer rectangular grids, dimensions 1..30, colors 0..9; background is 0.
- Distinct colors occupy disjoint rectangular regions, so completion targets
  cannot overwrite another color. Multiple induced rectangles per color are
  intentional and extend the narrower production sampler.

Each chain begins with points `(i,i)` and `(i,i+1)`. Rows and columns are embedded
independently into shuffled coordinate sets. Some motifs also have isolated
same-color marks on disjoint row and column sets. Those marks must be preserved
without joining the chain. A tight three-corner L teaches minimal rectangles;
a completed square plus isolated mark teaches preservation and no-op behavior.
All eight whole-grid dihedral symmetries are supported and checked.

The minimum two-demo prefix contains:

1. An 18×18 four-color example with a long chain plus island, a shorter chain,
   a minimal L, and an already completed square plus island. Three colors change.
2. An 8×10 one-color six-row chain, possibly transposed by the sampled symmetry.
   This teaches both the single-color and compact-canvas cases while still
   distinguishing two rounds from full closure.

Additional demonstrations add up to nine colors and larger canvases. Query
profiles are independently permuted by seed:

| Shape before optional symmetry | Content |
| --- | --- |
| 8×10 | One six-row chain plus a same-color island. |
| 20×24 | Four color regions with different chain lengths and a no-op motif. |
| 30×30 | Four long chains, including disconnected same-color islands. |
| 26×28 | Six color regions with varied chain lengths and a no-op motif. |

The large query has 64 original foreground cells and 232 after two rounds, with
content touching all four canvas boundaries. More than 80 changes occur in the
second round alone. It exercises cascades across the canvas rather than padding
a small example. Finite graph motifs and disjoint color regions bound the domain;
cross-color collisions and arbitrary interacting colored regions are not claimed.

The same seed gives matched input grids under both settings. Separate local RNG
streams preserve demo/query prefixes when counts change and leave global random
state untouched. The compact demo has 11 original marks and its related query 12,
so they cannot be duplicate inputs even when their dimensions and color match.

## Self-review and evidence

`rivals.py` independently implements a three-edge-path completion predicate in
Python and Racket, rather than importing the sampler's rectangle enumerator.
`audit.py` checks the 80 combinations of seeds 0–7, demo counts 2–6 and both
settings, with four queries. Its protected seed-0/17 pass checks all three default
demo labels and four query labels, but fits rivals using only the first **two**
demonstrations, so the advertised minimum is actually exercised.

The finite bank covers other round counts, fixed-point closure, global row×column
completion, geometric bounding boxes, per-color/count/size restrictions,
single-cell completion, output-only-new-cells, directional in-place scans, and
board-level color/canvas gates. Rival programs must agree with their independent
Python descriptions. Query disagreements count as teaching failures only after
the rival fits every visible demonstration.

Fresh review found a genuine initial hole: all demonstrations were multi-color,
so a rule that does nothing on single-color inputs fit them and failed a query.
The original two-setting case was confirmed with 12 protected Racket executions.
The compact single-color second demonstration fixes this without increasing the
minimum count. Its behavioral regression was observed failing before repair and
passing afterwards. The earlier source-bound case is retained in the return.

Finite rival elimination is not a uniqueness proof against arbitrary programs.
The small receipts in `evidence/current/` and the native manifest bind the
source-current checks; full command/results evidence is under
`checks/d89b3f447c00/` in the return.

## Reproduction and native public preview

From the outer packet folder, use the passing packet interpreter. Payloads run
in `WORK/repo`; `../checks` resolves to `WORK/checks`. Use fresh output paths.

```bash
WORK/.venv/bin/python review.py task-tests d89b3f447c00 \
  --phase after --out ../checks/d89b3f447c00/tests-replay
WORK/.venv/bin/python review.py run python3 \
  generators/d89b3f447c00/workspace/parametric/audit.py \
  --out ../checks/d89b3f447c00/self-review-replay.json
WORK/.venv/bin/python review.py run python3 -m arcpuzzles parametric qualify \
  d89b3f447c00 --seed 0 --seed 17 --demos 3 --queries 4 \
  --out ../checks/d89b3f447c00/qualification-replay --summary
```

After source edits, refresh the native source/evidence manifest before qualifying.
The default canonical source, adapter, executable helpers, tests and evidence
must match their inventory. Qualification executes labels through protected
Racket. Owner acceptance is a later operation on integrated bytes.

This packet already provides the reusable projection tool requested in the
previous round, so no separate exporter was copied into this task:

```bash
WORK/.venv/bin/python review.py preview-public export \
  --qualification ../checks/d89b3f447c00/qualification/qualification.json \
  --out ../checks/d89b3f447c00/sequential-public-replay
WORK/.venv/bin/python review.py preview-public verify \
  --bundle ../checks/d89b3f447c00/sequential-public-replay
```

Each public file contains the visible demonstrations and one masked query. Give
the model only the chosen file for that turn. The directory listing, future
query files, original order, answers, settings, and programs stay with the
controller. The first view can be used as a standalone one-query evaluation
without any public total-count hint. No turn controller or training loop is added.

The native helper checks current source/receipt bindings, exact public-byte IDs,
strict grids, duplicate views, staged publication, file inventory and tampering.
Its existing focused 33-test suite was reused rather than duplicated. Saved-file
verification does not rerun Racket, authenticate forged receipts, accept source,
or grant training admission.
