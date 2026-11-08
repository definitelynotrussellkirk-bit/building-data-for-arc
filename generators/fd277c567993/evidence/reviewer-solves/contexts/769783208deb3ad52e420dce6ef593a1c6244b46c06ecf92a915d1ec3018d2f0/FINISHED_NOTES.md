# Solve work log

## Exposure statement

Before this blind solve I had not opened the generator, Racket rule, canonical
row, reference solution, prior solution notes, or audit evidence for task
`fd277c567993`. I used only the visible examples printed by `blind prepare`, the
public `challenge.json`, and local Python checks against the four visible pairs.
This workspace was reconstructed after an interrupted container; the solution
below replays the already derived visible-only hypothesis without introducing
reference exposure.

## Observations and hypothesis

Each input has three equal-width panels separated by two one-column dividers.
Panel 2 repeats panel 1's foreground object and adds cyan (`8`) cells. Panel 3
contains a different foreground object. The output starts from panel 3 and
transfers the additions from panel 2, translated by the displacement from the
top-left corner of panel 1's foreground bounding box to the top-left corner of
panel 3's foreground bounding box. A transferred cell overwrites an existing
panel-3 cell when the translated location is occupied.

The four visible translations are example 0 `(-1, 0)`, example 1 `(0, -1)`,
example 2 `(0, +3)`, and example 3 `(-1, 0)` including an overwrite. Direct
copying, center alignment, and lower-right alignment fail visible examples.

## Implementation and verification

The solver slices the three panels, computes both nonzero bounding-box origins,
finds nonzero cells where panel 2 differs from panel 1, translates those cells,
and draws them over a copy of panel 3. Detecting additions by panel difference
also handles a marker replacing a source-object cell.

The prior local four-pair harness passed all visible training examples, and the
official visible-only check recorded 4/4. This replay will run the same official
check and freeze its result. Private query correctness remains unknown.

## Query deductions

- Query 0: source origin `(1,3)`, target origin `(0,1)`, offset `(-1,-2)`;
  additions `(4,4)` and `(4,6)` become output `(3,2)` and `(3,4)`.
- Query 1: source origin `(1,1)`, target origin `(1,2)`, offset `(0,+1)`;
  the addition at `(2,3)` becomes output `(2,4)` and overwrites a target cell.

## Official visible-only result

Revision 1 completed with `visible_passed: 4` of `visible_total: 4`. I stopped
because one compact rule covers every visible shift and overwrite case; masked
query correctness remains intentionally unreported by the checker.
