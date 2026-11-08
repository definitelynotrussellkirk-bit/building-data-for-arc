# Enclosed-region matching and pattern insertion

This unapproved family starts from the supplied public parent `8698868d`. The root
`reference.rkt` is a general component/count/placement algorithm. It contains no
original grids, answers, task lookup, or fixed object coordinates. The adjacent
`canonical.rkt` is an exact byte copy, kept inside the native adapter resource
boundary. `program({"pattern_orientation":"as_observed"})` is exactly those bytes.

## Rule and grammar

Infer the unique modal background. Build color-blind four-connected foreground
components. The component with the unique largest bounding-box area is the board;
the remaining components are monochrome framed square patterns of a common side n.
The board is a rectangle tiled by squares of side n+2. Each panel has a complete
one-cell frame in its own base color and contains only that color and background.
The patterns likewise have complete foreground borders, so background components
inside either kind of square are enclosed regions.

Count those background regions with four-connectivity. Counts, including zero,
match panels to patterns one-to-one. Rebuild each panel in its base color and
insert its selected pattern with a one-cell margin. Pattern foreground retains
its source color; pattern background becomes the panel base color. Crop the
output to the board. Pattern color, panel color, location, hole area, and exact
hole positions do not select the match. Colors may recur in spatially separate
objects and zero may be foreground.

The strict Python validator rejects non-integer/bool colors and coordinates,
nonrectangular/oversized grids, background ties, incomplete borders, inconsistent
pattern sizes, nondivisible boards, and missing or duplicate count matches. The
generated domain requires connected foreground in each framed pattern and panel.
The general Racket rule assumes that validated constructive grammar; it is not a
general malformed-input parser.

## Episode parameter and dependency

`pattern_orientation` is fixed for an entire episode:

- `as_observed`: inset the selected pattern in its observed orientation; canonical.
- `clockwise90`: rotate the selected square pattern clockwise once before inset.

Both settings share the exact input stream. Asymmetric patterns in the first two
demonstrations teach the orientation. The background and board frame never rotate
independently; the variant rotates only the matched loose pattern.

A extracts the board and patterns, measures enclosed-region counts, and creates
the count-based assignment. Its intermediate records each panel origin/base/count
and the selected source pattern. B consumes that assignment and renders the
selected pattern. B cannot choose a source shape or color before A identifies
its match. A causal intervention changes only this derived assignment while
retaining the input, setting, and rendering code.

## Sampling contract

The constructive scene bank supplies six demonstrations and four distinct novel
queries with changed pattern size, board geometry, source ordering, and clue/hole
geometry. Every scene receives an independently drawn palette bijection and global
D4 transform. Labels are computed from the augmented input, so the clockwise
variant remains clockwise even after an input reflection. There is no rejection
loop or original-example fallback.

Separate SHA-derived streams control settings, demonstrations, and queries.
The whole query bank is shuffled before a requested prefix is returned. Supported
counts are 2..6 demonstrations and 1..4 queries, with ordinary default 3 demonstrations;
the public authoring preflight uses the supported minimum 2 and four queries.
The declared `qualification_demos: 3` selects three for a later owner native check;
the minimum of two is separately exercised by this preflight and teaching audit.
Seeds are exact integers 0..2**63-1. The root generator returns individual canonical
inputs; full teaching assembly belongs to the native adapter.

## Evidence and status

Focused tests and independent protected-Racket audit evidence live under
`checks/public_eval_8698868d/`. The current source-bound authoring preflight,
original-pair execution, causal replay, and one-query public exports are separate
evidence stages. No receipt here confers owner registration, native qualification,
acceptance, or training admission. Current outcomes and finite limits belong in
the task's root `notes.md` and the packet `RESULTS.json`.
