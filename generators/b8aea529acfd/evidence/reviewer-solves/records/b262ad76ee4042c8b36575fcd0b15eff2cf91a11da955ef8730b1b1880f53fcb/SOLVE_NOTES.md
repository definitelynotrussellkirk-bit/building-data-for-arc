# Post-repair visible-only solve work log

This is a concise assistant work summary, not a captured token-level conversation
or a log-probability trace. Earlier rule exposure: **yes**. Before preparing this
episode I reviewed the assigned generator and its Racket authority during repair.
During this episode I used only the displayed public challenge, my own visible
probe, the empty solver stub, and visible-only checker feedback. I did not reopen
the generator, reference source, prior solution explanations, or private labels.

## Revision 1 — crop nonzero content, then reverse every row

Visible shapes: example 0 is 15x17 to 4x6; example 1 is 9x10 to 7x8;
example 2 is 13x16 to 5x6. Their outputs preserve the foreground colors/counts
and horizontal row order is reversed inside the nonzero bounding rectangle.
The dense second example retains the full accent edge even though the body
color is more frequent than black. These observations support using explicit
zero background and the bounds of all foreground cells.

`python3 probe_visible.py` reads only the three labeled training pairs. Exact
matches were crop+LR 3/3, crop-only 0/3, crop+UD 0/3, and crop+180 0/3.
The alternatives were comparison probes, not submitted wrong solve attempts.
The retained output is `probe_visible.txt`.

I implemented one general `solve(grid)` using nonzero coordinate bounds and row
reversal. Empty foreground raises explicitly because no visible example covers
that case. No rule was inferred from unknown query outputs, and no artificial
failed revision was created. Query correctness remains withheld by the checker.
