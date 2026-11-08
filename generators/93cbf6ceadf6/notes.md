# Working notes: 93cbf6ceadf6

## 2026-10-26 reviewer repair

The imported generator described a generic multi-motif gallery and did not
construct the canonical relation. A bounded diagnostic sample found the
required translation-normalized shape multiplicities `[2, 1]` in only 6 of
100 ordinary scenes.

The replacement is constructive rather than rejection-only:

- exactly three separated monochrome objects are placed;
- two objects share one translation-normalized shape and the third uses a
  different shape;
- repeated and odd shapes have equal area and bounding-box dimensions;
- colors vary through all-same, 2+1, and all-distinct multiplicities;
- shape roles are shuffled across positions;
- common dihedral orientation varies without weakening the controls;
- `grid_h` and `grid_w` are the only observable overrides, with exact 9 and 22
  boundaries;
- `_odd_output` independently mirrors the canonical Racket label.

Regression evidence:

- `WORK/checks/93-base-red`: the old gallery generator failed the canonical
  2+1 grammar and required helper/metadata contract;
- `WORK/checks/93-base-green-1`: 6/6 semantic suites passed, including all
  canonical pairs, 180 ordinary generated scenes, override boundaries,
  deterministic fresh returns, structural impostors, and protected-Racket /
  Python label agreement.

This is reviewer-authored evidence only. Owner acceptance and training
admission remain separate decisions.

## Native parametric family

The task-local family fixes the first stage to the canonical odd-shape
selection and varies `output_transform` across `identity`, `rotate_cw`, and
`flip_lr`. The identity program preserves canonical bytes exactly; the two
other programs apply one guarded Racket transform to the canonical cropped
output. Inputs are setting-independent, and every selected odd shape is
asymmetric under all three transforms.

Current reviewer evidence:

- 12/12 staged suites in `WORK/checks/93-parametric-green-2`;
- protected self-audit with 144 Racket evaluations;
- source inventory manifest
  `e2a82dc3c58787eb83d350159dc3a53cb4ffaecd56fabea2403be35a29588211`;
- authoring preflight with 6 jobs, 36 parametric labelled pairs, 3 canonical
  pairs, and 60 protected Racket evaluations;
- protected causal witness: replacing the normalized odd-object intermediate
  with a repeated-object intermediate changes the final output while the
  identity transform is held fixed.

These are reviewer-authored checks, not owner acceptance or training
admission.

## Public projection and final integrity checks

The qualified receipt was projected through the packet's native one-query
exporter into 24 public views. The combined first-turn checker for both assigned
families passed 14 first turns, 84 hidden-label invariance checks, 14 positive
controls, and 56 public views. A final cross-family sweep exercised 480 visible
scenes for this target (30 seeds at both 2 and 6 demonstrations), including all
three transforms and an edge-spanning 30x30 query. These checks do not grant
owner acceptance or training admission.
