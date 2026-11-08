# Count, then replicate — native adapter proposal

This task-local family extends the existing prototype for `7fc158ab7b70`
(original ARC task `ac0a08a4`). The production generator and canonical authority
are unchanged. Native qualification is reviewer evidence; owner qualification
and fresh acceptance of integrated bytes remain required. No training admission
or allocation change is implied.

## Six episode-fixed rules

| Parameter | Values | Meaning | Canonical default |
| --- | --- | --- | --- |
| `count_basis` | `cells`, `colors` | Count nonzero cells or distinct nonzero colors | `cells` |
| `scale_axes` | `both`, `rows`, `columns` | Replicate each cell in both dimensions, rows only, or columns only | `both` |

Step A computes an input-dependent integer from the complete input. Step B uses
that integer as the replication factor along the selected axes, including for
zero cells. The factor determines both output shape and every source-coordinate
lookup. Substituting a wrong count changes the result on repeated-color inputs.
The causal witness retained with qualification executes that intervention.

The native `adapter.py` loads the adjacent `scaling.py` by exact path and reuses
its sampler and mirror. The independent native worker executes the Racket
program on every claimed label. `program(default)` returns `canonical.rkt`
byte-for-byte; other settings use the existing parameterized Racket expression.
The canonical copy is a declared resource and is checked against the selected
reference, not installed as a new authority.

## Input grammar and teaching

All six settings share the same square 3–5 input grammar: 2–6 nonzero cells,
integer colors 0–9, and input side times cell count at most 30. A monochrome
input contains exactly two spatially separated cells. The sampler retains the
canonical grammar and supplies matched inputs across settings.

Requests independently support **2–6 demonstrations and 1–4 queries**, with
defaults of three and four. Native seeds are exact integers in `0..2**63-1`;
the standalone prototype also retains its historical negative-seed support.
Invalid counts and types fail explicitly. Sampling has a finite retry bound
and never substitutes duplicates or returns a short episode.

The first two demonstrations are constructive contrasts, randomized by colors
and square symmetries:

1. Two separated occurrences of one color in the middle row of a 3×3 grid.
   This distinguishes counting cells from colors and leaves an empty border.
2. A same-color L triomino and an isolated other color on a 4×4 grid.
   Counts are four cells, two colors, two components, largest component area
   three, and three occupied rows/columns. Together with the first example,
   these contrasts reject component and component-size shortcuts.

The optional third demonstration has three cells of three different colors.
The remaining demonstrations add sizes and repeat patterns without changing
any earlier demonstration. Query construction uses a separate prefix after six
candidate demos; changing either requested count leaves retained inputs unchanged.
All demonstrated and queried inputs are distinct within an episode.

The first query has six different colors on a 5×5 grid, occupying all four
corners and two interior cells. It reaches **30×30** for both counting bases
when scaling both axes, **30×5** for rows and **5×30** for columns. The remaining
queries cover a denser 3×3 input, repeated colors on a 4×4 input, and a separated
monochrome pair on a 5×5 input. Large input grids are outside the retained
grammar; the output-size stress uses actual distributed content.

`identify_demonstrations` accepts demonstrations only. Native qualification
requires the chosen setting to be the sole surviving declared program. The
additional `audit.py` tests a finite set of plausible shortcuts through protected
Racket, using only the two-demo prefix to fit them. Runtime errors fail the audit;
they never count as rival refutations. This evidence does not prove uniqueness
against every possible rule or cover every seed.

## Public export and one-query turns

The old writer placed public files in setting-named directories. The corrected
writer calls the reusable `exporter.export_episode(out, episode)` in one common
output directory. Public identifiers hash exactly the canonical serialized
bytes from the same checkout's `reviewer_support` helpers.

| Path | Contents | Consumer |
| --- | --- | --- |
| `turns/<visible-sha256>.json` | Demonstrations and exactly one query input | Solver, one file per turn |
| `public_archive/<visible-sha256>.json` | Demonstrations and all retained query inputs | Controller only |
| `private/<private-sha256>.json` | Full episode, answers, settings, exact program and export map | Controller/reviewer only |
| `manifest.json` | Suite counts, settings, source hashes and execution receipts | Controller/reviewer only |

A turn has only `train` and `test`, with exactly one input-only test pair. It
contains no query index, total count, future input, setting, program, or answer.
The first turn of a four-query request is byte-identical to a one-query request
at the same seed, setting, and demo count. Private changes alone cannot change
public paths. Existing differing files and symlink redirections are rejected.

`exporter.py` separates and validates supplied data; it does not certify labels.
The standalone writer obtains every label from the protected Racket bridge,
checks parity with the Python mirror, and retains the runtime identity. Give
the solver one selected `turns/` file, without the containing directory listing,
archive, private files, or suite manifest. The existing consumer controls reveal;
this proposal adds no turn controller or training loop.

Original prototype source and manifest are retained under
`evidence/public-id-correction/original/`; older reviewer-reported examples keep
their original status and are not the corrected public export.

## Reproduce from the outer packet directory

Use this checkout's own environment and bundled Racket setup:

```bash
WORK/.venv/bin/python review.py run python3 -m pytest -q generators/7fc158ab7b70/tests
WORK/.venv/bin/python review.py run python3 generators/7fc158ab7b70/workspace/parametric/scaling.py --all-settings --seed 17 --train 2 --test 4 --out ../checks/7fc158ab7b70/writer-replay
WORK/.venv/bin/python review.py run python3 generators/7fc158ab7b70/workspace/parametric/audit.py --out ../checks/7fc158ab7b70/self-audit-replay
WORK/.venv/bin/python review.py run python3 -m arcpuzzles parametric qualify 7fc158ab7b70 --seed 0 --seed 17 --demos 3 --queries 4 --out ../checks/7fc158ab7b70/qualification-replay --summary
```

Output directories must be new. Qualification consumes the source-bound
`promotion.json` and `evidence/manifest.json`; source changes require refreshing
that inventory and requalifying. The packet's return summary records the checks
actually executed, their bounded scope, and the separate owner acceptance gate.
