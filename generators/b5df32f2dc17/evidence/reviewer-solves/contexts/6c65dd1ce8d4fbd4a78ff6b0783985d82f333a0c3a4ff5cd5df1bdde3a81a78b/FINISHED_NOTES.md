# Solve notes

The visible examples act independently on each row. I parsed each nonzero monochrome run, preserved its color and length, sorted runs from longest to shortest, then rebuilt the row at the left edge with exactly one zero separator. Blank and singleton rows are consistent controls: they are merely left-packed. For an unshown equal-length tie, I preserve original left-to-right order as the least additional assumption.

I had earlier exposure to the task rule while repairing the assigned generator, so this is an exposed post-repair solve. During this solve episode I used only `solve/challenge.json`; I did not reopen the generator, Racket rule, reference solution, or private labels.
