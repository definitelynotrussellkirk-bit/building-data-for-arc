# Working notes: 54099d17f2dd

Review assignment `review-ffea91b203f27087` repaired the imported v2.0.1
sampler. Baseline blockers were missing rule pin, fake/dead axes, accepted
unknown overrides, invalid degenerate textures, and a validator that accepted
most impostors. The Racket authority itself matched the intended copy rule and
was not changed.

The v3.0.0 sampler uses finite constructive placement, exact observable axes,
a structural validator, Python rule mirror, and a four-example semantic
schedule. Canonical-fitting rivals and their witnesses are executable in the
generator and inspected by the reusable workspace tools. Final generator SHA-256:
`5b0ab830dbd12979b22091dc84c111b81d5b40570d8278652d979474c00b8593`.
## Current reviewer considerations

Source SHA-256: `5b0ab830dbd12979b22091dc84c111b81d5b40570d8278652d979474c00b8593`.

# Decisions: 54099d17f2dd

## Goal and authority boundary

The intended transformation was already correct in the selected canonical Racket
authority: normalize the sole color-2 template and stamp the same offsets in color
8 at the color-1 marker on a fresh zero grid. I therefore left the authority and
canonical data unchanged and repaired only the generator contract, curriculum,
validation, tests, and task-local tools.

No prior review return was used as a lead. The current selected packet source and
its reproduced before-battery failures were the design inputs.

## D1: expose only three exact axes

Chosen controls:

- `grid_h`: integer 8..13
- `grid_w`: integer 10..16
- `template_shape`: one of nine literal named shapes

These properties can be read back unambiguously from a generated input, so
`observe_overrides` can prove fulfillment. Unknown, out-of-range, and wrong-type
requests fail rather than silently falling through.

Rejected alternative: retain `density`, `position_bias`, vague shape metadata, or
other cosmetic knobs. They were dead, single-valued, or not structurally
observable, and they caused the baseline override gate to fail.

## D2: use a finite connected shape bank

The bank contains seven 3/4-cell forms and two asymmetric five-cell forms. It
keeps the task recognizable while varying dimensions and normalized geometry;
the five-cell forms are necessary because every canonical template has four
cells, making “copy only four” a plausible rival.

Rejected alternatives:

- Tetromino-only sampling: preserves the canonical shortcut.
- Arbitrary random blobs: weakens the task boundary and makes override semantics,
  strict validation, and lesson guarantees harder to state.
- Degenerate line/noise textures: the baseline used variants that no longer
  represented one reusable template object.

Failure mode/limit: a finite bank cannot cover every connected polyomino or every
hypothesis conditioned on exact shape identity. The reports therefore claim only
coverage of the declared bank and rivals.

## D3: construct source and marker placements instead of retrying

For each `(height, width, shape, relation)`, the generator enumerates lawful
source/marker anchors and samples from that finite set. It enforces in-bounds
source/stamp geometry, a one-background-cell gap, and one of four strict quadrant
relations. The pure candidate function is LRU-cached because the override battery
reuses the same finite geometries thousands of times.

Rejected alternative: capped random retries. A retry cap can turn a valid exact
override into seed-dependent failure and makes absence of a layout indistinguishable
from unlucky sampling.

## D4: four-profile schedule and four demonstrations

The production cycle is:

1. lower-left asymmetric `zigzag5`
2. upper-right tetromino
3. upper-left asymmetric `long_l5`
4. lower-right 3/4-cell shape

Four consecutive demonstrations contain two independent five-cell, leftward,
asymmetric witnesses. In a five-pair lesson, withholding any one pair still leaves
at least one witness for each declared rival. The schedule is ordered in
production, but arbitrary query positions were explicitly required and checked;
all 1,500 census rotations passed.

Rejected alternatives:

- Random unstructured lessons: individual grids may be correct while a lesson
  accidentally leaves a canonical-fitting rival alive.
- One witness per cycle: a query holdout can remove the only counterexample.
- More demonstrations: unnecessary for the two declared competitors and increases
  training cost without a measured benefit.

## D5: executable semantic competitors

The two selected competitors are:

- `mirror_when_marker_left`: horizontal reflection only for leftward copies.
- `copy_first_four_cells`: assumes all templates are tetrominoes.

Both reproduce all three canonical outputs, so they are not invented strawmen.
The generator declares the rivals, witness predicates, witness-to-rival mapping,
and `lesson_identifiable`; task tests and the reusable shortcut analyzer verify the
same behavior with actual generated grids.

Rejected alternative: document shortcuts only in prose. Prose does not let the
semantic gate or future agents replay the disagreement.

## D6: structural validation is the task boundary

`self_check` now validates rectangular ARC-valued grids, palette `{0,1,2}`, one
marker, one 4-connected 3..5-cell template from the declared bank, dimensions,
fit, gap, and strict-quadrant placement. `strict_canonical_like` delegates to that
same structural boundary, and `rule_mirror` rejects malformed inputs before
painting.

Rejected alternative: count-only validation. The baseline accepted impostors and
could not protect rule probes, exact-axis observation, or semantic witnesses.

## D7: independent tools for future agents

`workspace/reference_probe.py` extracts rule state without importing production
generator helpers and batch-compares its Python transcription against the selected
Racket authority. `workspace/analyze_shortcuts.py` verifies canonical fit, searches
ordinary scheduled draws, and records exact inputs, both outputs, differing cells,
override observations, and Racket parity.

This separation reduces the chance that a defect shared by generator and test
oracle masks itself.

## Verification policy

The final acceptance evidence uses the full after battery, explicit selected-task
tests, required-rotation semantic gate, 300-lesson census, independent shortcut
probe, and a fresh-copy patch replay. Intermediate failures are retained rather
than overwritten.

## Limitations and self-review

The declared rival family is finite. In particular, the ordinary profile schedule
correlates leftward cases with the two five-cell shapes, so a sufficiently
feature-conditioned hybrid rule can be constructed that is not one of the two
competitors; this is a distribution restriction, not hidden by the reports.

The exact override contract supports every shape in every profile relation, but
production lessons do not enumerate that full cross-product. The 300-lesson census
and exhaustive task-local cyclic-start tests establish the reported results only
for the declared rivals and sampled/constructed schedules, not universal ARC rule
identifiability.
