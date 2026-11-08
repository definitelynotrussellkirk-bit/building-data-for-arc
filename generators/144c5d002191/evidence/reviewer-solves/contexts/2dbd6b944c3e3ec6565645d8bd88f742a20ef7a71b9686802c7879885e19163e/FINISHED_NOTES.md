# Exposed post-repair solve work log

This is an authored work log, not a captured token-level conversation or a
log-probability trace. I had already read this task's rule while repairing its
generator, so earlier exposure is **yes**. During this solve I read only the
public preparation output/challenge and my own solution and feedback. I did
not reopen the generator, Racket rule, reference solution, earlier solution
explanations, or private query labels.

## Visible observations

Preparation supplied three demonstrations and two masked queries.

- Example 0: Input 11 rows × 14 columns; output 11 rows × 14 columns. A seven-cell
  color-3 shape disappears. The isolated colors 1 and 5 anchor recolored copies.
  The crop's top-left can be empty: the first occupied output cell is offset
  from a marker. One overlap is painted by the later marker's color.
- Example 1: Input 10 rows × 14 columns; output 10 rows × 14 columns. The color-1
  shape has seven occupied cells. Three color-5 singleton markers remain
  separate despite diagonal contact, while a color-3 singleton sits between
  two of them in the same row. Copies overlap and clip at the right edge.
  Grouping every cell of one color as a single object would lose these markers.
- Example 2: Input 10 rows × 14 columns; output 10 rows × 14 columns. A color-8
  cross produces full copies in colors 6, 4 and 5 at their singleton anchors.

Query 0 input is 10 rows × 14 columns; output unknown.
Query 1 input is 13 rows × 13 columns; output unknown.

## Revision 1 hypothesis

Use same-color orthogonal components. The non-singleton shape supplies occupied
offsets relative to its bounding box, independent of its color. Process singleton
components in row-major discovery order; place those offsets at each marker,
recolored to its color. Ignore cells outside the grid. Paint only occupied
offsets so blank shape cells do not erase an earlier copy. Start with a blank
same-size output; do not retain the source template or marker anchors separately.

I implemented a fresh small flood fill and stamp loop using only Python built-ins.
No generator/helper imports or reference calls are used by this solution.
The upcoming check is an ordinary attempted solve, not an intentional negative.

## Observed check result and stopping reason

The first checked revision completed successfully and matched **3/3 visible
examples**. No earlier checked revision failed. The two query inputs were
processed by the check, but private correctness feedback is withheld and remains
unknown. I did not fabricate a negative attempt or inspect hidden answers.

I stopped because the single implementation explains all visible shape, repeated
marker, clipping and overlap observations, and the available check passes all
three examples. Earlier rule exposure is yes; reference consultation during this
solve is no. This exposed solve is not an independent blind induction result.
