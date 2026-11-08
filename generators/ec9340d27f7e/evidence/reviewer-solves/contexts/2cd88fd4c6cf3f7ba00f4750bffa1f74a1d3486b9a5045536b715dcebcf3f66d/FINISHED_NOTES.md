# Blind solve notes — ec9340d27f7e

## Attempt 1

Hypothesis: each changed row contains one or more horizontal `C 0 C` motifs for a
nonzero color `C`. The transformation fills only the single zero between equal
neighbors. Repeated motifs such as `C 0 C 0 C` therefore become a solid run.

Evidence from the visible pairs:
- Rows with spacing exactly two are filled for colors 2, 4, 5, 7, 8, and 9.
- A same-color pair with two zeros between it is left unchanged.
- `C D C` with nonzero middle color `D` is left unchanged.
- No vertical changes are demonstrated.

Implementation scans each input row without feeding newly filled cells back into
the decision, and replaces a zero iff its immediate horizontal neighbors are the
same nonzero color. This directly covers both isolated and chained motifs.
