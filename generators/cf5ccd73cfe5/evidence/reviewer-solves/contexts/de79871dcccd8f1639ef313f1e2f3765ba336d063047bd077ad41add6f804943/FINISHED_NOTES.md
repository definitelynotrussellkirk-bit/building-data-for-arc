# Solve work log

I had not opened this task's rule, generator, notes, reference solutions, private
labels, or earlier solution explanations before this solve. I used only the public
challenge produced by `python3 review.py blind prepare`.

## Revision 1 — scale the detached motif into the frame

Hypothesis: each input contains (a) a complete one-cell-thick rectangular frame
and (b) a detached small motif. The output is the frame's bounding rectangle. Its
border keeps the frame color, while the motif's bounding box—including background
holes—is enlarged by integer row/column repetition to exactly fill the interior.

Evidence from the visible pairs:

- Example 0: a 3×2 motif expands by 2×4 into a 6×8 interior.
- Example 1: the 1×3 pattern `[5, 0, 5]` expands by 4×4 into a 4×12 interior.
- Example 2: a 3×3 motif expands by 2×2 into a 6×6 interior.

Implementation choices: detect the most frequent color as background; find a
same-color four-connected component that exactly equals a rectangle perimeter;
choose the largest such frame; crop all non-background cells outside it as the
motif; require exact divisibility; and repeat each motif cell into the interior.
This also handles motifs split into multiple components, as in visible example 1.

A test over all three public training pairs first failed on the template's
`NotImplementedError`; after this revision it is rerun before the official check.
Remaining uncertainty: the inferred task appears to guarantee one largest exact
frame and integer scale factors. The solution rejects malformed cases instead of
guessing an interpolation rule not supported by the examples.
