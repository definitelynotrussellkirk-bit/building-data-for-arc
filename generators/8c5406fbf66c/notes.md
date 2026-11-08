# Working notes: 8c5406fbf66c

## Reproduced defect

The canonical Racket rule scans every 2×2 window independently. A solid 2×3
same-color rectangle therefore has two overlapping matches, and both top-left
cells become 8. Version 1.2.0 instead classified connected components and
accepted only components of exactly four cells. It rejected the retained 2×3
witness and generated only separated blocks, leaving the concrete shortcut
"mark exact-four-cell 2×2 components" unchallenged.

## Repair

Version 1.4.1 makes windows, not components, the semantic unit and closes the
independent battery findings discovered after the first focused repair:

- `_active_windows` enumerates every nonzero same-color 2×2 window;
- `self_check` counts active windows and requires every nonzero cell to be
  covered by at least one such window, while retaining the minimal 2×3 witness;
- a period-three schedule emits one exact canonical profile followed by two
  overlap witnesses, so every three-example lesson includes both obligations;
- exact controls are reduced to observable `grid_h`, `grid_w`, and `blocks`,
  use strict scalar validation, and record keyed provenance on every branch;
- `observe_overrides` recovers all three controls from the returned grid;
- `strict_canonical_like`, `SEMANTIC_WITNESSES`, the
  `isolated_components_only` rival, and `lesson_identifiable` form an executable
  finite-rival teaching contract;
- `RULE_HASH = "29d77c7080ca"` pins the selected canonical source;
- the canonical Racket rule itself is unchanged.

The canonical-profile branch preserves the three source profiles
`(5,6,3)`, `(6,8,3)`, and `(6,9,4)` (height, width, palette size). The overlap
branch supports exactly 2–4 active windows throughout the declared 4–16 canvas
range, including 4 windows in a 4×4 grid via a solid 3×3 motif.

## Evidence

- `tests/test_overlapping_windows.py`: 11 focused tests covering the retained
  witness, protected canonical Racket, canonical acceptance/profile support,
  strict endpoint overrides, draw provenance, rival refutation, and every
  rotated three-demo lesson window.
- `counterexamples/review-overlapping-windows-v0001/witness.json`: compact
  before/after regression with both active anchors and current source binding.
- Packet receipt `checks/8c-full-battery-after-final/`: all 12 generator battery
  stages green with the declared period fully enumerated.

The finite contract refutes the retained isolated-component shortcut; it does
not prove uniqueness against arbitrary programs. Imported associated notes keep
original evidence and timestamps in `evidence/associated_notes.jsonl`.

## Native parametric admission proposal (2026-10-24)

The canonical default remains byte-for-byte unchanged at program SHA-256
`29d77c7080ca5589952e6febadcdcf8d34371c4fbea20b4e5bd86573e0534030`.
The task-local `window_scope` adapter adds one nearby alternative,
`key_count_relay`: count the unique color-1 source object's solid 2×2 windows
(`k` in 1..3), sort three independently varied candidate objects by occupied
area, select rank `k`, then mark only that object's 2×2-window top-left cells.
The same inputs are used for both settings; candidate color, position, area,
aspect ratio, source orientation, and isolated color-9 distractors vary.

The adapter supports independent 2–6 demonstration and 1–4 query requests,
keeps four private prefix-stable queries, reveals one query input per public
turn, and includes a substantive 30×30 boundary case. Two demonstrations
refute the finite shortcut set retained by `verify.py`; the check uses no query
answers. Visible public grids are strictly validated while private settings,
programs, future queries, and query answers cannot affect first-turn bytes.

Current evidence is bound by `workspace/parametric/evidence/manifest.json`.
Native qualification executed two settings over fresh seeds in protected Racket
(4 jobs, 40 labels), and the retained wrong-rank-one replay changes the qualified
answer when the intermediate is forced from 2 to 1. This is reviewer-ready only:
the owner must re-run qualification and exact-source acceptance after integration;
no variant or training admission is claimed.
