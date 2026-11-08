# Solve work log

## Exposure

I had already inspected this task's generator and Racket rule during the repair, so this is an **exposed** post-repair solve. During this solve episode I consulted only `solve/challenge.json`, this work log, and the visible-only checker. I did not reopen the generator, Racket authority, reference solutions, private labels, or the prior solve notes.

## Visible-example inference

All three demonstrations distinguish three vertical occupancy cases:

- A maximal same-color vertical run of exactly three cells has only its top and bottom cells changed to color 8; its middle cell keeps its input color.
- Same-color vertical runs of length four remain unchanged.
- Three consecutive occupied cells with changing colors remain unchanged.
- A same-color run of length two also remains unchanged.

This supports the rule “mark endpoints of maximal same-color vertical runs of length exactly 3,” rather than the color-blind shortcut “mark every three occupied cells” or a threshold rule such as length at least 3.

## Revision 1

Implemented a column scan over maximal contiguous runs of one nonzero color. The output is a deep copy; runs of length exactly three get endpoint color 8. No horizontal or component-level operation is needed. I am checking this as an ordinary solve attempt because it is the direct rule inferred from the visible demonstrations.

Remaining uncertainty before checking: masked-query correctness is unavailable by policy, but the demonstrations directly cover the color-sensitive and exact-length boundaries relevant to both test inputs.
