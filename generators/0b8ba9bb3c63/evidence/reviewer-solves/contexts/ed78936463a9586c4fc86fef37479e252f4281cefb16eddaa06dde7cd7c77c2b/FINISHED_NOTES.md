# Exposed post-repair solve

This is an authored work log, not a token-level model trace. I inspected the selected generator and canonical rule earlier during repair, so earlier exposure is **yes**. During this solve phase I read only the public challenge and its preparation output, and wrote a standalone Python solution without reopening generator code, reference code, private labels, or earlier solution explanations.

The visible shapes are 19x23, 19x19, and 18x19 for both input/output respectively. The query inputs are 17x22 and 19x19; query outputs and their correctness are unknown.

The cyan rectangle emits a yellow band to the left and right for every occupied row, and above and below for every occupied column. Red cells are overwritten where those bands reach them; cells outside the bands remain unchanged. Each individual row/column ray stops on a non-red colored blocker. The first demonstration shows gray/brown 9 clipping one part of the band, the second shows blue 1, and the third shows 7 and 6. Therefore the blocker role is not limited to blue. Partial blockers stop only the rays they actually intersect.

Attempt 1 implements independent per-cell rays from the rectangle boundary. It reads blockers from the original grid, paints only 0 or 2, and preserves the original source/blocker cells. This avoids needing to erase and later restore blockers. No size thresholds, canonical-grid replay, or query labels are used. I will stop after visible examples and execution pass, retaining unknown query correctness for maintainer scoring.
