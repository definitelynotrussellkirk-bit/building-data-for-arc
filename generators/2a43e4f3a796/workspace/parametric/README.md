# Stable gravity in four directions

This separate native adapter proposes four episode-fixed settings for
`2a43e4f3a796`: `gravity = down | up | left | right`. The production generator
v3.1.0 and selected Racket authority are unchanged. Downward gravity returns
the canonical program byte-for-byte; the other settings change the packing
axis or destination edge while retaining stable order and multiplicity.

## Rule and causal dependency

For each column (up/down) or row (left/right), first collect the nonzero values
in their original top-to-bottom or left-to-right order. Let the resulting
sequence have length m in a line of length L. Then place that exact sequence
against the selected edge and fill the other L−m cells with zero. Down/right
placement starts at L−m; up/left placement starts at zero and ends at m−1.

The sequence and its length are input-dependent intermediates consumed by
placement. Changing the length changes occupied coordinates; changing the
sequence changes the ordered output values. Gray 5 is ordinary moving foreground,
and zero stays background even when a nonzero color is more frequent.
The native causal witness changes the count used in the canonical placement
start while preserving the surrounding Racket program.

`gravity.py` owns the single sampler, Python label claim and instantiated Racket
programs. `adapter.py` loads that adjacent file by exact path and implements the
native `program(settings)` and `generate(seed, settings, demos, queries)` APIs.
The native worker independently executes each label claim. `canonical.rkt` is
a declared source-bound resource, not a replacement authority.

## Grammar, counts and teaching

The rule is total on rectangular 1–30 grids with exact integer colors 0–9. Blank,
solid, singleton, already-settled, one-row and one-column inputs remain lawful.
The separate sampler extends the unchanged production sampler's size range,
using the canonical validator's existing full ARC domain.

Native requests accept exact integer seeds 0..2**63−1, two through six demos,
and one through four queries. Ordinary counts remain three demos/four queries.
All ten candidate inputs are constructed from independent per-profile RNGs
before slicing either prefix. Count changes therefore preserve retained inputs;
all profile shapes differ, making every demo/query input novel within its
lesson without retries or fallback duplicates. Inputs match across settings.

The two required demonstrations are a dense 9×11 scene with a nonzero mode and
a sparse 13×15 scene with zero as the mode. Each contains a long, gapped row and
column crossing at their shared zero. Both line ends are occupied; a repeated
color sequence begins a,b,a, and gray 5 appears on both sides of the gap. The
construction exposes stable order, repeated values, gray mobility, line
independence and more-than-five-cell capacity under every gravity direction.
The second scene also rejects a conditional five-cell cap used only when zero
is modal. Optional later demos add random densities, sizes and blank lines.

| Query profile | Purpose |
| --- | --- |
| 30×30, dense random foreground | Maximum dimensions with varied colors, gaps and four boundary contacts |
| 19×27, sparse random foreground | Rectangular geometry and long movement distances |
| 1×30 | Minimum height, horizontal packing and vertical identity |
| 30×1 | Minimum width, vertical packing and horizontal identity |

These are meaningful full-grid inputs, not empty padding around a small
repeated scene. Additional protected-Racket audit fixtures exercise blank,
full and one-cell endpoints. The audit checks finite plausible rival rules
against only the two visible demos; a rival execution error is a failed audit,
never a successful refutation. This does not prove universal identifiability.

## Public export

The reusable `exporter.py` accepts a labeled episode in the form
`{'pairs': {'train': [...], 'test': [...]}, ...private metadata...}`.
It uses the shared `reviewer_support.public_challenge_bytes` and
`public_challenge_id` helpers from this checkout. Only exact visible bytes
influence a public path. The protected-Racket audit exports labeled examples.

| Path | Consumer and contents |
| --- | --- |
| `turns/<visible-sha>.json` | Solver: demonstrations and one current query input |
| `public_archive/<visible-sha>.json` | Controller: demonstrations and all retained query inputs |
| `private/<private-sha>.json` | Reviewer/controller: settings, answers, program and provenance |

Each turn contains no index, total count, future query, setting, program or
query answer. Its first-turn bytes are identical for one-query and four-query
requests at the same seed, setting and demo count. Give the solver exactly one
selected turn file, without directory listings or controller/private material.
The existing consumer manages reveal; no new controller or training loop is
introduced. The exporter validates projection and files, not label correctness.

## Reproduce from the outer packet directory

```bash
WORK/.venv/bin/python review.py run python3 -m pytest -q generators/2a43e4f3a796/tests
WORK/.venv/bin/python review.py run python3 generators/2a43e4f3a796/workspace/parametric/audit.py --out ../checks/2a43e4f3a796/self-audit-replay
WORK/.venv/bin/python review.py run python3 -m arcpuzzles parametric qualify 2a43e4f3a796 --seed 0 --seed 17 --demos 3 --queries 4 --out ../checks/2a43e4f3a796/qualification-replay --summary
```

Use a new output directory. The return summary and source-bound inventory
record actual results and finite limits. After integration the owner must run
native qualification and fresh acceptance on the exact live bytes. Reviewer
qualification alone is not accepted status or training admission. Historical
production battery heuristics and audit dispositions are outside this proposal.
