# Working notes: d2708f8b731b

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

## Parametric prototype-rotation proposal — review-5b7b5236332485e6

`workspace/parametric/` exposes
`prototype_transform=identity|quarter_turn`. `identity` is the exact canonical
program. Under `quarter_turn`, each left prototype is rotated clockwise before
its normalized shape is matched to right-side targets. Every sampled input uses
all four orientations of one asymmetric L-triomino orbit on both sides, making
the grammar total and matched across both settings while preserving legend
parsing, shape transformation and symbol-grounded recoloring.

Counts are 2–6 demonstrations and 1–4 queries with stable prefixes and private
settings. Legend order, colors, target positions and repetitions vary. The
fourth query is a 30×30 scene with 65 separated targets, at least twelve copies
of every orientation, 207+ neutral cells and nonzero content on every boundary.
Demonstrations reject the alternate setting, two constant-color shortcuts and a
target-position/order shortcut without using query answers.

The canonical test now resolves canonical data through
`reviewer_support.find_root/canonical_path`, so copied task-test runtimes work.
Fresh evidence: the staged target suite passed 22 tests plus five subtests; all
three canonical inputs passed; protected Racket executed five programs over
seven inputs (35 evaluations). Native inventory SHA-256:
`d67c37fd94ff5a519d586a1734af34c7121fa39832b9fe8b888c7918a8890ac7`.
The four-orientation grammar is intentionally bounded and remains a proposed
family, not owner qualification or training admission.
