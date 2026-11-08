# 6098a755202d

A zero-background grid contains one closed rectangular color-5 frame with at
least a one-cell outer margin. Two or three colored seed cells sit inside it.
For every zero inside the frame, find the minimum Manhattan distance to the
seeds and collect the **distinct colors** among the nearest seeds. Fill the cell
when that color set has size one; leave it 0 when different colors tie. The
frame and original seeds remain unchanged. Thus two equally near seeds of the
same color still fill their shared nearest cells.

The generator schedules three complementary lesson profiles across every three
sample indices: two distinct-color seeds, a repeated-color three-seed witness,
and three distinct-color seeds. The repeated-color profile is required because
all canonical seeds have distinct colors and therefore cannot distinguish the
executable rule from the plausible shortcut “any tie between seed cells stays
0.” Grid size, top/left frame offsets, and profile are explicit observable
overrides; unknown overrides are rejected.

Kind: `per_puzzle`. Reviewed version: `3.0.0`. Rule hash:
`5ede5108ff10`.
