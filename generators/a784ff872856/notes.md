# Current notes: a784ff872856

## Current rule and source identity

The unchanged canonical/Racket authority:

1. extracts every nonzero same-color 4-connected object;
2. crops each object to its bounding box;
3. sorts by `(-bbox_width, -bbox_height, color)`; and
4. packs the normalized crops vertically, left-aligned, with one zero row between adjacent crops.

Current generator version: `2.1.0`  
Current generator SHA-256: `6790a56640ea1cf49ca945e6794781b42dedcda4dc1c8eb72e0cc1c9b2e8a064`  
Pinned Racket rule hash: `7991026f57da`

The canonical program and rule hash were not changed.

## Defect → repair

Version 2.0 correctly repaired the primary-key defect by guaranteeing a wider sparse object with fewer occupied cells than a narrower dense object. It still generated no equal-width objects, so two additional canonical-fitting rules survived every ordinary lesson:

- sort shorter objects first when widths tie;
- sort larger color first when width and height both tie.

Version 2.1 extends the constructive curriculum without broadening the public axes:

- `height_tie`: width-2 objects of heights 3 and 2 expose descending height;
- `color_tie`: equal 2×4 crops expose ascending color;
- `combined`: four-object draws contain both secondary-key lessons;
- every mode still contains the width-vs-cell-count inversion.

Three-object draws alternate `height_tie` and `color_tie` over the existing four-step schedule. Four-object draws use `combined`. `EXAMPLES_NEEDED` remains 3, so every consecutive three-example window contains both secondary lessons; every query rotation is required to remain identifiable.

## Executable semantic contract

Declared canonical-fitting rivals:

- `cell_count_first`;
- `height_ascending_on_width_ties`;
- `color_descending_on_dimension_ties`.

Declared witnesses:

- `width_over_cell_count`;
- `height_descending_on_width_tie`;
- `color_ascending_on_dimension_tie`.

Source-bound retained cases:

- `counterexamples/cell_count_first.json`;
- `counterexamples/height_tie.json`;
- `counterexamples/color_tie.json`.

`workspace/verify_width_lesson.py` keeps its historical filename but now implements the `a784ff872856-sort-lesson-probe-v2` contract: it discovers all live rivals and retained cases, verifies source/version/rule bindings, checks witness support, and optionally checks every retained case against the selected Racket authority.

## Verification actually run

- Focused task suite: `57 passed`.
- Source-bound retained-case probe with Racket: all three rivals fit the three canonical pairs; all three retained cases pass `self_check`; each relevant rival is separated and has matching witness support; all Racket outputs match the Python mirror; catalog rule hash matches `7991026f57da`.
- Shared semantic gate: complete declared schedule period enumerated; all query rotations required identifiable; pass.
- Bounded adversarial pass: 8,192 boundary sampler cases across four bands and all boundary shapes, plus 15,360 sliding-window/query-rotation checks over 2,048 generated inputs; no errors.

Primary receipts:

- `checks/sort-lesson-probe.json`;
- `checks/semantic-secondary-sort/result.json`;
- `checks/task-tests-secondary-sort/result.json`;
- `checks/adversarial-sort-curriculum.json`.

## Public controls and schedule

Public exact controls remain:

- `grid_h`: integer 7..14;
- `grid_w`: integer 9..16;
- `n`: integer 3..4.

Unknown/retired keys and non-integer values are rejected; explicit `None` retains the schedule default. Schedule profiles are the canonical anchors `(7,10,3)`, `(7,11,3)`, `(8,12,3)`, followed by a difficulty-broad profile: easy `(9,12,3)`, default/medium `(10,13,4)`, hard `(12,15,4)`.

## Remaining limits

- The constructive shape family is intentionally small. The declared rival set covers the three sort-key reversals reviewed here, not every imaginable equivalent program.
- The teaching manifold is limited to 7..14 by 9..16 canvases and 3..4 objects. That does not restrict the abstract canonical authority.
- The adversarial pass is bounded, not a proof over all seeds.
- Packaging this repair does not grant catalog approval or training admission.
