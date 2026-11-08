# Rotation-only four-piece jigsaw

## Current rule and source decisions

The supplied parent contains three training labels and one gold test label.
All four describe the same rule: use rotations and translations to assemble
the four colored pieces into a completely filled square, with the gray 5 cell
at its northwest corner. Gray belongs to the orange 7 piece. Preserve every
colored cell. Group pieces by color, not by four-connected components: the
first supplied example has a diagonally attached, otherwise isolated 7 cell.
Reflection is not permitted. An independent enumeration found one distinct
rotation-only output for each original; allowing reflections admits alternatives.

`reference.rkt` is a new general exact-cover solver, not an example lookup.
It computes square side from nonzero area, deduplicates quarter-turns, and
anchors the actual 7+5 piece before filling the remaining space. It selects
the first solution on the admitted unique-assembly grammar. The Python kernel
enumerates until a second distinct answer is found and rejects ambiguous inputs.
Thus generation does not assume that the constructed latent board is unique.

## Native family

`anchor_corner = northwest | northeast` stays fixed across an episode. The
default source is byte-identical to `reference.rkt`; northeast places the marker
at the upper-right corner before the same assembly search. Its answer is the
clockwise rotation of the northwest reconstruction. This parameter changes the
geometric orientation taught by the demonstrations. It does not supply the
jigsaw's underlying sequential dependency: that dependency already exists in
the canonical assembly rule.

The adapter supports 2–6 demonstrations and independently 1–4 queries. The
minimum is two, and the normal private query bank contains four distinct fresh
inputs. The same seed/count request has exactly matched inputs across settings.
Query source profiles remain independent of the requested demonstration count.

All runtime dependencies are inside `workspace/parametric`: `adapter.py`, the
byte-identical `canonical.rkt`, and `kernel.py`. The standalone `generator.py`
and native `kernel.py` are also byte-identical; neither imports another task,
checkout, source dataset, or answer bank. The base rule ID is `ee_7b3084d4`.

## Fresh input grammar and diversity

Generated answers are squares with side 6–24. Four regions begin with independently
offset horizontal and vertical splits, so piece areas and extents can differ.
Each internal seam varies one-cell tabs and notches in both directions. The
three non-anchor colors, tab patterns, independent rotations, slot assignment,
and translation jitter vary with the input RNG. Marker 5 and base color 7 retain
their original roles. A blank separating row and column keep the four pieces
apart after scattering. Every proposal is solved from its rendered input; only
a unique answer equal to the latent construction is admitted.

Queries span output sides 6, 10, 16, and 24. The largest input is 30×30 with 576
colored cells distributed across all four slots, rather than a small puzzle
surrounded by padding. Its answer is 24×24. A filled 30×30 answer would require
900 colored input cells and leave no background for separated pieces within the
ARC 30×30 bound. The canonical solver also handles the original 4×4 answer;
fresh sampling starts at 6×6 to provide more variable seam geometry. This sampler
covers four roughly rectangular regions with one-cell tabs, not every possible
polyomino exact-cover instance supported by the solver.

## Sequential dependency and retained evidence

A: group and orient the input's 7+5 anchor piece at the instructed corner.
Its intermediate is the actual placed cell set and occupancy mask. B: rotate
and position the other three pieces so they cover exactly its complementary
space. Their valid placements depend on the input-specific anchor boundary.
The causal ablation retains the anchor in the output but omits its occupancy
when placing the other pieces, terminating after those three pieces have been
used. This yields overlapping placements and uncovered cells, despite preserving
the marker corner. Both complete programs execute as typed grids; the ablation
changes the final answer. The witness records these two edits explicitly.

Evidence is under `checks/public_eval_7b3084d4/`: official-pair execution and
all-setting authoring preflight, protected causal construction/replay, a finite
executable-rival audit, independent source review, and strict public projection
checks. `public_eval_7b3084d4-tests/` contains relocated task-test receipts.
The audit checks two seeds with six demonstrations and four queries per setting,
then checks whether the first two demonstrations reject six declared shortcuts.
Those checks do not prove universal teachability or exhaustive solver correctness.

## Reusable authoring projection tool

`workspace/authoring_preview.py` builds one-query views from an unregistered
public-creation preflight. It shuffles the complete four-query bank privately
before selecting a visible prefix. Public files contain only demonstrations
and the selected query input, and their names hash only those visible bytes.
The controller keeps the directory listing, mappings, settings, programs,
answers, and future queries private. The helper verifies source receipts and
serialization and tests hidden-field invariance plus tampering negatives. It
does not implement a model controller or perform another Racket replay.

From the packet folder, after the preflight exists:

```sh
WORK/.venv/bin/python review.py run python3 generators/public_eval_7b3084d4/workspace/audit_family.py --root . --out ../checks/public_eval_7b3084d4/audit.json
WORK/.venv/bin/python review.py run python3 generators/public_eval_7b3084d4/workspace/authoring_preview.py --root . export --public-preflight ../checks/public_eval_7b3084d4/preflight/preflight.json --presentation-seed 109 --out ../checks/public_eval_7b3084d4/authoring-preview
```

Use fresh destinations for reruns. The creation preflight and all retained
receipts are authoring evidence. Owner registration, exact-source review,
native qualification, acceptance, and training admission remain separate.

Owner worker API correction: use the existing worker input/findings contract. Earlier author checks used the incompatible return convention. Reference programs are unchanged; owner preflight and native acceptance determine current readiness. See evidence/owner-base-api-repair.json.

## Current repeated-return reconciliation

Preserve exact northwest/northeast programs and the broad rotation-only unique-assembly sampler. Port color-5 highlighting of the assembled bottom-right piece after canonical assembly. Incoming constructions only contribute where they satisfy the incumbent four-color-piece, marked-color-7 and unique-rotation grammar; generalized marker palettes/other packing interpretations remain excluded. Independent query shuffling and visible rival-separating prefix preserve 2–6 demos and four sequential queries. Evidence: `evidence/reconcile-15/`. Private native qualification, fresh native acceptance re-execution and bounded protected execution passed. Live publication and training admission remain separate.
