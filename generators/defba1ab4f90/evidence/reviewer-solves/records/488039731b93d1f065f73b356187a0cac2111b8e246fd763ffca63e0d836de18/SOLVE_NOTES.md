# Solve work log

## Exposure record

I had already inspected and repaired the task before this separately required solve, so earlier rule exposure is **yes**. After `solve prepare` I did not reopen the generator, Racket authority, reference solutions, private labels, or earlier solve notes. I used only `challenge.json` / the visible examples and local Python checks.

## Revision 1

Hypothesis from the three visible pairs:

- The unique red `2` on the top or left edge is the source of a stream. It advances inward, vertically from the top or horizontally from the left.
- The stream paints only background-zero cells red and preserves blue/green bars.
- When the next cell is part of a perpendicular bar, the stream slides along the clear line immediately before that bar until it is one cell beyond an endpoint, moves past the bar, and resumes its original direction.
- Blue `1` chooses the stream's left-hand side; green `3` chooses its right-hand side. This is orientation-relative: for a downward stream blue goes right and green left; for a rightward stream blue goes up and green down.
- Bars that do not intersect the current lane are distractors and remain unchanged.

I implemented that geometric rule directly, including rectangular-input checks, a single-marker check, full contiguous-bar endpoint detection, and blocked-detour rejection. A local comparison against all three visible training outputs matched exactly on the first revision. The strongest alternative considered was treating colors as fixed screen directions; train examples 0 and 1 refute that because the same color must rotate with the entry orientation.

Remaining uncertainty is limited to unseen malformed scenes; the visible grammar consistently supplies one non-corner source and clear detours.
