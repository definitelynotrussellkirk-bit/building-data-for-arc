# Fresh solve work log

This is a human-authored work log, not a token-level model trace. I had already
seen the task rule while reviewing the generator, so this is **not a blind
solve**. During this solve phase I consulted only `solve/challenge.json`; I did
not reopen the generator, Racket authority, private labels, reference solution,
or earlier solution explanations.

## Visible-example analysis

### Hypothesis 1: erase nonzero cells that are isolated from all nonzero cells

This fails on training example 1. The color-5 cell is cardinally adjacent to a
color-4 component, yet it is erased. Therefore connectivity is color-sensitive,
not simply “all nonzero cells.”

### Hypothesis 2: erase same-color components of size one using 8-connectivity

This fails on training example 2. The two color-2 cells at the top are diagonal
neighbors, but both are erased. Therefore diagonal contact does not connect an
object.

### Selected rule

Find every nonzero **same-color 4-connected component**. Preserve every
component with at least two cells exactly, and replace every one-cell component
with background 0. Grid dimensions and surviving colors/positions are unchanged.

The three demonstrations jointly test the important distinctions:

- example 1: a differently colored touching singleton is still erased;
- example 2: same-color diagonal singletons are still separate;
- example 3: multiple surviving components of repeated colors are handled
  independently, while unrelated one-cell components disappear.

## Predicted query behavior

- Query 1: keep the horizontal four-cell color-4 component and vertical
  two-cell color-1 component; erase singleton colors 3, 6, and 8.
- Query 2: keep the three-cell color-7 component, the three-cell color-1
  component, and the vertical three-cell color-2 component; erase all three
  separated color-4 singletons.

## Revision 1

Implemented a row-major breadth-first traversal over same-color cardinal
neighbors. The output starts as background and copies back only components of
size greater than one. The implementation does not mutate its input.
