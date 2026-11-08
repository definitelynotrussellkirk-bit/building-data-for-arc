# Global mode / modal-row mode

This native parametric candidate keeps the original ARC `5582e5ca` frequency-fill
rule and adds a spatially restricted frequency comparison. The canonical
production generator and its selected Racket source are unchanged.

| Episode-fixed `scope` | Exact behavior |
| --- | --- |
| `global` (default) | Fill with the unique most frequent nonzero color, using the byte-exact canonical Racket program. |
| `modal_row` | Find that global color; select the unique row containing it most often; remove zero and that global color from the selected row; fill with the unique most frequent remaining color. |

The second rule needs the selected row before choosing the answer. A spatial
redistribution can preserve every global color count while changing the selected
row and output. This is an input-derived region selection, not an iterative
physical simulation. The focused tests contain a literal histogram-preserving
row-switch example, and the return includes a protected Racket wrong-row witness.

## Grammar and teaching

The separate parametric sampler supports rectangular inputs from 3 through 30
cells on each side. The exact canonical expression is valid over this larger
grammar; the reviewed production sampler retains its 3..5 limits. Both settings
use identical input streams for the same seed and counts. All inputs have at
least three nonzero colors, a unique global nonzero mode, a unique selected row,
and a nonempty selected-row remainder with a unique mode. Ties are excluded
rather than teaching a hidden tie-breaking convention.

Requests support 2..6 demonstrations and, independently, 1..4 queries. The normal
request is 3 demonstrations and 4 queries. Two demonstrations are selected from
a bounded constructive pool using **demonstration predictions only**, to reject
every declared wrong rival under both settings. Extra demonstrations supply
additional scales and colors. The 22 named candidates include both settings,
global runner-up, overall mode including zero, fixed first/last rows, richest
column, zero/mode inclusion mistakes, rarest/minimum/maximum/first colors, and
nine constant colors. This finite check does not prove universal identifiability.

Four query inputs are independent of the rule setting and requested counts:
3x3, 8x13, a 21..29-by-21..29 rectangle, and 30x30. Large grids contain distributed
color comparisons throughout the canvas. Rows, palettes, densities, zero
decoys, selected-row position and local/global frequency relationships vary.
No query is cloned from a demonstration or another query. A bounded sampler
failure raises an explicit error; no shortened episode is returned.

## Run and inspect

From the packet's outer directory, use its passing Python interpreter:

```sh
WORK/.venv/bin/python review.py run python3 -m pytest \
  generators/8b0844e3951e/tests/test_parametric_modal_row.py -q

WORK/.venv/bin/python review.py run python3 \
  generators/8b0844e3951e/workspace/parametric/audit.py \
  --out ../checks/8b0844e3951e/new-audit
```

The rerunnable audit refuses existing destinations. It separates Python finite
rival screening from protected Racket execution, executes both setting programs
and six independent shortcut programs, checks request endpoints, and writes
small source-bound reports plus two complete four-query example episodes.
`public/` contains exact visible-byte SHA256 filenames; settings, programs,
intermediates and query labels are confined to `private/`.

The public four-query files are **controller containers**, not prompts. The
existing downstream consumer must reveal one input after each answer. Initial
content is the demonstrations plus the first query only, and is byte-identical
for one-query and four-query requests. The audit checks that projection using
`reviewer_support.public_challenge_bytes`, including private/future-field
mutation invariance. It does not implement or validate a downstream controller.

## Native handoff

`adapter.py` loads the adjacent `prototype.py`; `promotion.json` declares the two
settings and independent count limits. `evidence/manifest.json` is built by the
native inventory helper and binds the actual source and focused evidence.

```sh
WORK/.venv/bin/python review.py run python3 -m arcpuzzles parametric qualify \
  8b0844e3951e --seed 0 --seed 17 --demos 3 --queries 4 \
  --out ../checks/8b0844e3951e/qualification --summary
```

The returned native qualification and execution receipts, compact audit, and
causal witness are linked in `WORK/RESULTS.json`. Qualification executes both
settings on the demonstrations before checking the chosen setting's four query
labels. The owner must integrate the exact source, qualify it again, and run
native acceptance. Reviewer readiness does not grant acceptance or training
admission. The current evidence measures bounded correctness and teachability,
not model learning benefit.
