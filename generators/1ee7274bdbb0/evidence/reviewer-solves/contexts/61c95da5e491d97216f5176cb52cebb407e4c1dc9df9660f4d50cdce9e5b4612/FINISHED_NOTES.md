# Post-repair visible-only solve — 1ee7274bdbb0

Earlier exposure: yes. I inspected this task's generator, canonical Racket rule,
canonical examples and authoring evidence during the repair. This episode is
therefore exposed, not a fresh blind induction measurement. Once the prepared
visible episode was displayed I used only its examples and my Python solution;
I did not reopen the rule, generator, reference solutions, prior solution
explanations or private query labels during the attempt.

## Revision 1

The six visible demonstrations keep the same overall dimensions as their inputs:
three 3x11 pairs, then 4x14, 7x11 and 9x14. Full color-9 lines partition the
arrays into square tiles. All red (2) cells become cyan (8), and green (3)
cells disappear. Unmarked tiles preserve their coordinates. A marked tile
rotates the red occupancy clockwise around the entire square tile.

For example, demonstration 0 changes the left tile, whose green marker is at
its top-right corner; the other two tiles copy. Demonstration 3 includes two
green cells per marked tile and demonstrates the same single quarter-turn.
Demonstration 5 includes three markers per marked tile with the same action.
Thus marker presence controls the branch; position and marker count do not
specify an alternate pivot, angle, or repeated number of turns. Demonstration 4
shows that row separators delimit independent tile rows.

Implementation: find full 9-valued separators, extract each tile, replace 2 by
8 and everything else by 0, rotate a marked tile using transpose of reversed
rows, then place it back into a separator-preserving output.

Check from packet root:
`python3 review.py solve check --intent solve --note 'Visible tile separators, conditional clockwise rotation, red-to-cyan recoloring and marker removal.'`
No diagnostic negative or artificial failed revision was created. Hidden-query
correctness remains for independent maintainer scoring.

Observed check: exit 0, execution completed, all 6/6 visible demonstrations matched. No reference was consulted during this solve. Hidden-query labels remain unopened and their correctness remains unknown.
