# Solve work log

This is a human-authored work log. I had already inspected the assigned task's rule and generator while repairing it, so this is an **exposed** solve. During this solve episode I used only `solve/challenge.json`, my own counting, and checker feedback; I did not reopen the generator, Racket source, reference solutions, private labels, or earlier solution explanations.

## Revision 1

Visible evidence supports counting every sliding 2×2 window made entirely of color 1, then writing the count as a length-five row of leading 1s followed by 0s.

- Training example 1 contains a 6×2 vertical rectangle of 1s, hence five overlapping 2×2 windows and output `[1,1,1,1,1]`.
- Training example 2 contains a 2×6 horizontal rectangle of 1s, again five overlapping windows.
- Training example 3 contains five separated 2×2 all-1 blocks.

This distinguishes sliding-window counting from counting connected objects: the first two examples each have one connected target component but five windows.

For both visible queries I count two target windows. Query 1 has a 3×2 all-1 strip, and query 2 has a 2×3 all-1 strip. The predicted outputs are therefore both `[1,1,0,0,0]`.

The implementation scans every possible 2×2 anchor, counts all-one windows, validates the visible five-cell encoding range, and returns the unary bar. No alternative hypothesis remained competitive after comparing the elongated training strips with the separated-block example.
