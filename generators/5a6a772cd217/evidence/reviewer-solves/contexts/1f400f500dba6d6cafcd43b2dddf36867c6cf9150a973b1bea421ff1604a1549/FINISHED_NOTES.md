# Visible-only solve notes — 5a6a772cd217

## Exposure declaration

I had already inspected this task while repairing its generator, so this is an
**exposed** solve, not a blind one. During this solve phase I used only the
visible train examples printed by `solve_episode.py prepare`; I did not reopen
the generator, Racket rule, reference solution, or private query labels.

## Hypothesis from the visible examples

1. Find each 4-connected color-5 component that forms a hollow rectangle.
2. Order those frames lexicographically by their top row, then left column.
   Train 0 and train 2 are decisive: the topmost frame is physically to the
   right, yet its interior appears first in the output.
3. Extract the *entire* interior rectangle, including zeros; do not tight-crop
   to the colored cell.
4. Top-align all interiors in a common output height equal to the tallest
   interior.
5. Concatenate the panels directly. For an interior narrower than 3 columns,
   add one zero column. The first panel puts that extra zero after its content;
   every later narrow panel puts the zero before its content.

Checks against the visible examples:

- Train 0: the top-right 2x2 interior becomes a 3-column first panel with a
  trailing zero; the later 3x3 interior follows it.
- Train 1: the first panel is already 3 columns; both later 2-column interiors
  receive a leading zero, giving 3+3+3 output columns.
- Train 2: the top-right narrow frame is first despite its x-position, followed
  by the lower-left full-width frame and then the final narrow frame.

## Implementation plan

Use a 4-neighbor flood fill over color 5, obtain each component bounding box,
sort boxes by `(top, left)`, slice interiors, pad each panel according to the
rule above, and concatenate row by row. No query-specific constants are used.
