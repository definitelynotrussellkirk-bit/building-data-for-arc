# Solve work log

This is a human-authored work log, not a token-level model trace. I had already
seen the selected task's reference rule while reviewing its generator, so prior
rule exposure is **yes**. During this fresh episode I used only the visible
examples in `solve/README.md` / `solve/challenge.json`; I did not reopen the
Racket rule, generator, prior solve notes, reference solutions, or private labels.

## Revision 1

### Observations

Across all three visible pairs, the output preserves the input and sometimes
fills the two missing corners of a 2×2 square. A fill occurs when the other two
corners form a diagonal, have the same nonzero colour, and both missing corners
were zero in the input. Both diagonal orientations occur:

- train 1 completes colour 4 at rows 2–3, columns 0–1 from a main diagonal;
- train 1 completes colour 8 at rows 2–3, columns 5–6 from an anti-diagonal;
- train 2 leaves same-colour orthogonal cells unchanged;
- train 2 leaves a mixed-colour diagonal unchanged;
- train 2 leaves a same-colour diagonal unchanged when an opposite corner is
  already occupied.

### Hypothesis

Scan every original 2×2 window. If one diagonal contains equal nonzero values
and both opposite corners are zero, copy that colour into the opposite corners.
Apply the main- and anti-diagonal cases symmetrically, never overwrite occupied
cells, and compute all decisions from the original input so a newly completed
square cannot trigger a cascade.

### Implementation

`solution.py` copies the input, scans each original 2×2 window, and writes only
the two qualifying zero corners. The source grid remains immutable during the
scan. I expect this to reproduce all visible examples and handle both hidden
queries without relying on colour identity or location.

### Remaining uncertainty

The visible examples strongly distinguish the blocked-corner, mixed-colour,
orthogonal-pair, and one-orientation shortcuts. The only residual uncertainty
is ordinary finite-example induction: an undeclared alternative rule could agree
on these examples, but no such alternative is suggested by the observed changes.
