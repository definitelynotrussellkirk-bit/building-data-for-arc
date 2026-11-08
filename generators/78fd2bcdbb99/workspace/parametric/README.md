# 78fd2bcdbb99 native parametric family

The hidden episode setting is `repair = fill | erase`.

1. **A — axis inference:** count left/right and up/down mismatches, choosing left/right on a tie.
2. **Intermediate:** the selected mirror axis for that input.
3. **B — repair policy:** `fill` copies a nonzero mirror into an empty cell (the exact canonical program); `erase` removes the unmatched nonzero instead.

Inputs are generated independently of the setting. Every scene contains multiple missing mirror pairs, both axes occur in the teaching prefix, query inputs include a 30×30 boundary-spanning case, and the same finite programs are used by the protected-Racket worker.
