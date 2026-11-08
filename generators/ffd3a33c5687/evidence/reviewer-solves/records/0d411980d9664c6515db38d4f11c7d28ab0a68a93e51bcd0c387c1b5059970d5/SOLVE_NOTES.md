# Solve notes

## Revision 1

Visible pattern: each output row is horizontally symmetric. For every mirrored
column pair, copy the nonzero member to both cells. The demonstrations also
contain occupied conflicts: in train 1 row 1, the outer pair is `0,5` and becomes
`5,5`, while row 0 has `0,5` at the outer pair and `7,2` at the next occupied
conflict; the output uses the left-side `7` for that conflict. Train 2 row 4 has
`1` on the left and `9` on the right and becomes `1,1`. Therefore the exact rule
is: choose the left member when it is nonzero, otherwise choose the right member,
and write the choice to both mirror positions. A center column is unchanged.

The implementation is a pure row-wise transform and does not mutate the input.
