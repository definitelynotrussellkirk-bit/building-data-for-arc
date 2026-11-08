# Post-repair visible-only solve — 457b4958145b

This is a reviewer-authored work log, not a token-level model trace. I previously
read the task's generator and Racket rule while repairing it, and wrote semantic
rival probes. Earlier exposure is therefore **yes**. During this solve I opened
only the newly prepared visible challenge and authored this fresh Python
solution; generator code, reference source, earlier solution files and private
query labels stayed closed. Prior knowledge cannot be erased, so this is an
exposed post-repair attempt, not an independent blind induction claim.

## Visible evidence and revision 1

Examples have these independently measured dimensions:

- Example 0: input 12 rows x 12 columns; output 3 rows x 12 columns.
- Example 1: input 12 rows x 12 columns; output 3 rows x 9 columns.
- Example 2: input 14 rows x 13 columns; output 3 rows x 9 columns.
- Example 3: input 13 rows x 13 columns; output 3 rows x 9 columns.
- Query 0: input 12 rows x 12 columns; output unknown.
- Query 1: input 12 rows x 14 columns; output unknown.

The output is a horizontal collection of padded component crops. Example 1
contains disconnected objects sharing color 2, so color buckets would merge
unrelated pieces. I use same-color four-neighbor connected components. The 9s
select a reference point but are excluded as objects. Examples 0 and 2 retain
a 9 inside the right object's padding, so crops copy the full input rectangle.
Example 3 orders colors 7,3,2 around the earlier 9, consistent with the first
row-major marker. The top L shapes in examples 0 and 2 are first, consistent
with bounding-box-center geometry rather than occupied-cell centroids.

The implementation uses atan2 around the first 9, clockwise from up, with
upper-left coordinates resolving equal angles. Height-two pieces extend down
one row; narrow pieces gain a side column depending on their position. The
color-6 rectangle has a left padding column. I also retain the color-2 short,
three-column exception remembered from earlier exposure; these visible
examples alone do not establish that additional branch. Bounds clip at the
input edges, as the left-border components in example 1 demonstrate.

No negative attempt was fabricated. The first actual solution is checked with
the supported visible-only checker; private correctness remains unavailable.

## Observed check outcome

Revision 1 completed successfully: all 4 visible examples matched and both masked
queries executed. The checker did not reveal private query correctness (UNKNOWN).
The solve is finished with earlier repair exposure declared and no reference
consulted during this solve episode.
