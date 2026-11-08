# Solve notes

Earlier exposure: yes. I had already inspected and repaired this task's generator before this required final-source replay, so this episode cannot be blind.

Visible-example hypothesis: copy the grid, then replace the middle zero of each **horizontal, contiguous** `1,0,1` triple with `1`, evaluating triples against the original row. Overlapping triples therefore fill both internal zeros in `1,0,1,0,1`. The examples deliberately leave wider horizontal gaps, vertical triples, `2,0,2`, and `1,2,1` unchanged.

I did not consult the Racket rule, canonical answers, generator source, private labels, or the prior solve notes while preparing this replay. One implementation should be enough because all three visible training pairs distinguish the relevant boundaries.
